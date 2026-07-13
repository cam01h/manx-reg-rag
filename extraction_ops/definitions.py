import logging
import re
import inflect
from extraction_ops.models import Definition, ToolBelt, Chunk
from dataclasses import replace

logger = logging.getLogger(__name__)
p = inflect.engine()


def extract_to_definitions(toolbelt: ToolBelt, lines: list[str]) -> list[Definition]:
    if toolbelt.definition_tools is None:
        return []

    logger.info("loading definitions from [%s]", toolbelt.document)
    tools = toolbelt.definition_tools
    definitions = []
    pending_terms = []
    pending_text = ""

    def flush():
        nonlocal pending_text
        if pending_text and pending_terms:
            for term in pending_terms:
                defined_term = Definition(
                    document=toolbelt.document,
                    scope=tools.definition_scope,
                    term=term,
                    definition=pending_text,
                )
                definitions.append(defined_term)
        pending_terms.clear()
        pending_text = ""

    for line in lines:
        if not line.strip():
            continue
        elif tools.is_definition_line(line):
            flush()
            def_line = [toolbelt.clean_header(segment) for segment in line.split('"')]
            if len(def_line) == 3:
                pending_terms.append(def_line[1])
                pending_text = def_line[2]
            elif len(def_line) == 5:
                if tools.is_double_def_line(def_line):
                    pending_terms.append(def_line[1])
                    pending_terms.append(def_line[3])
                    pending_text = def_line[4]
                elif tools.is_false_dub_def(def_line):
                    pending_terms.append(def_line[1])
                    pending_text = f'{def_line[2]} "{def_line[3]}" {def_line[4]}'
                else:
                    logger.warning(
                        "looks like two quoted terms but unable to parse: [%s]",
                        line.strip(),
                    )
            else:
                pending_terms.append(def_line[1])
                pending_text = " ".join(def_line[2:])
                logger.warning(
                    "unexpected def_line shape, [%d] segments found, took [%s] as term and buffer set to [%s]",
                    len(def_line),
                    def_line[1],
                    pending_text,
                )
        else:
            pending_text += "\n" + toolbelt.clean_body(line)
    flush()
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
