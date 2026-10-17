import logging
from collections.abc import Callable

from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.chunking import segment_by_headers
from extraction_ops.models import Section
from tests.extraction_ops.diagnostics.models import Stage
from tests.extraction_ops.diagnostics.utils import (
    make_md_golden_test,
    make_object_golden_test,
)

logger = logging.getLogger(__name__)

_SEC_STAGE = "raw_sections"
_HEAD_STAGE = "headers"


def _opperation(doc: str, input: str) -> list[Section]:
    matchers = TOOLBELT_REGISTRY[doc].header_matchers
    chunk_lines = input.split("\n")
    sections = segment_by_headers(chunk_lines, matchers)
    if len(sections) > 1:
        logger.info(
            "[%d] sections found in [%s], each with [%d] levels",
            len(sections),
            doc,
            len(sections[0].headers),
        )
    elif sections:
        logger.warning(
            "single section found in [%s]: [%s]", doc, str(sections[0].headers)
        )
    else:
        logger.warning("no sections found in [%s]", doc)
    return sections


def _to_text_builder(stage: str) -> Callable[[list[Section]], str]:
    def to_text(sections: list[Section]) -> str:
        md = []
        for seg in sections:
            if stage == _SEC_STAGE:
                md.extend(f"Header [{i + 1}]: {h}" for i, h in enumerate(seg.headers))
                md.extend(seg.body_lines)
                md.extend(["", "---", ""])
            elif stage == _HEAD_STAGE:
                md.append(" | ".join(h for h in seg.headers))
            else:
                logger.error("incorrect stage string")
                raise ValueError("incorrect stage string")
        return "\n".join(md)

    return to_text


Sections = Stage(
    suffix="md",
    consumes="chunk_lines",
    operation=_opperation,
    test_golden=make_object_golden_test(_SEC_STAGE, Section),
    to_text=_to_text_builder(_SEC_STAGE),
    model=Section,
)


Headers = Stage(
    suffix="md",
    consumes="chunk_lines",
    operation=_opperation,
    test_golden=make_md_golden_test(_HEAD_STAGE, _to_text_builder(_HEAD_STAGE)),
    to_text=_to_text_builder(_HEAD_STAGE),
)
