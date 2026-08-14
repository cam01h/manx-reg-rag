import logging
import argparse
from pathlib import Path
from typing import Callable
from config import EXTRACTION_OPS_TEST_DATA, setup_logging
from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.md_ops import check_for_scope_end, check_for_scope_start
from tests.extraction_ops.diagnostics.utils import compare_lines

logger = logging.getLogger(__name__)


def _scan_lines(
    doc: str, start_marker: Callable[[str], bool], end_marker: Callable[[str], bool]
) -> str:
    input_path = EXTRACTION_OPS_TEST_DATA / f"clean_md/{doc}_golden.md"
    if not input_path.exists():
        logger.error("no initial start file found at [%s]", input_path)
        raise FileNotFoundError(
            f"no golden clean md start point found at [{input_path}]"
        )
    md_lines = input_path.read_text().splitlines()
    kept_lines = []
    in_scope = False
    for line in md_lines:
        if check_for_scope_start(doc, start_marker, in_scope, line):
            logger.info("start line detected in [%s]", doc)
            logger.info("[%s]", line)
            in_scope = True
        if in_scope:
            kept_lines.append(line)
        if check_for_scope_end(end_marker, line):
            logger.info("end line detected in [%s]", doc)
            logger.info("[%s]", line)
            break
    return "\n".join(kept_lines)


def _write_file(path: Path, md: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md)


def _write_test_trimmed_md(
    doc: str, start_marker: Callable[[str], bool], end_marker: Callable[[str], bool]
) -> None:
    trimmed_md = _scan_lines(doc, start_marker, end_marker)
    output_path = EXTRACTION_OPS_TEST_DATA / f"trimmed_md/{doc}_trimmed_test.md"
    _write_file(output_path, trimmed_md)


def _write_golden_trimmed_md(
    doc: str, start_marker: Callable[[str], bool], end_marker: Callable[[str], bool]
) -> None:
    trimmed_md = _scan_lines(doc, start_marker, end_marker)
    output_path = EXTRACTION_OPS_TEST_DATA / f"trimmed_md/{doc}_trimmed_golden.md"
    _write_file(output_path, trimmed_md)


def _test_golden_trimmed_md(
    doc: str, start_marker: Callable[[str], bool], end_marker: Callable[[str], bool]
) -> None:
    trimmed_md = _scan_lines(doc, start_marker, end_marker)
    md_lines = trimmed_md.split("\n")
    golden_path = EXTRACTION_OPS_TEST_DATA / f"trimmed_md/{doc}_trimmed_golden.md"
    if not golden_path.exists():
        logger.error("no golden template found at [%s]", golden_path)
        raise FileNotFoundError(f"no golden template found at [{golden_path}]")
    golden_md_lines = golden_path.read_text().split("\n")
    compare_lines(md_lines, golden_md_lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="apply trimmer")
    parser.add_argument(
        "doc",
        choices=TOOLBELT_REGISTRY.keys(),
        help="which document to apply the trimmer to",
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
        _write_golden_trimmed_md(args.doc, tools.trimmer.start, tools.trimmer.end)
    elif args.test_golden:
        _test_golden_trimmed_md(args.doc, tools.trimmer.start, tools.trimmer.end)
    else:
        _write_test_trimmed_md(args.doc, tools.trimmer.start, tools.trimmer.end)


if __name__ == "__main__":
    setup_logging("diagnostics")
    main()
