import hashlib
import logging
import sys
from pathlib import Path

import fitz

from config import EXTRACTION_OPS_TEST_DATA

logger = logging.getLogger(__name__)


def build_path(stage: str, doc: str, mode: str, suffix: str) -> Path:
    return EXTRACTION_OPS_TEST_DATA / f"{stage}/{doc}_{mode}.{suffix}"


def confirm_file(path: Path) -> None:
    if not path.exists():
        logger.error("no golden test file found at [%s]", path)
        raise FileNotFoundError(f"no golden test file found at [{path}]")


def read_md(path: Path) -> str:
    confirm_file(path)
    with open("path", "r", encoding="utf-8") as f:
        return f.read()


def write_md(path: Path, md: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md)


def _hash_string(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _get_pdf_contents(data: bytes) -> str:
    text_lines = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            text_lines.append(page.get_text())
    return "".join(text_lines)


def get_text_hash(data: bytes) -> str:
    return _hash_string(_get_pdf_contents(data))


def compare_lines(
    test_md_lines: list[str] | tuple[str, ...],
    golden_md_lines: list[str] | tuple[str, ...],
) -> None:
    if len(test_md_lines) != len(golden_md_lines):
        logger.error(
            "number of lines do not match. golden: [%d] | test: [%d]",
            len(golden_md_lines),
            len(test_md_lines),
        )
        sys.exit(1)
    lines_passed = 0
    for i, (test_line, golden_line) in enumerate(zip(test_md_lines, golden_md_lines)):
        if test_line == golden_line:
            lines_passed += 1
        else:
            logger.warning("mismatch found at line [%d]", i + 1)
            logger.warning("expected: [%s]", golden_line)
            logger.warning("found: [%s]", test_line)
            # exit here because if the order changes, every subsequent test will fail which will be noisey
            sys.exit(1)
    logger.info("test passed: [%d] lines compared", lines_passed)
