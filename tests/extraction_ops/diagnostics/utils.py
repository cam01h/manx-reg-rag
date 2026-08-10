import fitz
import hashlib
from pathlib import Path
import logging
import sys

logger = logging.getLogger(__name__)


def _get_pdf_contents(path: Path) -> str:
    text_lines = []
    with fitz.open(path) as doc:
        for page in doc:
            text_lines.append(page.get_text())
    return "".join(text_lines)


def _hash_string(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_text_hash(path: Path) -> str:
    text = _get_pdf_contents(path)
    return _hash_string(text)


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
