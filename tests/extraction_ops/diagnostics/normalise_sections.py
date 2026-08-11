import argparse
import json
import logging
import dataclasses
from config import EXTRACTION_OPS_TEST_DATA, setup_logging
from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.chunking import normalise_sections
from extraction_ops.models import CleanSection, Section, ToolBelt
from tests.extraction_ops.diagnostics.utils import compare_lines

logger = logging.getLogger(__name__)


def _get_normalised_from_golden_sections(
    doc: str, tools: ToolBelt
) -> list[CleanSection]:
    golden_sections_path = (
        EXTRACTION_OPS_TEST_DATA / f"sections/{doc}_sections_golden.json"
    )
    if not golden_sections_path.exists():
        logger.error("no golden sections json found at [%s]", golden_sections_path)
        raise FileNotFoundError(
            f"no golden sections json found at [{golden_sections_path}]"
        )
    loaded_data = json.loads(golden_sections_path.read_text())
    loaded_sections = [
        Section(
            headers=tuple(str(h) for h in d["headers"]),
            body_lines=[str(b) for b in d["body_lines"]],
        )
        for d in loaded_data
    ]
    normalised = normalise_sections(tools, loaded_sections)
    logger.info(
        "[%d] Sections normalised into [%d] CleanSections",
        len(loaded_sections),
        len(normalised),
    )
    return normalised


def _write_test_normalised_sections(doc: str, tools: ToolBelt) -> None:
    normalised = _get_normalised_from_golden_sections(doc, tools)
    output_path = (
        EXTRACTION_OPS_TEST_DATA / f"normalised_sections/{doc}_cleansections_test.txt"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join([str(s) for s in normalised]))


def _write_golden_normalised_sections(doc: str, tools: ToolBelt) -> None:
    normalised = _get_normalised_from_golden_sections(doc, tools)
    output_path = (
        EXTRACTION_OPS_TEST_DATA / f"normalised_sections/{doc}_cleansections_golden.txt"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join([str(s) for s in normalised]))
    json_output_path = (
        EXTRACTION_OPS_TEST_DATA
        / f"normalised_sections/{doc}_cleansections_golden.json"
    )
    json_output_path.parent.mkdir(parents=True, exist_ok=True)
    normalised_as_dicts = [dataclasses.asdict(s) for s in normalised]
    json_output_path.write_text(json.dumps(normalised_as_dicts, indent=2))


def _test_normalised_sections(doc: str, tools: ToolBelt) -> None:
    normalised = _get_normalised_from_golden_sections(doc, tools)
    golden_path = (
        EXTRACTION_OPS_TEST_DATA
        / f"normalised_sections/{doc}_cleansections_golden.json"
    )
    loaded_data = json.loads(golden_path.read_text())
    loaded_sections = [
        CleanSection(
            headers=tuple(str(h) for h in d["headers"]),
            body=d["body"],
        )
        for d in loaded_data
    ]
    logger.info("comparing headers of [%s]", doc)
    if len(normalised) != len(loaded_sections):
        logger.info(
            "different number of CleanSections found between test and golden data in [%s]",
            doc,
        )
        raise ValueError(
            f"different number of CleanSections found between test and golden data in {doc}"
        )
    for test, golden in zip(normalised, loaded_sections):
        compare_lines(test.headers, golden.headers)
    logger.info("comparing body lines of [%s]", doc)
    test_body_lines = [s.body.split("\n") for s in normalised]
    golden_body_lines = [s.body.split("\n") for s in loaded_sections]
    for test, golden in zip(test_body_lines, golden_body_lines):
        compare_lines(test, golden)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="process golden Sections into normalised CleanSections"
    )
    parser.add_argument(
        "doc",
        choices=TOOLBELT_REGISTRY.keys(),
        help="which document to apply normalise_sections to",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--save-golden",
        action="store_true",
        help="write normalised CleanSections as golden",
    )
    group.add_argument(
        "--test-golden",
        action="store_true",
        help="direct comparison of CleanSection headers and line by line comparison of body lines against golden template",
    )
    args = parser.parse_args()
    tools = TOOLBELT_REGISTRY[args.doc]
    if args.save_golden:
        _write_golden_normalised_sections(args.doc, tools)
    elif args.test_golden:
        _test_normalised_sections(args.doc, tools)
    else:
        _write_test_normalised_sections(args.doc, tools)


if __name__ == "__main__":
    setup_logging("diagnostics")
    main()
