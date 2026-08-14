import argparse
import logging
from config import EXTRACTION_OPS_TEST_DATA, setup_logging
from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.md_ops import process_lines
from extraction_ops.models import CleanOutPut, ToolBelt
from tests.extraction_ops.diagnostics.utils import compare_lines

logger = logging.getLogger(__name__)


def _process_trimmed(doc: str, tools: ToolBelt) -> CleanOutPut:
    input_path = EXTRACTION_OPS_TEST_DATA / f"trimmed_md/{doc}_trimmed_golden.md"
    if not input_path.exists():
        logger.error("no initial start file found at [%s]", input_path)
        raise FileNotFoundError(
            f"no golden trimmed md start point found at [{input_path}]"
        )
    return process_lines(input_path.read_text().split("\n"), tools)


def _write_test_output_md(doc: str, tools: ToolBelt) -> None:
    output = _process_trimmed(doc, tools)
    chunk_path = (
        EXTRACTION_OPS_TEST_DATA / f"processed_md/{doc}_processed_chunks_test.md"
    )
    chunk_path.parent.mkdir(parents=True, exist_ok=True)
    chunk_path.write_text("\n".join(output.chunk_lines))
    if tools.definition_tools:
        definitions_path = (
            EXTRACTION_OPS_TEST_DATA
            / f"processed_md/{doc}_processed_definitions_test.md"
        )
        definitions_path.parent.mkdir(parents=True, exist_ok=True)
        definitions_path.write_text("\n".join(output.definition_lines))


def _write_golden_output_md(doc: str, tools: ToolBelt) -> None:
    output = _process_trimmed(doc, tools)
    chunk_path = (
        EXTRACTION_OPS_TEST_DATA / f"processed_md/{doc}_processed_chunks_golden.md"
    )
    chunk_path.parent.mkdir(parents=True, exist_ok=True)
    chunk_path.write_text("\n".join(output.chunk_lines))
    if tools.definition_tools:
        definitions_path = (
            EXTRACTION_OPS_TEST_DATA
            / f"processed_md/{doc}_processed_definitions_golden.md"
        )
        definitions_path.parent.mkdir(parents=True, exist_ok=True)
        definitions_path.write_text("\n".join(output.definition_lines))


def _test_golden_output_md(doc: str, tools: ToolBelt):
    output = _process_trimmed(doc, tools)
    chunk_path = (
        EXTRACTION_OPS_TEST_DATA / f"processed_md/{doc}_processed_chunks_golden.md"
    )
    if not chunk_path.exists():
        logger.error("no golden chunk md found at [%s]", chunk_path)
        raise FileNotFoundError(f"no golden chunk md found at [{chunk_path}]")
    golden_chunk_lines = chunk_path.read_text().split("\n")
    logger.info("testing [%s] chunk lines against golden", doc)
    compare_lines(output.chunk_lines, golden_chunk_lines)
    if tools.definition_tools:
        definitions_path = (
            EXTRACTION_OPS_TEST_DATA
            / f"processed_md/{doc}_processed_definitions_golden.md"
        )
        if not definitions_path.exists():
            logger.error("no golden definition md found at [%s]", definitions_path)
            raise FileNotFoundError(
                f"no golden definition md found at [{definitions_path}]"
            )
        golden_definitions_lines = definitions_path.read_text().split("\n")
        logger.info("testing [%s] definition lines against golden", doc)
        compare_lines(output.definition_lines, golden_definitions_lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="process lines of md into chunk and definition lines output"
    )
    parser.add_argument(
        "doc",
        choices=TOOLBELT_REGISTRY.keys(),
        help="which document to apply process lines to",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--save-golden",
        action="store_true",
        help="write chunk and definition output as golden",
    )
    group.add_argument(
        "--test-golden",
        action="store_true",
        help="line by line comparison of chunk md and definition md output against golden template",
    )
    args = parser.parse_args()
    tools = TOOLBELT_REGISTRY[args.doc]
    if args.save_golden:
        _write_golden_output_md(args.doc, tools)
    elif args.test_golden:
        _test_golden_output_md(args.doc, tools)
    else:
        _write_test_output_md(args.doc, tools)


if __name__ == "__main__":
    setup_logging("diagnostics")
    main()
