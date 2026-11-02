import logging
import re

from app.models import Citation, UiCitation
from config import FALLBACK_URL
from db_ops.models import Payload

logger = logging.getLogger(__name__)

REF_PATTERN = re.compile(r"\bC\d{3,}\b")


def _build_ui_citation(citation: Citation, chunk: Payload) -> UiCitation:
    return UiCitation(
        document=chunk.document,
        headers=[h for h in chunk.headers if h],
        url=chunk.url or FALLBACK_URL,
        relevance=citation.relevance,
    )


def resolve_citations(
    citations: list[Citation], served: dict[str, Payload]
) -> list[UiCitation]:
    """Swap the agent's {ref, relevance} citations for the details the browser
    needs. Keeps the agent's order, drops repeats quietly and drops (and logs)
    any ref that was never served in this run."""
    resolved: list[UiCitation] = []
    done: set[str] = set()
    for c in citations:
        # "c001 " is clearly C001, so don't lose the citation over formatting
        ref = c.ref.strip().upper()
        if ref in done:
            continue
        done.add(ref)
        chunk = served.get(ref)
        if chunk is None:
            logger.warning("dropped citation with unknown ref [%s]", c.ref)
            continue
        resolved.append(_build_ui_citation(c, chunk))
    return resolved


def refs_in_text(text: str, served: dict[str, Payload]) -> list[str]:
    """Refs served in this run that also appear in the answer text. The prompt
    says never to write them there, so any hit is worth a log line."""
    return sorted({m for m in REF_PATTERN.findall(text) if m in served})
