import logging

from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.chunking import normalise_sections
from extraction_ops.models import CleanSection, Section
from tests.extraction_ops.diagnostics.models import Stage
from tests.extraction_ops.diagnostics.utils import make_object_golden_test

logger = logging.getLogger(__name__)

_STAGE = "norm_sections"


def _opperation(doc: str, input: list[Section]) -> list[CleanSection]:
    tools = TOOLBELT_REGISTRY[doc]
    return normalise_sections(tools, input)


def _to_text(norm_sections: list[CleanSection]) -> str:
    md_lines = []
    for s in norm_sections:
        headers = [
            f"{'#' * min(i + 1, 6)} Header Level {i + 1}: {h}"
            for i, h in enumerate(s.headers)
            if h
        ]
        md_lines.extend(headers)
        body = s.body.splitlines()
        md_lines.extend(body)
        md_lines.extend(["", "---", ""])
    return "\n".join(md_lines)


NormSections = Stage(
    suffix="md",
    consumes="raw_sections",
    operation=_opperation,
    test_golden=make_object_golden_test(_STAGE, CleanSection),
    to_text=_to_text,
    model=CleanSection,
)
