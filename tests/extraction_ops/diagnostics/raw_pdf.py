import logging

from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.pdf_ops import fetch_pdf

from .models import Stage
from .utils import (
    make_pdf_golden_test,
)

logger = logging.getLogger(__name__)

_STAGE = "raw_pdf"


def _operation(doc: str, _input=None) -> bytes:
    tools = TOOLBELT_REGISTRY[doc]
    return fetch_pdf(tools.document, tools.input_url)


RawPdf = Stage(
    suffix="pdf",
    consumes=None,
    operation=_operation,
    test_golden=make_pdf_golden_test(_STAGE),
    to_text=None,
)
