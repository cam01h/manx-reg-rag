from app.models import Citation, UiCitation
from db_ops.models import Payload


def _build_ui_citations(citation: Citation, chunk: Payload) -> UiCitation:
    return UiCitation(
        document=chunk.document,
        headers=chunk.headers,
        url=chunk.url,
        relevance=citation.relevance,
    )


def resolve_citations(
    citations: list[Citation], served: dict[str, Payload]
) -> list[UiCitation]:
    citations_for_ui = []
    for id, chunk in served.items():
        for c in citations:
            if c.ref == id:
                citations_for_ui.append(_build_ui_citations(c, chunk))
    return citations_for_ui
