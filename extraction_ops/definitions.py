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

    logger.info("loading definitions from %s", specs.document)
    definitions = {}
    keys = []
    v = ""

    for line in lines:
        if not line.strip():
            continue
        if specs.is_definition_line(line):
            if v != "" and keys != []:
                for k in keys:
                    definitions[k] = v
            keys = []
            v = ""
            def_line = line.split('"')
            for i, w in enumerate(def_line):
                def_line[i] = specs.h_strip_md(w)
            if len(def_line) == 3:
                keys.append(def_line[1])
                v = def_line[2]
            if len(def_line) == 5:
                if specs.is_double_def_line(def_line):
                    keys.append(def_line[1])
                    keys.append(def_line[3])
                    v = def_line[4]
                elif specs.is_false_dub_def(def_line):
                    keys.append(def_line[1])
                    v = f'{def_line[2]} "{def_line[3]}" {def_line[4]}'
        else:
            v += "\n" + specs.strip_md(line)
    if v != "" and keys != []:
        for k in keys:
            definitions[k] = v
    logger.info("%d definitions formatted.", len(definitions))
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
            if term_in_body(term, chunk.body):
                terms_used.append(term)
        chunks_with_terms.append(replace(chunk, terms_used=terms_used))
    logger.info("Definitions attached")
    return chunks_with_terms
