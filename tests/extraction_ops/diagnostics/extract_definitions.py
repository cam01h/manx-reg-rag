import argparse
import dataclasses
import json
import logging
import sys
from config import EXTRACTION_OPS_TEST_DATA, setup_logging
from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.definitions import extract_to_definitions
from extraction_ops.models import Definition, ToolBelt
from tests.extraction_ops.diagnostics.utils import compare_lines

logger = logging.getLogger(__name__)


def _load_definitions(doc: str, tools: ToolBelt) -> list[Definition]:
    definitions_path = (
        EXTRACTION_OPS_TEST_DATA / f"processed_md/{doc}_processed_definitions_test.md"
    )
    definition_lines = definitions_path.read_text().split("\n")
    return extract_to_definitions(tools, definition_lines)


def _write_test_output(doc: str, tools: ToolBelt) -> None:
    definition_list: list[Definition] = _load_definitions(doc, tools)
    test_path = (
        EXTRACTION_OPS_TEST_DATA / f"extracted_definitions/{doc}_definitions_test.json"
    )
    test_path.parent.mkdir(parents=True, exist_ok=True)
    definitions_as_dicts = [dataclasses.asdict(d) for d in definition_list]
    test_path.write_text(json.dumps(definitions_as_dicts, indent=2))


def _write_golden_output(doc: str, tools: ToolBelt) -> None:
    definition_list: list[Definition] = _load_definitions(doc, tools)
    test_path = (
        EXTRACTION_OPS_TEST_DATA
        / f"extracted_definitions/{doc}_definitions_golden.json"
    )
    test_path.parent.mkdir(parents=True, exist_ok=True)
    definitions_as_dicts = [dataclasses.asdict(d) for d in definition_list]
    test_path.write_text(json.dumps(definitions_as_dicts, indent=2))


def _test_golden(doc: str, tools: ToolBelt) -> None:
    definition_list: list[Definition] = _load_definitions(doc, tools)
    definitions_as_dicts = [dataclasses.asdict(d) for d in definition_list]
    golden_path = (
        EXTRACTION_OPS_TEST_DATA
        / f"extracted_definitions/{doc}_definitions_golden.json"
    )
    golden_data = json.loads(golden_path.read_text())
    if len(definitions_as_dicts) != len(golden_data):
        logger.error(
            "test definitions = [%d], golden definitions = [%s]",
            len(definitions_as_dicts),
            len(golden_data),
        )
        sys.exit(1)
    for test, golden in zip(definitions_as_dicts, golden_data):
        if test["document"] != golden["document"]:
            logger.error(
                "document not matched. test = [%s], golden = [%s]",
                test["document"],
                golden["document"],
            )
            sys.exit(1)
        elif test["term"] != golden["term"]:
            logger.error(
                "term not matched. test = [%s], golden = [%s]",
                test["term"],
                golden["term"],
            )
            logger.info("this could be an order error, manual inspection recommended")
            sys.exit(1)
        else:
            logger.info("term: [%s]", test["term"])
            compare_lines(
                test["definition"].split("\n"), golden["definition"].split("\n")
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="segment definfitions md into json")
    parser.add_argument(
        "doc",
        choices=TOOLBELT_REGISTRY.keys(),
        help="which document to apply extract definitions to",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--save-golden",
        action="store_true",
        help="write definitions json as golden",
    )
    group.add_argument(
        "--test-golden",
        action="store_true",
        help="line by line comparison of definition json against golden template",
    )
    args = parser.parse_args()
    tools = TOOLBELT_REGISTRY[args.doc]
    if tools.definition_tools is not None:
        if args.save_golden:
            _write_golden_output(args.doc, tools)
        elif args.test_golden:
            _test_golden(args.doc, tools)
        else:
            _write_test_output(args.doc, tools)
    else:
        logger.info("no definition tools found in [%s]", args.doc)


if __name__ == "__main__":
    setup_logging("diagnostics")
    main()
