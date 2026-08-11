import logging
import re
from typing import Callable
import inflect
from extraction_ops.load_to_md import normalise_serial_new_lines
from extraction_ops.models import Definition, DefinitionTools, ToolBelt, Chunk
from dataclasses import replace

logger = logging.getLogger(__name__)
p = inflect.engine()


def segment_by_definitions(
    lines: list[str], is_definition_line: Callable[[str], bool]
) -> list[list[str]]:
    """Group lines into one list per definition.

    Each group's first line is the definition line and the rest are its body.
    A leading group whose first line is not a definition line is orphan text
    that preceded the first definition.
    """
    sections: list[list[str]] = []
    buffer: list[str] = []

    for line in lines:
        if is_definition_line(line):
            if buffer:
                sections.append(buffer)
            buffer = [line]
        else:
            buffer.append(line)
    if buffer:
        sections.append(buffer)

    return sections


def split_definition_line(line: str, clean_header: Callable[[str], str]) -> list[str]:
    return [clean_header(segment) for segment in line.split('"')]


def parse_definition_line(
    segments: list[str], def_tools: DefinitionTools
) -> tuple[list[str], str] | None:
    """Return (terms, opening body text) for a definition line, or None if unparseable."""
    if len(segments) == 3:
        return [segments[1]], segments[2]

    if len(segments) == 5:
        if def_tools.is_double_def_line(segments):
            # "term one" or "term two" means ...
            return [segments[1], segments[3]], segments[4]
        if def_tools.is_false_dub_def(segments):
            # "term" means ... "quoted phrase" ... -- second quote is not a term
            return [segments[1]], f'{segments[2]} "{segments[3]}" {segments[4]}'
        return None

    if len(segments) > 3:
        return [segments[1]], " ".join(segments[2:])

    return None


def pack_definitions(section: list[str], toolbelt: ToolBelt) -> list[Definition]:
    """Turn one section into a Definition per term. Section[0] is always the definition line."""
    def_tools = toolbelt.definition_tools
    if def_tools is None:
        return []

    def_line = section[0]
    if not def_tools.is_definition_line(def_line):
        logger.warning("orphan text before first definition dropped: [%s]", def_line)
        return []

    segments = split_definition_line(def_line, toolbelt.clean_header)
    parsed = parse_definition_line(segments, def_tools)
    if parsed is None:
        logger.warning(
            "definition line claimed but not parseable, [%d] segments: [%s]",
            len(segments),
            def_line.strip(),
        )
        return []

    terms, opening_text = parsed
    if len(segments) not in (3, 5):
        logger.warning(
            "unexpected definition line shape, [%d] segments, took [%s] as term: [%s]",
            len(segments),
            terms[0],
            def_line.strip(),
        )

    body_lines = [opening_text] + [toolbelt.clean_body(line) for line in section[1:]]
    body = "\n".join(body_lines).strip()
    if not body:
        logger.warning("term with no definition body dropped: %s", terms)
        return []

    return [
        Definition(document=toolbelt.document, term=term, definition=body)
        for term in terms
    ]


def extract_to_definitions(toolbelt: ToolBelt, lines: list[str]) -> list[Definition]:
    if toolbelt.definition_tools is None:
        return []
    logger.info("loading definitions from [%s]", toolbelt.document)
    normalised = normalise_serial_new_lines(lines)
    sections = segment_by_definitions(
        normalised, toolbelt.definition_tools.is_definition_line
    )
    definitions = [
        definition
        for section in sections
        for definition in pack_definitions(section, toolbelt)
    ]
    logger.info("[%d] definitions formatted.", len(definitions))
    return definitions


def term_in_body(term: str, body: str) -> bool:
    term_variants = list({term, p.plural(term)})  # type: ignore[arg-type]
    patterns = [rf"\b{re.escape(v)}\b" for v in term_variants]
    for pattern in patterns:
        if re.search(pattern, body, re.IGNORECASE):
            return True
    return False


def attach_definitions(
    chunks: list[Chunk], definitions: list[Definition]
) -> list[Chunk]:
    logger.info("Attaching definitions to chunks")

    chunks_with_terms = []
    for chunk in chunks:
        terms_used = []
        for definition in definitions:
            # TODO: calling term_in_body is inefficient and should be pre computed
            if term_in_body(definition.term, chunk.body):
                terms_used.append(definition.term)
        chunks_with_terms.append(replace(chunk, terms_used=terms_used))
    logger.info("Definitions attached")
    return chunks_with_terms
