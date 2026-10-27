import logging
from pathlib import Path

from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.md_ops import pdf_to_md
from tests.extraction_ops.diagnostics.models import Stage
from tests.extraction_ops.diagnostics.utils import (
    make_md_golden_test,
)

logger = logging.getLogger(__name__)

_STAGE = "raw_md"


def _operation(doc: str, input: Path) -> str:
    tools = TOOLBELT_REGISTRY[doc]
    return pdf_to_md(input, doc, tools.use_ocr, tools.use_layout, tools.md_options)


RawMd = Stage(
    suffix="md",
    consumes="handled_pdf",
    operation=_operation,
    test_golden=make_md_golden_test(_STAGE),
    to_text=None,
)
