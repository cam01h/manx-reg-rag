import logging

from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.definitions import segment_by_definitions
from tests.extraction_ops.diagnostics.models import Stage
from tests.extraction_ops.diagnostics.utils import make_md_golden_test

logger = logging.getLogger(__name__)

_STAGE = "def_segs"


def _opperation(doc: str, input: str) -> list[list[str]]:
    tools = TOOLBELT_REGISTRY[doc].definition_tools
    if tools is None:
        logger.warning("[%s] has no definition tools", doc)
        return [[""]]
    else:
        return segment_by_definitions(input.splitlines(), tools.is_definition_line)


def _to_text(sections: list[list[str]]) -> str:
    readable_sections = []
    for i, s in enumerate(sections):
        readable_sections.append(f"## Term {i + 1}: {s[0]}\n")
        readable_sections.extend(s[1:])
        readable_sections.extend(["", "---", ""])
    return "\n".join(readable_sections)


DefSegs = Stage(
    suffix="md",
    consumes="def_lines",
    operation=_opperation,
    test_golden=make_md_golden_test(_STAGE, _to_text),
    to_text=_to_text,
    model=list[str],
)
