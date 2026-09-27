import logging

from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.md_ops import check_for_scope_end, check_for_scope_start
from tests.extraction_ops.diagnostics.models import Stage
from tests.extraction_ops.diagnostics.utils import make_md_golden_test

logger = logging.getLogger(__name__)

_STAGE = "trimmed_md"


def _operation(doc: str, input: str) -> str:
    trimmer = TOOLBELT_REGISTRY[doc].trimmer
    kept_lines = []
    in_scope = False
    for line in input.splitlines():
        if check_for_scope_start(doc, trimmer.start, in_scope, line):
            logger.info("start line detected in [%s]", doc)
            logger.info("[%s]", line)
            in_scope = True
        if in_scope:
            kept_lines.append(line)
        if check_for_scope_end(trimmer.end, line):
            logger.info("end line detected in [%s]", doc)
            logger.info("[%s]", line)
            break
    else:
        logger.critical("no end line found in [%s]", doc)
    if not in_scope:
        logger.critical("no start line found in [%s]", doc)
        raise ValueError(f"no start line found in [{doc}]")
    return "\n".join(kept_lines)


TrimmedMd = Stage(
    suffix="md",
    consumes="clean_md",
    operation=_operation,
    test_golden=make_md_golden_test(_STAGE),
    to_text=None,
)
