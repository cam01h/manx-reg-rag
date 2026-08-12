import argparse
import logging
from typing import Callable
from config import EXTRACTION_OPS_TEST_DATA, setup_logging
from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.definitions import segment_by_definitions
from tests.extraction_ops.diagnostics.utils import compare_lines

logger = logging.getLogger(__name__)


def _parse_to_readable(sections: list[list[str]]) -> str:
    readable_sections = []
    for section in sections:
        def_line = f"[{section[0]}]\n"
        body = "\n".join(section[1:])
        readable_sections.append(def_line + body)
    return "\n---\n".join(readable_sections)


def _get_definition_sections(
    doc: str, is_definition_line: Callable[[str], bool]
) -> str:
    definitions_path = (
        EXTRACTION_OPS_TEST_DATA / f"processed_md/{doc}_processed_definitions_test.md"
    )
    definition_lines = definitions_path.read_text().split("\n")
    return _parse_to_readable(
        segment_by_definitions(definition_lines, is_definition_line)
    )


def _write_test_output(doc: str, is_definition_line: Callable[[str], bool]) -> None:
    output = _get_definition_sections(doc, is_definition_line)
    test_path = (
        EXTRACTION_OPS_TEST_DATA
        / f"definition_sections/{doc}_definitions_sections_test.md"
    )
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_text(output)


def _write_golden_output(doc: str, is_definition_line: Callable[[str], bool]) -> None:
    output = _get_definition_sections(doc, is_definition_line)
    golden_path = (
        EXTRACTION_OPS_TEST_DATA
        / f"definition_sections/{doc}_definitions_sections_golden.md"
    )
    golden_path.parent.mkdir(parents=True, exist_ok=True)
    golden_path.write_text(output)


def _test_golden(doc: str, is_definition_line: Callable[[str], bool]) -> None:
    test_md = _get_definition_sections(doc, is_definition_line)
    golden_path = (
        EXTRACTION_OPS_TEST_DATA
        / f"definition_sections/{doc}_definitions_sections_golden.md"
    )
    if not golden_path.exists():
        logger.error("no golden definition md found at [%s]", golden_path)
        raise FileNotFoundError(f"no golden definition md found at [{golden_path}]")
    golden_md = golden_path.read_text()
    compare_lines(test_md.split("\n"), golden_md.split("\n"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="segment definfitions md into readable defintion sections"
    )
    parser.add_argument(
        "doc",
        choices=TOOLBELT_REGISTRY.keys(),
        help="which document to apply segment by definitions to",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--save-golden",
        action="store_true",
        help="write definition sections output as golden",
    )
    group.add_argument(
        "--test-golden",
        action="store_true",
        help="line by line comparison of definition sections md output against golden template",
    )
    args = parser.parse_args()
    tools = TOOLBELT_REGISTRY[args.doc]
    if tools.definition_tools is not None:
        if args.save_golden:
            _write_golden_output(args.doc, tools.definition_tools.is_definition_line)
        elif args.test_golden:
            _test_golden(args.doc, tools.definition_tools.is_definition_line)
        else:
            _write_test_output(args.doc, tools.definition_tools.is_definition_line)
    else:
        logger.info("no definition tools found in [%s]", args.doc)


if __name__ == "__main__":
    setup_logging("diagnostics")
    main()
