from dataclasses import asdict
import pymupdf4llm
import json
from typing import cast
from .specs.aml_handbook import AmlHandbook
from .specs.aml_code import AmlCode
from .specs.specs import DocSpecs
from .chunking import extract_to_chunks, normalise_chunk_size
from .definitions import extract_to_definitions, attach_definitions
from config import (
    CHUNKS_JSONL_PATH,
    DEFINITIONS_JSONL_PATH,
    setup_logging,
)
import logging

logger = logging.getLogger(__name__)


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
        chunks = extract_to_chunks(doc, md)
        chunks = normalise_chunk_size(chunks, doc)
        logger.info("%d normalised chunks", len(chunks))
        if doc.has_definition_section:
            definitions = extract_to_definitions(doc, md)
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
