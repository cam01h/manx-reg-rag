import logging

from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.definitions import extract_to_definitions
from extraction_ops.models import Definition
from tests.extraction_ops.diagnostics.models import Stage
from tests.extraction_ops.diagnostics.utils import make_object_golden_test

logger = logging.getLogger(__name__)

_STAGE = "definitions"


def _opperation(doc: str, input: str) -> list[Definition]:
    tools = TOOLBELT_REGISTRY[doc]
    return extract_to_definitions(tools, input.split("\n"))


def _to_text(output: list[Definition]) -> str:
    md = []
    for i, d in enumerate(output):
        md.append(f'## Term {i + 1}: "{d.term}"')
        md.extend([d.definition, "", "---", ""])
    return "\n".join(md)


Definitions = Stage(
    suffix="md",
    consumes="def_lines",
    operation=_opperation,
    test_golden=make_object_golden_test(_STAGE, Definition),
    to_text=_to_text,
    model=Definition,
)
