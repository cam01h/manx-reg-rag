import argparse
import json
import logging
import sys
from config import EXTRACTION_OPS_TEST_DATA, setup_logging
from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.definitions import build_term_variants
from tests.extraction_ops.diagnostics.utils import compare_lines

logger = logging.getLogger(__name__)


def _load_variants(doc: str) -> dict[str, list[str]]:
    input_path = (
        EXTRACTION_OPS_TEST_DATA
        / f"extracted_definitions/{doc}_definitions_golden.json"
    )
    loaded_data = json.loads(input_path.read_text())
    return build_term_variants([d["term"] for d in loaded_data])


def _write_test_output(doc: str) -> None:
    variants = _load_variants(doc)
    test_path = (
        EXTRACTION_OPS_TEST_DATA / f"term_variants/{doc}_term_variants_test.json"
    )
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_text(json.dumps(variants, indent=2))


def _write_golden_output(doc: str) -> None:
    variants = _load_variants(doc)
    golden_path = (
        EXTRACTION_OPS_TEST_DATA / f"term_variants/{doc}_term_variants_golden.json"
    )
    golden_path.parent.mkdir(parents=True, exist_ok=True)
    golden_path.write_text(json.dumps(variants, indent=2))


def _test_golden(doc: str) -> None:
    variants: dict[str, list[str]] = _load_variants(doc)
    golden_path = (
        EXTRACTION_OPS_TEST_DATA / f"term_variants/{doc}_term_variants_golden.json"
    )
    if not golden_path.exists():
        logger.error("no [%s] golden file found found at [%s]", doc, golden_path)
        raise FileNotFoundError(f"no {doc} golden file found found at {golden_path}")
    golden_data: dict[str, list[str]] = json.loads(golden_path.read_text())
    if len(variants) != len(golden_data):
        logger.error(
            "test terms = [%d], golden terms = [%s]",
            len(variants),
            len(golden_data),
        )
        sys.exit(1)
    for (test_t, test_v), (golden_t, golden_v) in zip(
        variants.items(), golden_data.items()
    ):
        if test_t != golden_t:
            logger.error(
                "term not matched. test = [%s], golden = [%s]",
                test_t,
                golden_t,
            )
            logger.info("this could be an order error, manual inspection recommended")
            sys.exit(1)
        elif len(test_v) != len(golden_v):
            logger.error(
                "for [%s] test found [%d] variants and golden found [%d] variants",
                test_t,
                len(test_v),
                len(golden_v),
            )
            sys.exit(1)
        else:
            logger.info("test term: [%s], golden term: [%s]", test_t, golden_t)
            compare_lines(test_v, golden_v)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="for identified definition terms, extract term variants to json"
    )
    parser.add_argument(
        "doc",
        choices=TOOLBELT_REGISTRY.keys(),
        help="which document to apply build term variants",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--save-golden",
        action="store_true",
        help="write term variants json as golden",
    )
    group.add_argument(
        "--test-golden",
        action="store_true",
        help="comparison of terms and a comparison of variants per term against golden template",
    )
    args = parser.parse_args()
    tools = TOOLBELT_REGISTRY[args.doc]
    if tools.definition_tools is not None:
        if args.save_golden:
            _write_golden_output(args.doc)
        elif args.test_golden:
            _test_golden(args.doc)
        else:
            _write_test_output(args.doc)
    else:
        logger.info("no definition tools found in [%s]", args.doc)


if __name__ == "__main__":
    setup_logging("diagnostics")
    main()
