import dataclasses
import hashlib
import json
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import fitz
from pydantic import TypeAdapter

from config import EXTRACTION_OPS_TEST_DATA

logger = logging.getLogger(__name__)


# NOTE: file handling
def build_path(stage: str, doc: str, mode: str = "golden", suffix: str = "md") -> Path:
    return EXTRACTION_OPS_TEST_DATA / f"{stage}/{doc}_{mode}.{suffix}"


def confirm_file(path: Path) -> None:
    if not path.exists():
        logger.error("no golden test file found at [%s]", path)
        raise FileNotFoundError(f"no golden test file found at [{path}]")


def read_md(path: Path) -> str:
    confirm_file(path)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_md(path: Path, md: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, default=dataclasses.asdict)


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


# NOTE: golden test factories
def make_pdf_golden_test(stage: str) -> Callable[[str, bytes], None]:
    def test_golden(doc: str, output: bytes) -> None:
        path = build_path(stage, doc, "golden", "pdf")
        confirm_file(path)
        if get_text_hash(output) == get_text_hash(path.read_bytes()):
            logger.info("test passed: matching text hashes")
        else:
            logger.warning("test failed: text hashes do not match")
            sys.exit(1)

    return test_golden


def make_md_golden_test(
    stage: str, to_text: Callable = lambda s: s
) -> Callable[[str, Any], None]:
    def test_golden(doc: str, output: str) -> None:
        golden_md_path = build_path(stage, doc)
        golden_md_lines = read_md(golden_md_path).splitlines()
        test_md_lines = to_text(output).splitlines()
        compare_lines(test_md_lines, golden_md_lines)

    return test_golden


def _compare_objects(test: list, golden: list) -> None:
    if len(test) != len(golden):
        logger.error(
            "object counts differ. golden: [%d] | test: [%d]", len(golden), len(test)
        )
        sys.exit(1)
    for i, (t, g) in enumerate(zip(test, golden)):
        for field in dataclasses.fields(t):
            tv, gv = getattr(t, field.name), getattr(g, field.name)
            if tv == gv:
                continue
            logger.warning("object [%d] field [%s] differs", i, field.name)
            if isinstance(tv, str):
                compare_lines(tv.splitlines(), gv.splitlines())
            elif isinstance(tv, (list, tuple)):
                compare_lines([str(x) for x in tv], [str(x) for x in gv])
            logger.warning("expected: [%s]", gv)
            logger.warning("found: [%s]", tv)
            sys.exit(1)
    logger.info("test passed: [%d] objects compared", len(test))


def make_object_golden_test(stage: str, model: type) -> Callable[[str, list], None]:
    def test_golden(doc: str, output: list) -> None:
        path = build_path(stage, doc, "golden", "json")
        confirm_file(path)
        golden = TypeAdapter(list[model]).validate_json(path.read_text())
        _compare_objects(output, golden)

    return test_golden


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
