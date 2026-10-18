import argparse
import json
import logging
from dataclasses import asdict
from pathlib import Path

from config import CHUNKS_DIR, DEFINITIONS_DIR, setup_logging
from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.md_ops import pdf_to_output
from extraction_ops.pdf_ops import apply_pdf_handlers, get_pdf_from_url

from .chunking import extract_to_chunks
from .definitions import attach_definitions, extract_to_definitions
from .models import Chunk, Definition, ToolBelt

logger = logging.getLogger(__name__)


def _write_jsonl(records: list[Chunk] | list[Definition], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w") as f:
            for r in records:
                f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
        logger.info("[%d] records written to [%s]", len(records), path)
    except Exception:
        logger.exception("failed to write records to [%s]", path)
        raise


def select_toolbelts(doc: str | None) -> dict[str, ToolBelt]:
    if doc is None:
        return TOOLBELT_REGISTRY
    return {doc: TOOLBELT_REGISTRY[doc]}


def check_pdf_paths(toolbelts: dict[str, ToolBelt]) -> None:
    for tools in toolbelts.values():
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


def get_pdfs(toolbelts: dict[str, ToolBelt]) -> None:
    for tools in toolbelts.values():
        get_pdf_from_url(tools.document, tools.input_url, tools.pdf_path)


def handle_pdfs(toolbelts: dict[str, ToolBelt]) -> None:
    check_pdf_paths(toolbelts)
    for tools in toolbelts.values():
        apply_pdf_handlers(tools)


def ingest_document(key: str, tools: ToolBelt) -> None:
    output = pdf_to_output(tools)
    definitions = extract_to_definitions(tools, output.definition_lines)
    chunks = extract_to_chunks(tools, output.chunk_lines)
    _write_jsonl(attach_definitions(chunks, definitions), CHUNKS_DIR / f"{key}.jsonl")
    _write_jsonl(definitions, DEFINITIONS_DIR / f"{key}.jsonl")


def ingest(toolbelts: dict[str, ToolBelt]) -> None:
    check_pdf_paths(toolbelts)
    for key, tools in toolbelts.items():
        ingest_document(key, tools)


def build_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest documents from url to formatted chunks and definitions"
    )
    parser.add_argument(
        "--doc",
        choices=TOOLBELT_REGISTRY.keys(),
        help="process a single document (default: all documents)",
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
        help="apply pdf handlers attached in toolbelt",
    )
    group.add_argument(
        "--ingest",
        action="store_true",
        help="process each pdf into chunks and definitions, written to per-document jsonl files",
    )
    return parser.parse_args()


def main() -> None:
    args = build_cli()
    toolbelts = select_toolbelts(args.doc)
    if args.get_pdfs:
        get_pdfs(toolbelts)
    elif args.handle_pdfs:
        handle_pdfs(toolbelts)
    elif args.ingest:
        ingest(toolbelts)
    else:
        get_pdfs(toolbelts)
        handle_pdfs(toolbelts)
        ingest(toolbelts)


if __name__ == "__main__":
    setup_logging("extraction ops")
    main()
