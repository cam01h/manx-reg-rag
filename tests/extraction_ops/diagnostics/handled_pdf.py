import logging
import shutil
import tempfile
from pathlib import Path

from extraction_ops import TOOLBELT_REGISTRY

from .models import Stage
from .utils import build_path, make_pdf_golden_test

logger = logging.getLogger(__name__)

_STAGE = "handled_pdf"


def _operation(doc: str, input: Path) -> bytes:
    tools = TOOLBELT_REGISTRY[doc]
    if not tools.pdf_handlers:
        return input.read_bytes()
    num_handlers = len(tools.pdf_handlers)
    with tempfile.TemporaryDirectory() as tmp:
        working = Path(tmp) / input.name
        shutil.copy2(input, working)
        for i, handler in enumerate(tools.pdf_handlers, start=1):
            handler(working)
            if i < num_handlers:
                snapshot = build_path(_STAGE, doc, f"debug{i}", "pdf")
                snapshot.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(working, snapshot)
        return working.read_bytes()


HandledPdf = Stage(
    suffix="pdf",
    consumes="raw_pdf",
    operation=_operation,
    test_golden=make_pdf_golden_test(_STAGE),
    to_text=None,
)
