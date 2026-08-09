import argparse
import logging
from typing import Callable
from config import EXTRACTION_OPS_TEST_DATA, setup_logging
from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.chunking import segment_by_headers
from tests.extraction_ops.diagnostics.utils import compare_lines

logger = logging.getLogger(__name__)


def _get_headers(doc: str, matchers: list[Callable[[str], bool]]) -> list[str]:
    input_path = (
        EXTRACTION_OPS_TEST_DATA / f"processed_md/{doc}_processed_chunks_golden.md"
    )
    chunk_lines = input_path.read_text().split("\n")
    sections = segment_by_headers(chunk_lines, matchers)
    if len(sections) > 1:
        logger.info(
            "[%d] headers found in [%s], each with [%d] levels",
            len(sections),
            doc,
            len(sections[0].headers),
        )
    elif sections:
        logger.warning(
            "single segment found in [%s]: [%s]", doc, str(sections[0].headers)
        )
    else:
        logger.warning("no sections found in [%s]", doc)
    return [str(s.headers) for s in sections]


def _write_test_headers(doc: str, matchers: list[Callable[[str], bool]]) -> None:
    headers = _get_headers(doc, matchers)
    output_path = EXTRACTION_OPS_TEST_DATA / f"headers/{doc}_headers_test.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(headers))


def _write_golden_headers(doc: str, matchers: list[Callable[[str], bool]]) -> None:
    headers = _get_headers(doc, matchers)
    output_path = EXTRACTION_OPS_TEST_DATA / f"headers/{doc}_headers_golden.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(headers))


def _test_golden_headers(doc: str, matchers: list[Callable[[str], bool]]) -> None:
    test_headers = _get_headers(doc, matchers)
    golden_path = EXTRACTION_OPS_TEST_DATA / f"headers/{doc}_headers_golden.md"
    if not golden_path.exists():
        logger.error("no golden headers md found at [%s]", golden_path)
        raise FileNotFoundError(f"no golden headers md found at [{golden_path}]")
    golden_headers = golden_path.read_text()
    compare_lines(test_headers, golden_headers.split("\n"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="process golden chunk lines into headers only"
    )
    parser.add_argument(
        "doc",
        choices=TOOLBELT_REGISTRY.keys(),
        help="which document to apply segment_by_headers to",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--save-golden",
        action="store_true",
        help="write section headers as golden",
    )
    group.add_argument(
        "--test-golden",
        action="store_true",
        help="line by line comparison of headers against golden template",
    )
    args = parser.parse_args()
    tools = TOOLBELT_REGISTRY[args.doc]
    if args.save_golden:
        _write_golden_headers(args.doc, tools.header_matchers)
    elif args.test_golden:
        _test_golden_headers(args.doc, tools.header_matchers)
    else:
        _write_test_headers(args.doc, tools.header_matchers)


if __name__ == "__main__":
    setup_logging("diagnostics")
    main()
