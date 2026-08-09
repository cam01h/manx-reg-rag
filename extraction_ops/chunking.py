import logging
import hashlib
from dataclasses import replace
from typing import Callable
from extraction_ops.models import Chunk, CleanSection, Section, ToolBelt
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
            body_lines.append(line.strip())
        else:
            flush()
            headers = update_header_stack(headers, level, line)
    flush()

    return sections


def clean_section(tools: ToolBelt, section: Section) -> CleanSection:
    return CleanSection(
        headers=tuple(tools.clean_header(h) for h in section.headers),
        body=tools.clean_body("\n".join(section.body_lines)),
    )


def _log_oversized(length: int, headers: tuple[str, ...], final_pass: bool) -> None:
    message = "unsplittable section oversized at [%d] chars: %s"
    if final_pass:
        logger.warning(message, length, headers)
    else:
        logger.debug(message, length, headers)


def split_one_section(
    section: CleanSection, splitter: Callable[[str], list[str]], final_pass: bool
) -> list[CleanSection]:
    if len(section.body) <= MAX_CHUNK_CHAR:
        return [section]

    segments = splitter(section.body)
    if len(segments) == 1:
        _log_oversized(len(section.body), section.headers, final_pass)
        return [section]

    split_sections: list[CleanSection] = []
    buffer = ""

    def flush(body: str) -> None:
        split_sections.append(replace(section, body=body.strip()))

    for segment in segments:
        if len(segment) > MAX_CHUNK_CHAR:
            _log_oversized(len(segment), section.headers, final_pass)
        if buffer != "" and len(buffer) + len(segment) > MAX_CHUNK_CHAR:
            flush(buffer)
            buffer = segment
        else:
            buffer += "\n" + segment
    if buffer != "":
        flush(buffer)
    return split_sections


def merge_undersized_sections(sections: list[CleanSection]) -> list[CleanSection]:
    def should_merge(section: CleanSection, previous: CleanSection) -> bool:
        is_too_short = len(section.body) < MIN_CHUNK_CHAR
        same_header_bracket = previous.headers == section.headers
        combined_not_too_big = (
            len(previous.body) + len(section.body) < TARGET_CHUNK_CHAR
        )
        return is_too_short and same_header_bracket and combined_not_too_big

    merged: list[CleanSection] = []
    previous: CleanSection | None = None
    for section in sections:
        if previous is None:
            previous = section
            continue
        if should_merge(section, previous):
            # TODO: undersized sections following a large section never merge
            previous = replace(previous, body=f"{previous.body}\n\n{section.body}")
        else:
            merged.append(previous)
            previous = section
    if previous is not None:
        merged.append(previous)

    if len(sections) != len(merged):
        logger.info(
            "[%d] sections merged into [%d] ([%d] merges)",
            len(sections),
            len(merged),
            len(sections) - len(merged),
        )
    else:
        logger.info("no sections were merged")
    return merged


def filter_sections(sections: list[CleanSection], min_len: int) -> list[CleanSection]:
    kept: list[CleanSection] = []
    for section in sections:
        if len(section.body) >= min_len:
            kept.append(section)
        else:
            logger.debug("filtered section: %s", section)
    logger.info("[%d] sections removed by length", len(sections) - len(kept))
    return kept


def get_body_hash(body: str) -> str:
    return hashlib.sha1(body.encode()).hexdigest()[:16]


def pack_chunk(tools: ToolBelt, section: CleanSection) -> Chunk:
    headers = list(section.headers)
    return Chunk(
        chunk_id=f"{tools.document}, {', '.join(headers)} - {get_body_hash(section.body)}",
        document=tools.document,
        hierarchy=tools.hierarchy,
        headers=headers,
        body=section.body,
    )


def normalise_sections(tools: ToolBelt, sections: list[Section]) -> list[CleanSection]:
    splitters = tools.re_pack_splitters
    normalised: list[CleanSection] = []

    for section in sections:
        raw_body = "\n".join(section.body_lines)
        # early filter: drops non-paragraph noise before it can block adjacency
        if len(raw_body) < tools.min_body_len:
            logger.debug("section dropped pre-clean: %s", section.headers)
            continue
        clean = clean_section(tools, section)
        pieces = split_one_section(clean, splitters.primary, final_pass=False)
        pieces = [
            final
            for piece in pieces
            for final in split_one_section(piece, splitters.fallback, final_pass=True)
        ]
        normalised.extend(pieces)

    normalised = merge_undersized_sections(normalised)
    normalised = filter_sections(normalised, tools.min_body_len)
    return normalised


def extract_to_chunks(tools: ToolBelt, lines: list[str]) -> list[Chunk]:
    logger.info("chunking [%s]", tools.document)
    sections = segment_by_headers(lines, tools.header_matchers)
    logger.info("initial section count: [%d]", len(sections))
    sections = normalise_sections(tools, sections)
    chunks = [pack_chunk(tools, section) for section in sections]
    logger.info("final chunk count: [%d]", len(chunks))
    return chunks
