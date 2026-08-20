import argparse
from dataclasses import asdict
import json
from pathlib import Path
from extraction_ops import ALL_TOOLBELTS
from extraction_ops.md_ops import pdf_to_output
from extraction_ops.pdf_ops import apply_pdf_handlers, get_pdf_from_url
from .models import Chunk, Definition, ToolBelt
from .chunking import extract_to_chunks
from .definitions import extract_to_definitions, attach_definitions
from config import (
    CHUNKS_JSONL_PATH,
    DEFINITIONS_JSONL_PATH,
    setup_logging,
)
import logging

logger = logging.getLogger(__name__)


def _write_chunks(chunks: list[Chunk], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w") as f:
            for c in chunks:
                f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
        logger.info("[%d] chunks written to [%s]", len(chunks), path)
    except Exception:
        logger.exception("failed to write chunks to [%s]", path)
        raise


def _write_definitions(definitions: list[Definition], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w") as f:
            for d in definitions:
                f.write(json.dumps(asdict(d), ensure_ascii=False) + "\n")
        logger.info("[%d] definitions written to [%s]", len(definitions), path)
    except Exception:
        logger.exception("failed to write definitions to [%s]", path)
        raise


def write_chunks_and_definitions(toolbelts: list[ToolBelt]) -> None:
    chunks_with_definitions: list[Chunk] = []
    definitions: list[Definition] = []
    for tools in toolbelts:
        output = pdf_to_output(tools)
        doc_definitions = extract_to_definitions(tools, output.definition_lines)
        definitions.extend(doc_definitions)
        doc_chunks = extract_to_chunks(tools, output.chunk_lines)
        chunks_with_definitions.extend(attach_definitions(doc_chunks, doc_definitions))
    _write_chunks(chunks_with_definitions, CHUNKS_JSONL_PATH)
    _write_definitions(definitions, DEFINITIONS_JSONL_PATH)


def check_pdf_paths(toolbelts: list[ToolBelt]) -> None:
    for tools in ALL_TOOLBELTS:
        if not tools.pdf_path.exists():
            logger.error(
                "no pdf for [%s] found at pdf path: [%s]",
                tools.document,
                tools.pdf_path,
            )
            raise FileNotFoundError(
                f"no pdf for {tools.document} found at pdf path: {tools.pdf_path}"
            )
    logger.info("all [%d] pdf files located", len(toolbelts))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest documents from url to formatted chunks and definitions"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--get-pdfs",
        action="store_true",
        help="retrieve PDFs from the toolbelt url",
    )
    group.add_argument(
        "--handle-pdfs",
        action="store_true",
        help="appply pdf handlers attached in toolbelt",
    )
    group.add_argument(
        "--ingest",
        action="store_true",
        help="process each pdf into chunks and defintions that are then written to jsonl files",
    )
    args = parser.parse_args()
    if args.get_pdfs:
        for tools in ALL_TOOLBELTS:
            get_pdf_from_url(tools.document, tools.input_url, tools.pdf_path)
    elif args.handle_pdfs:
        check_pdf_paths(ALL_TOOLBELTS)
        for tools in ALL_TOOLBELTS:
            apply_pdf_handlers(tools)
    elif args.ingest:
        check_pdf_paths(ALL_TOOLBELTS)
        write_chunks_and_definitions(ALL_TOOLBELTS)
    else:
        for tools in ALL_TOOLBELTS:
            get_pdf_from_url(tools.document, tools.input_url, tools.pdf_path)
            apply_pdf_handlers(tools)
        write_chunks_and_definitions(ALL_TOOLBELTS)


if __name__ == "__main__":
    setup_logging("extraction ops")
    main()
