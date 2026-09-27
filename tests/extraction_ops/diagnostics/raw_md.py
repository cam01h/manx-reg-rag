import logging
from pathlib import Path

from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.md_ops import pdf_to_md
from tests.extraction_ops.diagnostics.models import Stage
from tests.extraction_ops.diagnostics.utils import build_path, compare_lines, read_md

logger = logging.getLogger(__name__)

_STAGE = "raw_md"


def _operation(doc: str, input: Path) -> str:
    tools = TOOLBELT_REGISTRY[doc]
    return pdf_to_md(input, doc, tools.use_ocr)


def _test_golden(doc: str, input: str) -> None:
    golden_md_path = build_path(_STAGE, doc)
    golden_md_lines = read_md(golden_md_path).splitlines()
    test_md_lines = input.splitlines()
    compare_lines(test_md_lines, golden_md_lines)


RawMd = Stage(
    suffix="md",
    consumes="handled_pdf",
    operation=_operation,
    test_golden=_test_golden,
    to_text=None,
)
