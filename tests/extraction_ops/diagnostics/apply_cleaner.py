import argparse
from pathlib import Path
from typing import Callable
import logging
from config import EXTRACTION_OPS_TEST_DATA
from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.load_to_md import clean_md_to_lines
from tests.extraction_ops.diagnostics.utils import compare_lines
from config import setup_logging

logger = logging.getLogger(__name__)


def _get_start_file(doc: str) -> Path:
    input_path = EXTRACTION_OPS_TEST_DATA / f"raw_md/{doc}_golden.md"
    if not input_path.exists():
        logger.error("no initial start file found at [%s]", input_path)
        raise FileNotFoundError(f"no golden test file found at [{input_path}]")
    return input_path


def _get_clean_md(doc: str, cleaner: Callable[[str], str]) -> str:
    input_path = _get_start_file(doc)
    md = input_path.read_text()
    clean_md_lines = clean_md_to_lines(cleaner, md)
    return "\n".join(clean_md_lines)


def _write_cleaned_test_md(doc: str, cleaner: Callable[[str], str]) -> None:
    clean_md = _get_clean_md(doc, cleaner)
    output_path = EXTRACTION_OPS_TEST_DATA / f"clean_md/{doc}_test.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(clean_md)
    logger.info("cleaner applied to [%s]", doc)


def _write_golden_clean_md(doc: str, cleaner: Callable[[str], str]) -> None:
    clean_md = _get_clean_md(doc, cleaner)
    output_path = EXTRACTION_OPS_TEST_DATA / f"clean_md/{doc}_golden.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(clean_md)
    logger.info("golden cleaned md file written for [%s]", doc)


def _test_golden_clean_md(doc: str, cleaner: Callable[[str], str]) -> None:
    input_path = _get_start_file(doc)
    md = input_path.read_text()
    clean_md_lines = clean_md_to_lines(cleaner, md)
    golden_md_path = EXTRACTION_OPS_TEST_DATA / f"clean_md/{doc}_golden.md"
    if not golden_md_path.exists():
        logger.error("no golden template found at [%s]", golden_md_path)
        raise FileNotFoundError(f"no golden template found at [{golden_md_path}]")
    golden_md = golden_md_path.read_text()
    compare_lines(clean_md_lines, golden_md.split("\n"))


def main() -> None:
    parser = argparse.ArgumentParser(description="apply test cleaner")
    parser.add_argument(
        "doc",
        choices=TOOLBELT_REGISTRY.keys(),
        help="which document to apply the cleaner to",
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
    if args.save_golden:
        _write_golden_clean_md(args.doc, tools.clean_text)
    elif args.test_golden:
        _test_golden_clean_md(args.doc, tools.clean_text)
    else:
        _write_cleaned_test_md(args.doc, tools.clean_text)


if __name__ == "__main__":
    setup_logging("diagnostics")
    main()
