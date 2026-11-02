import logging

import pytest

from app.citations import refs_in_text, resolve_citations
from app.models import Citation
from config import FALLBACK_URL
from db_ops.models import Payload


def make_chunk(
    document: str = "The AML/CFT Code 2019",
    headers: list[str] | None = None,
    url: str = "https://example.im/code.pdf",
) -> Payload:
    return Payload(
        chunk_id=f"{document} - hash",
        document=document,
        hierarchy="Secondary legislation",
        sectors=("class_1",),
        headers=["PART 4", "14 Enhanced customer due diligence"]
        if headers is None
        else headers,
        body="body",
        url=url,
        score=1.0,
    )


@pytest.fixture
def served() -> dict[str, Payload]:
    return {
        "C001": make_chunk(),
        "C002": make_chunk(
            document="The AML/CFT Handbook", url="https://example.im/handbook.pdf"
        ),
        "C003": make_chunk(
            document="The Proceeds of Crime Act 2008", url="https://example.im/poca.pdf"
        ),
    }


def test_known_ref_resolves_to_the_right_chunk(served):
    [ui] = resolve_citations([Citation(ref="C002", relevance="why")], served)
    assert ui.document == "The AML/CFT Handbook"
    assert ui.url == "https://example.im/handbook.pdf"
    assert ui.headers == ["PART 4", "14 Enhanced customer due diligence"]
    assert ui.relevance == "why"


def test_keeps_the_agents_order_not_the_serving_order(served):
    cited = [Citation(ref="C003", relevance="a"), Citation(ref="C001", relevance="b")]
    result = resolve_citations(cited, served)
    assert [c.document for c in result] == [
        "The Proceeds of Crime Act 2008",
        "The AML/CFT Code 2019",
    ]


def test_unknown_ref_is_dropped_and_logged(served, caplog):
    cited = [Citation(ref="C001", relevance="a"), Citation(ref="C099", relevance="b")]
    with caplog.at_level(logging.WARNING, logger="app.citations"):
        result = resolve_citations(cited, served)
    assert len(result) == 1
    assert "C099" in caplog.text


def test_a_title_instead_of_a_ref_is_dropped(served, caplog):
    cited = [Citation(ref="The AML/CFT Code 2019, PART 4", relevance="a")]
    with caplog.at_level(logging.WARNING, logger="app.citations"):
        assert resolve_citations(cited, served) == []
    assert "dropped citation" in caplog.text


def test_same_ref_cited_twice_shows_once(served):
    cited = [
        Citation(ref="C001", relevance="first"),
        Citation(ref="C001", relevance="second"),
    ]
    [ui] = resolve_citations(cited, served)
    assert ui.relevance == "first"


def test_ref_formatting_slips_still_resolve(served):
    cited = [Citation(ref=" c001 ", relevance="a")]
    [ui] = resolve_citations(cited, served)
    assert ui.document == "The AML/CFT Code 2019"


def test_no_citations_is_fine(served):
    assert resolve_citations([], served) == []


def test_empty_url_falls_back(served):
    served["C001"] = make_chunk(url="")
    [ui] = resolve_citations([Citation(ref="C001", relevance="a")], served)
    assert ui.url == FALLBACK_URL


def test_empty_headers_are_filtered_out(served):
    served["C001"] = make_chunk(headers=["PART 4", "", "14 Enhanced"])
    [ui] = resolve_citations([Citation(ref="C001", relevance="a")], served)
    assert ui.headers == ["PART 4", "14 Enhanced"]


def test_refs_in_text_only_reports_served_refs(served):
    text = "See C001 and also [C003]. Form C777 is something else."
    assert refs_in_text(text, served) == ["C001", "C003"]


def test_refs_in_text_clean_answer(served):
    assert refs_in_text("Nothing to see here.", served) == []
