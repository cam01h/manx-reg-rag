import logging
from collections import Counter

from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.chunking import pack_chunk
from extraction_ops.models import Chunk, CleanSection
from tests.extraction_ops.diagnostics.models import Stage
from tests.extraction_ops.diagnostics.utils import make_object_golden_test

logger = logging.getLogger(__name__)

_STAGE = "chunks"


def _opperation(doc: str, input: list[CleanSection]) -> list[Chunk]:
    tools = TOOLBELT_REGISTRY[doc]
    chunks = [pack_chunk(tools, section) for section in input]
    tagged = Counter(chunk.sectors for chunk in chunks)
    for sectors, count in tagged.most_common():
        logger.info("[%d] chunks tagged %s", count, sectors)
    return chunks


def _to_text(chunks: list[Chunk]) -> str:
    md = []
    for i, chunk in enumerate(chunks):
        md.append(f"## Chunk {i + 1} ({len(chunk.body)} chars)")
        md.append(f"Headers: {' | '.join(h for h in chunk.headers if h)}")
        md.append(f"Sectors: {', '.join(chunk.sectors)}")
        md.append("")
        md.extend(chunk.body.splitlines())
        md.extend(["", "---", ""])
    return "\n".join(md)


Chunks = Stage(
    suffix="md",
    consumes="norm_sections",
    operation=_opperation,
    test_golden=make_object_golden_test(_STAGE, Chunk),
    to_text=_to_text,
    model=Chunk,
)
