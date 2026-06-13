import logging
import re
import inflect
from .specs.specs import DocSpecs
from .chunk import Chunk
from dataclasses import replace

logger = logging.getLogger(__name__)
p = inflect.engine()


def extract_to_definitions(specs: DocSpecs, lines: list[str]) -> dict[str, str]:
    if (
        specs.is_definition_line is None
        or specs.is_double_def_line is None
        or specs.is_false_dub_def is None
    ):
        logger.info("no definition section")
        return {}

    logger.info("loading definitions from [%s]", specs.document)
    definitions = {}
    pending_terms = []
    pending_value = ""

    def flush():
        nonlocal pending_value
        if pending_value and pending_terms:
            for term in pending_terms:
                definitions[term] = pending_value
        pending_terms.clear()
        pending_value = ""

    for line in lines:
        if not line.strip():
            continue
        elif specs.is_definition_line(line):
            flush()
            def_line = [specs.h_strip_md(segment) for segment in line.split('"')]
            if len(def_line) == 3:
                pending_terms.append(def_line[1])
                pending_value = def_line[2]
            elif len(def_line) == 5:
                if specs.is_double_def_line(def_line):
                    pending_terms.append(def_line[1])
                    pending_terms.append(def_line[3])
                    pending_value = def_line[4]
                elif specs.is_false_dub_def(def_line):
                    pending_terms.append(def_line[1])
                    pending_value = f'{def_line[2]} "{def_line[3]}" {def_line[4]}'
                else:
                    logger.warning(
                        "looks like two quoted terms but unable to parse: [%s]",
                        line.strip(),
                    )
            else:
                pending_terms.append(def_line[1])
                pending_value = " ".join(def_line[2:])
                logger.warning(
                    "unexpected def_line shape, [%d] segments found, took [%s] as term and buffer set to [%s]",
                    len(def_line),
                    def_line[1],
                    pending_value,
                )
        else:
            pending_value += "\n" + specs.strip_md(line)
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


def attach_definitions(chunks: list[Chunk], definitions: dict) -> list[Chunk]:
    logger.info("Attaching definitions to chunks")

    chunks_with_terms = []
    for chunk in chunks:
        terms_used = []
        for term in definitions:
            # TODO: calling term_in_body is inefficient and should be pre computed
            if term_in_body(term, chunk.body):
                terms_used.append(term)
        chunks_with_terms.append(replace(chunk, terms_used=terms_used))
    logger.info("Definitions attached")
    return chunks_with_terms
