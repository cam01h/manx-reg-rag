from dataclasses import asdict
import json
from pathlib import Path
from extraction_ops.toolbelts.aml_code import AmlCode
from extraction_ops.toolbelts.aml_handbook.aml_handbook import AmlHandbook
from .load_to_md import load_clean_md
from .models import Chunk, Definition, ToolBelt
from .chunking import extract_to_chunks, normalise_chunk_size
from .definitions import extract_to_definitions, attach_definitions
from config import (
    CHUNKS_JSONL_PATH,
    DEFINITIONS_JSONL_PATH,
    setup_logging,
)
import logging

logger = logging.getLogger(__name__)


def process_document(tools: ToolBelt) -> tuple[list[Chunk], list[Definition]]:
    md = load_clean_md(tools)
    chunks = extract_to_chunks(tools, md.chunk_lines)
    chunks = normalise_chunk_size(chunks, tools)
    logger.info(
        "[%d] normalised chunks", len(chunks)
    )  # TODO: should be in normalise chunks func
    definitions = extract_to_definitions(tools, md.definition_lines)
    chunks = attach_definitions(chunks, definitions)
    return chunks, definitions


def process_documents(docs: list[ToolBelt]) -> tuple[list[Chunk], list[Definition]]:
    all_chunks: list[Chunk] = []
    all_definitions: list[Definition] = []
    for doc in docs:
        chunks, definitions = process_document(doc)
        all_chunks.extend(chunks)
        all_definitions.extend(definitions)
    return all_chunks, all_definitions


def write_chunks(chunks: list[Chunk], path: Path) -> None:
    try:
        with path.open("w") as f:
            for c in chunks:
                f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
        logger.info("[%d] chunks written to [%s]", len(chunks), path)
    except Exception:
        logger.exception("failed to write chunks to [%s]", path)
        raise


def write_definitions(definitions: list[Definition], path: Path) -> None:
    try:
        with path.open("w") as f:
            for d in definitions:
                f.write(json.dumps(asdict(d), ensure_ascii=False) + "\n")
        logger.info("[%d] definitions written to [%s]", len(definitions), path)
    except Exception:
        logger.exception("failed to write definitions to [%s]", path)
        raise


def main() -> None:
    setup_logging("ingest")
    docs = [
        AmlCode,
        AmlHandbook,
    ]
    all_chunks, all_definitions = process_documents(docs)
    write_chunks(all_chunks, CHUNKS_JSONL_PATH)
    write_definitions(all_definitions, DEFINITIONS_JSONL_PATH)


if __name__ == "__main__":
    main()
