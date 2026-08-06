import argparse
from pathlib import Path
from typing import Callable
import logging
from config import EXTRACTION_OPS_TEST_DATA, setup_logging
from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.load_to_md import pdf_to_md
from tests.extraction_ops.diagnostics.utils import compare_lines

logger = logging.getLogger(__name__)


def _get_start_file(doc: str, handlers: list[Callable[[Path], None]] | None) -> Path:
    if handlers:
        return EXTRACTION_OPS_TEST_DATA / f"handled_pdf/{doc}_golden{len(handlers)}.pdf"
    else:
        return EXTRACTION_OPS_TEST_DATA / f"raw_pdf/{doc}_golden.pdf"


def _write_test(doc: str, md: str) -> None:
    path = EXTRACTION_OPS_TEST_DATA / f"raw_md/{doc}_test.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md)


def _write_golden(doc: str, md: str) -> None:
    path = EXTRACTION_OPS_TEST_DATA / f"raw_md/{doc}_golden.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md)


def _test_golden(doc: str, test_md: str) -> None:
    golden_path = EXTRACTION_OPS_TEST_DATA / f"raw_md/{doc}_golden.md"
    if not golden_path.exists():
        logger.error("no golden test file found at [%s]", golden_path)
        raise FileNotFoundError(f"no golden test file found at [{golden_path}]")
    golden_md = golden_path.read_text()
    test_md_lines = test_md.splitlines()
    golden_md_lines = golden_md.splitlines()
    compare_lines(test_md_lines, golden_md_lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="convert existing golden pdf to md via pymupdf4llm"
    )
    parser.add_argument(
        "doc",
        choices=TOOLBELT_REGISTRY.keys(),
        help="which pdf convert",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--save-golden",
        action="store_true",
        help="save output md as golden template",
    )
    group.add_argument(
        "--test-golden",
        action="store_true",
        help="line by line comparison of test md with known golden template",
    )
    args = parser.parse_args()
    tools = TOOLBELT_REGISTRY[args.doc]
    input_path = _get_start_file(args.doc, tools.pdf_handlers)
    md = pdf_to_md(input_path, args.doc, tools.use_ocr)
    if args.save_golden:
        _write_golden(args.doc, md)
    elif args.test_golden:
        _test_golden(args.doc, md)
    else:
        _write_test(args.doc, md)


if __name__ == "__main__":
    setup_logging("diagnostics")
    main()
