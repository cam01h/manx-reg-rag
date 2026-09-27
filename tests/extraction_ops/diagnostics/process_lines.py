import logging
from collections.abc import Callable

from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.md_ops import process_lines
from extraction_ops.models import CleanOutPut

from .models import Stage
from .utils import (
    make_md_golden_test,
)

logger = logging.getLogger(__name__)

_CHUNK_STAGE = "chunk_lines"
_DEFINITION_STAGE = "definition_lines"


def _operation_builder(
    select: Callable[[CleanOutPut], list[str]],
) -> Callable[[str, str], str]:
    def func(doc: str, input: str) -> str:
        tools = TOOLBELT_REGISTRY[doc]
        output = process_lines(input.splitlines(), tools)
        return "\n".join(select(output))

    return func


ChunkLines = Stage(
    suffix="md",
    consumes="trimmed",
    operation=_operation_builder(lambda output: output.chunk_lines),
    test_golden=make_md_golden_test(_CHUNK_STAGE),
    to_text=None,
)

DefLines = Stage(
    suffix="md",
    consumes="trimmed",
    operation=_operation_builder(lambda output: output.definition_lines),
    test_golden=make_md_golden_test(_DEFINITION_STAGE),
    to_text=None,
)
