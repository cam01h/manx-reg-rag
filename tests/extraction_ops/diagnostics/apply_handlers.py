import argparse
import os
from pathlib import Path
import shutil
import logging
import sys
from typing import Callable
from config import EXTRACTION_OPS_TEST_DATA, setup_logging
from extraction_ops import TOOLBELT_REGISTRY
from tests.extraction_ops.diagnostics.utils import get_text_hash

logger = logging.getLogger(__name__)


def _apply_one_handler(
    input_path: Path, output_path: Path, handler: Callable[[Path], None]
) -> str:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(input_path, output_path)
    handler(output_path)
    text_hash = get_text_hash(output_path)
    return text_hash


def _write_test_pdfs(doc: str, handlers: list[Callable[[Path], None]]) -> None:
    input_path = EXTRACTION_OPS_TEST_DATA / f"raw_pdf/{doc}_golden.pdf"
    if not os.path.exists(input_path):
        logger.warning(
            "no golden file found from previous operation at [%s]", input_path
        )
        raise FileNotFoundError(f"No golden file found at {input_path}")
    for i, handler in enumerate(handlers):
        output_path = EXTRACTION_OPS_TEST_DATA / f"handled_pdf/{doc}_test{i + 1}.pdf"
        _apply_one_handler(input_path, output_path, handler)
        input_path = output_path


def _write_golden(doc: str, handlers: list[Callable[[Path], None]]) -> None:
    input_path = EXTRACTION_OPS_TEST_DATA / f"raw_pdf/{doc}_golden.pdf"
    if not os.path.exists(input_path):
        logger.warning(
            "no golden file found from previous opperation at [%s]", input_path
        )
        raise FileNotFoundError
    for i, handler in enumerate(handlers):
        output_path = EXTRACTION_OPS_TEST_DATA / f"handled_pdf/{doc}_golden{i + 1}.pdf"
        text_hash = _apply_one_handler(input_path, output_path, handler)
        hash_path = (
            EXTRACTION_OPS_TEST_DATA / f"handled_pdf/{doc}_golden_hash{i + 1}.txt"
        )
        hash_path.write_text(text_hash)
        input_path = output_path


def _test_golden(doc: str, handlers: list[Callable[[Path], None]]) -> None:
    passed_tests = 0
    temp_paths = []
    break_occured = False
    input_path = EXTRACTION_OPS_TEST_DATA / f"raw_pdf/{doc}_golden.pdf"
    if not os.path.exists(input_path):
        logger.warning(
            "no golden file found from previous opperation at [%s]", input_path
        )
        raise FileNotFoundError
    for i, handler in enumerate(handlers):
        output_path = EXTRACTION_OPS_TEST_DATA / f"handled_pdf/{doc}_temp{i + 1}.pdf"
        temp_paths.append(output_path)
        text_hash = _apply_one_handler(input_path, output_path, handler)
        hash_path = (
            EXTRACTION_OPS_TEST_DATA / f"handled_pdf/{doc}_golden_hash{i + 1}.txt"
        )
        try:
            golden_hash = hash_path.read_text()
        except FileNotFoundError:
            logger.error(
                "no golden hash file detected for handler for handler [%d]", i + 1
            )
            break_occured = True
            break
        if text_hash == golden_hash:
            passed_tests += 1
        else:
            logger.warning("test hash did not match golden_hash on handler [%d]", i + 1)
        input_path = output_path

    for path in temp_paths:
        os.remove(path)

    if break_occured:
        sys.exit(1)
    if passed_tests == len(handlers):
        logger.info(
            "[%d] tests passed against [%d] handlers", passed_tests, len(handlers)
        )
    else:
        logger.warning(
            "[%d] tests passed against [%d] handlers", passed_tests, len(handlers)
        )
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply pdf handlers to the documents")
    parser.add_argument(
        "doc",
        choices=TOOLBELT_REGISTRY.keys(),
        help="which document to apply pdf handlers to",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--save-golden",
        action="store_true",
        help="Save the handled PDFs and a hash of the text in each as the new golden template",
    )
    group.add_argument(
        "--test-golden",
        action="store_true",
        help="Test the hash of the contents of a fresh handled pdf against a known golden file",
    )
    args = parser.parse_args()
    tools = TOOLBELT_REGISTRY[args.doc]
    if tools.pdf_handlers is None:
        logger.info("[%s] has no attached pdf handlers", args.doc)
    else:
        if args.save_golden:
            _write_golden(args.doc, tools.pdf_handlers)
        elif args.test_golden:
            _test_golden(args.doc, tools.pdf_handlers)
        else:
            _write_test_pdfs(args.doc, tools.pdf_handlers)


if __name__ == "__main__":
    setup_logging("diagnostics")
    main()
