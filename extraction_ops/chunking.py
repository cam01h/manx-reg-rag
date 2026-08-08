import logging
import hashlib
from dataclasses import replace
from typing import Callable
from extraction_ops.models import Chunk, Section, ToolBelt
from config import MAX_CHUNK_CHAR, MIN_CHUNK_CHAR, TARGET_CHUNK_CHAR

logger = logging.getLogger(__name__)


def match_level(line: str, matchers: list[Callable[[str], bool]]) -> int | None:
    for level, is_header in enumerate(matchers):
        if is_header(line):
            return level
    return None


def update_header_stack(
    headers: tuple[str, ...], level: int, line: str
) -> tuple[str, ...]:
    updated = list(headers)
    updated[level] = line
    for i in range(level + 1, len(updated)):
        updated[i] = ""
    return tuple(updated)


def segment_by_headers(
    lines: list[str], matchers: list[Callable[[str], bool]]
) -> list[Section]:
    sections: list[Section] = []
    headers: tuple[str, ...] = ("",) * len(matchers)
    body_lines: list[str] = []

    def flush() -> None:
        nonlocal body_lines
        if any(line.strip() for line in body_lines):
            sections.append(Section(headers=headers, body_lines=body_lines))
        body_lines = []

    for line in lines:
        level = match_level(line, matchers)
        if level is None:
            # blank lines are kept deliberately: they carry the paragraph
            body_lines.append(line.strip())
        else:
            flush()
            headers = update_header_stack(headers, level, line)
    flush()

    return sections


def pack_chunk(tools: ToolBelt, section: Section) -> Chunk:
    return Chunk(
        chunk_id="",  # assigned in normalise_chunk_size
        document=tools.document,
        hierarchy=tools.hierarchy,
        headers=[tools.clean_header(h) for h in section.headers],
        body=tools.clean_body("\n".join(section.body_lines)),
    )


def extract_to_chunks(tools: ToolBelt, lines: list[str]) -> list[Chunk]:
    logger.info("chunking [%s]", tools.document)
    sections = segment_by_headers(lines, tools.header_matchers)
    chunks = [pack_chunk(tools, section) for section in sections]
    logger.info("initial chunk count: [%d]", len(chunks))
    return chunks


def _split_one_chunk(
    chunk: Chunk, splitter: Callable[[str], list[str]], final_pass: bool
) -> list[Chunk]:
    if len(chunk.body) < MAX_CHUNK_CHAR:
        return [chunk]
    # TODO: use fallback splitter to preserve the intro to a list
    segments = splitter(chunk.body)
    if len(segments) == 1:
        if len(chunk.body) > MAX_CHUNK_CHAR:
            if final_pass:
                logger.warning(
                    "unsplitable chunk in final pass oversized at [%d] chars: %s",
                    len(chunk.body),
                    chunk.headers,
                )
            else:
                logger.debug(
                    "unsplitable chunk oversized at [%d] chars: %s",
                    len(chunk.body),
                    chunk.headers,
                )
        return [chunk]

    split_chunks = []
    buffer = ""

    def flush(body: str):
        split_chunks.append(replace(chunk, body=body.strip()))

    for s in segments:
        if len(s) > MAX_CHUNK_CHAR:
            if final_pass:
                logger.warning(
                    "unsplitable chunk in final pass oversized at [%d] chars: %s",
                    len(chunk.body),
                    chunk.headers,
                )
            else:
                logger.debug(
                    "unsplitable chunk oversized at [%d] chars: %s",
                    len(chunk.body),
                    chunk.headers,
                )
        if buffer != "" and len(buffer + s) > MAX_CHUNK_CHAR:
            flush(buffer)
            buffer = s
        else:
            buffer += "\n" + s
    if buffer != "":
        flush(buffer)
    return split_chunks


def re_pack_oversized_chunks(
    chunks: list[Chunk], splitter: Callable[[str], list[str]], final_pass: bool
):
    return [out for c in chunks for out in _split_one_chunk(c, splitter, final_pass)]


def re_pack_undersized_chunks(chunks: list[Chunk]) -> list[Chunk]:

    def should_merge(chunk: Chunk, previous_chunk: Chunk) -> bool:
        is_too_short = len(chunk.body) < MIN_CHUNK_CHAR
        not_at_boundary = previous_chunk.headers == chunk.headers
        previous_chunk_not_too_big = (
            len(previous_chunk.body) + len(chunk.body) < TARGET_CHUNK_CHAR
        )
        return is_too_short and not_at_boundary and previous_chunk_not_too_big

    checked_chunks = []
    previous_chunk = None
    for chunk in chunks:
        if previous_chunk is None:
            previous_chunk = chunk
            continue
        if should_merge(chunk, previous_chunk):
            # TODO: undersized chunks following a large chunk never merge. Accepted for now
            previous_chunk = replace(
                previous_chunk,
                body=f"{previous_chunk.body}\n\n{chunk.headers[-1]} - {chunk.body}",
            )
        else:
            checked_chunks.append(previous_chunk)
            previous_chunk = chunk
    if previous_chunk:
        checked_chunks.append(previous_chunk)
    if len(chunks) != len(checked_chunks):
        reduction = len(chunks) - len(checked_chunks)
        logger.info(
            "[%d] were merged into %d ([%d] merges)",
            len(chunks),
            len(checked_chunks),
            reduction,
        )
    else:
        logger.info("No chunks were merged")
    return checked_chunks


def filter_chunks(chunks: list[Chunk], min_len: int) -> list[Chunk]:
    filtered_chunks = []
    deleted_chunks = []
    for c in chunks:
        if len(c.body) >= min_len:
            filtered_chunks.append(c)
        else:
            deleted_chunks.append(c)
    for chunk in deleted_chunks:
        logger.debug("filtered chunk: %s", chunk)
    logger.info("[%d] chunks removed by length", len(deleted_chunks))
    return filtered_chunks


def get_body_hash(body: str) -> str:
    return hashlib.sha1(body.encode()).hexdigest()[:16]


def assign_chunk_ids(chunks: list[Chunk]) -> list[Chunk]:
    return [
        replace(
            c,
            chunk_id=f"{c.document}, {', '.join(c.headers)} - {get_body_hash(c.body)}",
        )
        for c in chunks
    ]


def normalise_chunk_size(chunks: list[Chunk], tools: ToolBelt) -> list[Chunk]:
    chunks = re_pack_oversized_chunks(chunks, tools.re_pack_splitters.primary, False)
    chunks = re_pack_oversized_chunks(chunks, tools.re_pack_splitters.fallback, True)
    chunks = re_pack_undersized_chunks(chunks)
    chunks = filter_chunks(chunks, tools.min_body_len)
    chunks = assign_chunk_ids(chunks)
    return chunks
