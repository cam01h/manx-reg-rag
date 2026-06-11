from dataclasses import asdict, replace
import pymupdf4llm
import json
from typing import Callable, cast
from .chunk import Chunk
from .specs.aml_handbook import AmlHandbook
from .specs.aml_code import AmlCode
from .specs.specs import DocSpecs
import inflect
import re
from config import (
    CHUNKS_JSONL_PATH,
    DEFINITIONS_JSONL_PATH,
    DELETE_LEN,
    MAX_CHUNK_CHAR,
    MIN_CHUNK_CHAR,
    TARGET_CHUNK_CHAR,
    setup_logging,
)
import logging

logger = logging.getLogger(__name__)
p = inflect.engine()


def load_clean_md(specs: DocSpecs) -> list[str]:
    logger.info("Loading %s to md", specs.document)
    try:
        md = cast(
            str, pymupdf4llm.to_markdown(specs.input_path, header=False, footer=False)
        )
    except Exception:
        logger.exception("failed pymupdf4llm conversion")
        raise
    md_lines = md.splitlines()
    trimmed_lines = md_lines[specs.start_line : specs.end_line]
    md = "\n".join(trimmed_lines)
    md = specs.re_steps(md)
    md = md.replace("“", '"').replace("”", '"')
    trimmed_lines = md.splitlines()
    logger.info("Extraction to md complete.")
    return trimmed_lines


def extract_doc(specs: DocSpecs, lines: list[str]) -> list[Chunk]:
    logger.info("chunking %s", specs.document)
    if specs.has_definition_section:
        lines = lines[: specs.definitions_start] + lines[specs.definitions_end :]
        logger.info("definition section removed")

    def pack_chunk(major: str, minor: str, body: str) -> Chunk:
        current_chunk = Chunk(
            document=specs.document,
            hierarchy=specs.hierarchy,
            major=major,
            minor=minor,
            body=body.strip(),
        )
        return current_chunk

    buffer = ""
    chunks = []
    major = ""
    minor = ""

    for line in lines:
        if specs.is_major_header_line(line):
            if buffer.strip() != "":
                chunks.append(pack_chunk(major, minor, buffer))
                buffer = ""
            major = specs.strip_md(line)
        elif specs.is_minor_header_line(line):
            if buffer.strip() != "":
                chunks.append(pack_chunk(major, minor, buffer))
                buffer = ""
            minor = specs.strip_md(line)
        else:
            buffer += "\n" + line
    chunks.append(pack_chunk(major, minor, buffer))
    logger.info("initial chunk count: %d", len(chunks))
    return chunks


def extract_definitions(specs: DocSpecs, lines: list[str]) -> dict[str, str]:
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


def re_pack_oversized_chunk(chunk: Chunk, splitter: Callable) -> list[Chunk]:
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
    chunks = [
        out
        for c in chunks
        for out in re_pack_oversized_chunk(c, specs.re_pack_splitter)
    ]
    chunks = re_pack_undersized_chunks(chunks)
    chunks = filter_chunks(chunks)
    return chunks


if __name__ == "__main__":
    setup_logging("ingest")
    docs = [
        AmlCode,
        AmlHandbook,
    ]
    all_chunks = []
    all_definitions = {}
    for doc in docs:
        md = load_clean_md(doc)
        chunks = extract_doc(doc, md)
        chunks = normalise_chunk_size(chunks, doc)
        logger.info("%d normalised chunks", len(chunks))
        if doc.has_definition_section:
            definitions = extract_definitions(doc, md)
            chunks = attach_definitions(chunks, definitions)
            all_definitions[doc.document] = definitions
        all_chunks.extend(chunks)
    try:
        with CHUNKS_JSONL_PATH.open("w") as f:
            for c in all_chunks:
                f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
        logger.info("%d chunks written to %s", len(all_chunks), CHUNKS_JSONL_PATH)
    except Exception:
        logger.exception("failed to write chunks to %s", CHUNKS_JSONL_PATH)
        raise
    try:
        with DEFINITIONS_JSONL_PATH.open("w") as f:
            json.dump(all_definitions, f, ensure_ascii=False, indent=2)
        total_definitions = sum(len(defs) for defs in all_definitions.values())
        logger.info(
            "%d definitions written to %s", total_definitions, DEFINITIONS_JSONL_PATH
        )
    except Exception:
        logger.exception("failed to write definitions to %s", DEFINITIONS_JSONL_PATH)
        raise
