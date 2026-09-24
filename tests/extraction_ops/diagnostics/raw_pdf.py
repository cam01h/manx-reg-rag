import logging
import sys

from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.pdf_ops import fetch_pdf
from tests.extraction_ops.diagnostics.models import Stage
from tests.extraction_ops.diagnostics.utils import (
    build_path,
    confirm_file,
    get_text_hash,
)

logger = logging.getLogger(__name__)

_STAGE = "raw_pdf"


def _operation(doc: str, _input=None) -> bytes:
    tools = TOOLBELT_REGISTRY[doc]
    return fetch_pdf(tools.document, tools.input_url)


def _test_golden(doc: str, output: bytes) -> None:
    path = build_path(_STAGE, doc, "golden", "pdf")
    confirm_file(path)
    if get_text_hash(output) == get_text_hash(path.read_bytes()):
        logger.info("test passed: matching text hashes")
    else:
        logger.warning("test failed: text hashes do not match")
        sys.exit(1)


RawPdf = Stage(
    suffix="pdf",
    consumes=None,
    operation=_operation,
    test_golden=_test_golden,
    to_text=None,
)
