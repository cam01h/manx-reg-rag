import logging

from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.md_ops import clean_md_to_lines
from tests.extraction_ops.diagnostics.models import Stage
from tests.extraction_ops.diagnostics.utils import (
    make_md_golden_test,
)

logger = logging.getLogger(__name__)

_STAGE = "clean_md"


def _operation(doc: str, input: str) -> str:
    tools = TOOLBELT_REGISTRY[doc]
    clean_md = clean_md_to_lines(tools.clean_text, input)
    logger.info("cleaner applied to [%s]", doc)
    return "\n".join(clean_md)


CleanMd = Stage(
    suffix="md",
    consumes="raw_md",
    operation=_operation,
    test_golden=make_md_golden_test(_STAGE),
    to_text=None,
)
