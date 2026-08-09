import argparse
import dataclasses
import logging
import json
from typing import Callable
from config import EXTRACTION_OPS_TEST_DATA, setup_logging
from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.chunking import segment_by_headers
from extraction_ops.models import Section
from tests.extraction_ops.diagnostics.utils import compare_lines

logger = logging.getLogger(__name__)


def _get_sections(doc: str, matchers: list[Callable[[str], bool]]) -> list[Section]:
    input_path = (
        EXTRACTION_OPS_TEST_DATA / f"processed_md/{doc}_processed_chunks_golden.md"
    )
    chunk_lines = input_path.read_text().split("\n")
    sections = segment_by_headers(chunk_lines, matchers)
    if len(sections) > 1:
        logger.info(
            "[%d] sections found in [%s], each with [%d] levels",
            len(sections),
            doc,
            len(sections[0].headers),
        )
    elif sections:
        logger.warning(
            "single section found in [%s]: [%s]", doc, str(sections[0].headers)
        )
    else:
        logger.warning("no sections found in [%s]", doc)
    return sections


def _write_test_sections(doc: str, matchers: list[Callable[[str], bool]]) -> None:
    sections = _get_sections(doc, matchers)
    output_path = EXTRACTION_OPS_TEST_DATA / f"sections/{doc}_sections_test.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join([str(section) for section in sections]))


def _write_golden_sections(doc: str, matchers: list[Callable[[str], bool]]) -> None:
    sections = _get_sections(doc, matchers)
    readable_output_path = (
        EXTRACTION_OPS_TEST_DATA / f"sections/{doc}_sections_golden.md"
    )
    readable_output_path.parent.mkdir(parents=True, exist_ok=True)
    readable_output_path.write_text("\n".join([str(section) for section in sections]))
    json_output_path = EXTRACTION_OPS_TEST_DATA / f"sections/{doc}_sections_golden.json"
    json_output_path.parent.mkdir(parents=True, exist_ok=True)
    sections_as_dicts = [dataclasses.asdict(s) for s in sections]
    json_output_path.write_text(json.dumps(sections_as_dicts, indent=2))


def _test_golden_sections(doc: str, matchers: list[Callable[[str], bool]]) -> None:
    test_sections = _get_sections(doc, matchers)
    golden_path = EXTRACTION_OPS_TEST_DATA / f"sections/{doc}_sections_golden.json"
    if not golden_path.exists():
        logger.error("no golden sections json found at [%s]", golden_path)
        raise FileNotFoundError(f"no golden sections md found at [{golden_path}]")
    loaded_data = json.loads(golden_path.read_text())
    loaded_sections = [
        Section(
            headers=tuple(str(h) for h in d["headers"]),
            body_lines=[str(b) for b in d["body_lines"]],
        )
        for d in loaded_data
    ]
    if len(test_sections) != len(loaded_sections):
        logger.info(
            "different number of sections found between test and golden data in [%s]",
            doc,
        )
        raise ValueError(
            f"different number of sections found between test and golden data in {doc}"
        )
    logger.info("comparing headers of [%s]", doc)
    test_headers = [str(s.headers) for s in test_sections]
    golden_headers = [str(s.headers) for s in loaded_sections]
    compare_lines(test_headers, golden_headers)
    logger.info("comparing body lines of [%s]", doc)
    test_body_lines = [s.body_lines for s in test_sections]
    golden_body_lines = [s.body_lines for s in loaded_sections]
    for test, golden in zip(test_body_lines, golden_body_lines):
        compare_lines(test, golden)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="process golden chunk lines into Sections"
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
        help="write sections as golden",
    )
    group.add_argument(
        "--test-golden",
        action="store_true",
        help="direct comparison of section headers and line by line comparison of body lines against golden template",
    )
    args = parser.parse_args()
    tools = TOOLBELT_REGISTRY[args.doc]
    if args.save_golden:
        _write_golden_sections(args.doc, tools.header_matchers)
    elif args.test_golden:
        _test_golden_sections(args.doc, tools.header_matchers)
    else:
        _write_test_sections(args.doc, tools.header_matchers)


if __name__ == "__main__":
    setup_logging("diagnostics")
    main()
