import logging
from dataclasses import replace
from typing import Callable
from .specs.specs import DocSpecs
from .chunk import Chunk
from config import MAX_CHUNK_CHAR, MIN_CHUNK_CHAR, TARGET_CHUNK_CHAR, DELETE_LEN

logger = logging.getLogger(__name__)


def extract_to_chunks(specs: DocSpecs, lines: list[str]) -> list[Chunk]:
    logger.info("chunking %s", specs.document)
    if specs.has_definition_section:
        lines = lines[: specs.definitions_start] + lines[specs.definitions_end :]
        logger.info("definition section removed")

    buffer = ""
    chunks = []
    major = ""
    minor = ""

    def pack_chunk(major: str, minor: str, body: str) -> Chunk:
        current_chunk = Chunk(
            document=specs.document,
            hierarchy=specs.hierarchy,
            major=major,
            minor=minor,
            body=body.strip(),
        )
        return current_chunk

    def flush():
        nonlocal buffer
        if buffer.strip():
            chunks.append(pack_chunk(major, minor, buffer))
            buffer = ""

    for line in lines:
        if specs.is_major_header_line(line):
            flush()
            major = specs.strip_md(line)
        elif specs.is_minor_header_line(line):
            flush()
            minor = specs.strip_md(line)
        else:
            buffer += "\n" + line
    flush()
    logger.info("initial chunk count: %d", len(chunks))
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
            logger.warning("unsplitable chunk oversized at %d chars", len(s))
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
        not_at_boundary = (
            chunk.major == previous_chunk.major and chunk.minor == previous_chunk.minor
        )
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
                body=f"{previous_chunk.body}\n\n{chunk.minor} - {chunk.body}",
            )
        else:
            checked_chunks.append(previous_chunk)
            previous_chunk = chunk
    if previous_chunk:
        checked_chunks.append(previous_chunk)
    if len(chunks) != len(checked_chunks):
        reduction = len(chunks) - len(checked_chunks)
        logger.info(
            "%d were merged into %d (%d merges)",
            len(chunks),
            len(checked_chunks),
            reduction,
        )
    else:
        logger.info("No chunks were merged")
    return checked_chunks


def filter_chunks(chunks: list[Chunk]) -> list[Chunk]:
    filtered_chunks = []
    deleted_chunks = 0
    for c in chunks:
        if len(c.body) >= DELETE_LEN:
            filtered_chunks.append(c)
        else:
            deleted_chunks += 1
    logger.info("%d chunks removed by length", deleted_chunks)
    return filtered_chunks


def normalise_chunk_size(chunks: list[Chunk], specs: DocSpecs) -> list[Chunk]:
    chunks = re_pack_oversized_chunks(chunks, specs.re_pack_splitter)
    chunks = re_pack_undersized_chunks(chunks)
    chunks = filter_chunks(chunks)
    return chunks
