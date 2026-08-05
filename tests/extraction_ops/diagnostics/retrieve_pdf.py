import argparse
from config import EXTRACTION_OPS_TEST_DATA, setup_logging
from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.load_to_md import get_pdf_from_url
from extraction_ops.models import ToolBelt
from tests.extraction_ops.diagnostics.utils import get_text_hash
import logging
import sys

logger = logging.getLogger(__name__)


def _write_test(tools: ToolBelt, doc: str) -> None:
    path = EXTRACTION_OPS_TEST_DATA / f"raw_pdf/{doc}_test.pdf"
    path.parent.mkdir(parents=True, exist_ok=True)
    get_pdf_from_url(tools.document, tools.input_url, path)


def _write_golden(tools: ToolBelt, doc: str) -> None:
    path = EXTRACTION_OPS_TEST_DATA / f"raw_pdf/{doc}_golden.pdf"
    path.parent.mkdir(parents=True, exist_ok=True)
    get_pdf_from_url(tools.document, tools.input_url, path)
    text_hash = get_text_hash(path)
    hash_path = EXTRACTION_OPS_TEST_DATA / f"raw_pdf/{doc}_golden_hash.txt"
    hash_path.parent.mkdir(parents=True, exist_ok=True)
    hash_path.write_text(text_hash)


def _test_golden(tools: ToolBelt, doc: str) -> None:
    golden_path = EXTRACTION_OPS_TEST_DATA / f"raw_pdf/{doc}_golden_hash.txt"
    try:
        golden_text_hash = golden_path.read_text().strip()
    except FileNotFoundError:
        logger.exception("no golden hash file created")
        raise
    test_path = EXTRACTION_OPS_TEST_DATA / f"raw_pdf/{doc}_test.pdf"
    test_path.parent.mkdir(parents=True, exist_ok=True)
    _write_test(tools, doc)
    test_text_hash = get_text_hash(test_path)
    if test_text_hash == golden_text_hash:
        logger.info("test passed: matching hashes detected")
    else:
        logger.warning("test failed: hashes do not match")
        logger.warning("golden hash: [%s]", golden_text_hash)
        logger.warning("test hash: [%s]", test_text_hash)
        sys.exit(1)


def diagnostic_pdf_retrieval() -> None:
    parser = argparse.ArgumentParser(description="Retrieve PDF for a doc")
    parser.add_argument(
        "doc", choices=TOOLBELT_REGISTRY.keys(), help="which document to retrieve"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--save-golden",
        action="store_true",
        help="Save the downloaded PDF and its text hash as the new golden template",
    )
    group.add_argument(
        "--test-golden",
        action="store_true",
        help="Test the hash of the contents of a fresh test pdf against a known golden file",
    )
    args = parser.parse_args()
    tools = TOOLBELT_REGISTRY[args.doc]
    if args.save_golden:
        _write_golden(tools, args.doc)
    elif args.test_golden:
        _test_golden(tools, args.doc)
    else:
        _write_test(tools, args.doc)


if __name__ == "__main__":
    setup_logging("diagnostics")
    diagnostic_pdf_retrieval()
