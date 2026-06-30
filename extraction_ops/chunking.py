import logging
from dataclasses import replace
from typing import Callable
from .specs.specs import DocSpecs
from .chunk import Chunk
from config import MAX_CHUNK_CHAR, MIN_CHUNK_CHAR, TARGET_CHUNK_CHAR, DELETE_LEN

logger = logging.getLogger(__name__)


def extract_to_chunks(specs: DocSpecs, lines: list[str]) -> list[Chunk]:
    logger.info("chunking [%s]", specs.document)
    if specs.has_definition_section:
        lines = lines[: specs.definitions_start] + lines[specs.definitions_end :]
        logger.info("definition section removed")

    buffer = ""
    chunks = []
    headers = [""] * len(specs.header_matchers)

    def pack_chunk(headers: list[str], body: str) -> Chunk:
        current_chunk = Chunk(
            document=specs.document,
            hierarchy=specs.hierarchy,
            headers=[h for h in headers],
            body=specs.strip_md(body.strip()),
        )
        return current_chunk

    def flush():
        nonlocal buffer
        if buffer.strip():
            chunks.append(pack_chunk(headers, buffer))
            buffer = ""

    def match_level(line: str, matchers: list[Callable[[str], bool]]) -> int | None:
        for level, is_header in enumerate(matchers):
            if is_header(line):
                return level
        return None

    for line in lines:
        level = match_level(line, specs.header_matchers)
        if level is None:
            buffer += "\n" + line.strip()
        else:
            flush()
            headers[level] = specs.strip_md(line)
            for i in range(level + 1, len(headers)):
                headers[i] = ""
    flush()
    logger.info("initial chunk count: [%d]", len(chunks))
    return chunks


def _split_one_chunk(chunk: Chunk, splitter: Callable) -> list[Chunk]:
    if len(chunk.body) < MAX_CHUNK_CHAR:
        return [chunk]
    # TODO: Unsplittable chunks slip through oversized, maybe add a fallback splitter
    segments = splitter(chunk.body)
    if len(segments) == 1:
        return [chunk]

    split_chunks = []
    buffer = ""

    def flush(body: str):
        split_chunks.append(replace(chunk, body=body.strip()))

    for s in segments:
        if len(s) > MAX_CHUNK_CHAR:
            logger.warning(
                "unsplitable chunk oversized at [%d] chars: %s", len(s), chunk.headers
            )
        if buffer != "" and len(buffer + s) > MAX_CHUNK_CHAR:
            flush(buffer)
            buffer = s
        else:
            buffer += "\n" + s
    if buffer != "":
        flush(buffer)
    return split_chunks


def re_pack_oversized_chunks(chunks: list[Chunk], splitter: Callable):
    return [out for c in chunks for out in _split_one_chunk(c, splitter)]


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


def filter_chunks(chunks: list[Chunk]) -> list[Chunk]:
    filtered_chunks = []
    deleted_chunks = []
    for c in chunks:
        if len(c.body) >= DELETE_LEN:
            filtered_chunks.append(c)
        else:
            deleted_chunks.append(c)
    for chunk in deleted_chunks:
        logger.debug("filtered chunk: %s", chunk)
    logger.info("[%d] chunks removed by length", len(deleted_chunks))
    return filtered_chunks


def normalise_chunk_size(chunks: list[Chunk], specs: DocSpecs) -> list[Chunk]:
    chunks = re_pack_oversized_chunks(chunks, specs.re_pack_splitter)
    chunks = re_pack_undersized_chunks(chunks)
    chunks = filter_chunks(chunks)
    return chunks
