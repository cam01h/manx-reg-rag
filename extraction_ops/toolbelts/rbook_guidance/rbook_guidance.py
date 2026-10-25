import re

from extraction_ops.models import ChunkSplitters, ToolBelt
from extraction_ops.toolbelts.rule_book.rule_book_sectors import (
    RB_ALL,
    RULE_BOOK_SECTORS,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    replace_from_dict,
    split_on_new_sentence,
    starts_with,
)

from .rbook_guidance_flattener import (
    flatten_guidance_tables,
    promote_unboxed_rules,
    strip_page_furniture,
)
from .rbook_guidance_handler import rbook_guidance_unbox_one_row_tables

_FOOTNOTE_1 = "It is the Authority's expectation that guidance is followed unless alternative processes are adequate."

_REPLACEMENT_DICT = {
    # title footnote moved under the title, it frames the whole document
    "# **Financial Services Act 2008 - Guidance on the Financial Services Rule Book 2016 [1]**": f"## **Financial Services Act 2008 - Guidance on the Financial Services Rule Book 2016**\n\n{_FOOTNOTE_1}",
    f"1 {_FOOTNOTE_1}": "",
    # glued words, mostly where a hyperlink starts or ends
    "extendedGuidance": "extended Guidance",
    "isinfo@iomfsa.im": "is info@iomfsa.im",
    "websitewww.ifrs.org": "website www.ifrs.org",
    "Additionally,1931": "Additionally, 1931",
    "ofCompanies Act": "of Companies Act",
    "foundhere.": "found here.",
    "theGuidance": "the Guidance",
    "documentGuidance": "document Guidance",
    "SeeClass 8": "See Class 8",
    "andClass 8": "and Class 8",
    "theFinancial Services": "the Financial Services",
    "licenceholdershere.": "licenceholders here.",
    "Authority'sRisk-Based": "Authority's Risk-Based",
    "SeeGuidance": "See Guidance",
    "SeeFinancial Advisers": "See Financial Advisers",
    "alsoFinancial Advisers": "also Financial Advisers",
    "theCollective Investment": "the Collective Investment",
    "andGovernance of": "and Governance of",
    "theCompliance Support": "the Compliance Support",
    "theReturns/Forms": "the Returns/Forms",
    "onOTC": "on OTC",
    "theConsent and": "the Consent and",
    "furtherGuidance": "further Guidance",
    "theFitness &": "the Fitness &",
    "banks andfor non-bank": "banks and for non-bank",
    "alsoGuidance": "also Guidance",
    "theTraining and": "the Training and",
    "theattached chart": "the attached chart",
    "alsoWhistleblowing": "also Whistleblowing",
    "Questions andA Brief": "Questions and A Brief",
    "documentfor banks": "document for banks",
    "TheUK Government": "The UK Government",
    "abriefing document": "a briefing document",
    "aTemplate Breaches": "a Template Breaches",
    "theRule Book": "the Rule Book",
    "Authority'sProcedural": "Authority's Procedural",
    "SeeThe guidance": "See The guidance",
    "aProforma": "a Proforma",
    "toexternal": "to external",
    # line-end hyphens and inline bold that pymupdf4llm runs into the next word
    "limit- no more": "limit - no more",
    "safe- keeping": "safekeeping",
    "sub- paragraph": "sub-paragraph",
    "post- merger": "post-merger",
    "an**_ongoing_** **_requirement_**": "an ongoing requirement",
    ";**and**": "; and",
    "is**not**": "is not",
    # last bullet runs into the next sentence
    "- Lending reporting form Guidance for": "- Lending reporting form\n\nGuidance for",
    # superscripts in 3.12
    "30 [th] January": "30th January",
    "1 [st] February": "1st February",
}


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = strip_page_furniture(text)
    text = promote_unboxed_rules(text)
    text = flatten_guidance_tables(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    return text


_Trimmer = build_simple_markers(
    "## **Financial Services Act 2008", "See extended Guidance - Rules 7.17 and 9.27"
)

# blank line, unless the next line is a list item: keeps "...expects to be notified of:"
# with the bullets that follow it
_PARAGRAPH_NOT_LIST = re.compile(r"\n[ \t]*\n(?![ \t]*(?:- |\d+\. ))")


def _split_on_paragraph_not_list(text: str) -> list[str]:
    return _PARAGRAPH_NOT_LIST.split(text)


_Splitters = ChunkSplitters(
    primary=_split_on_paragraph_not_list, fallback=split_on_new_sentence
)

_RULE_HEADER = re.compile(r"^## \*\*\d\.\d")


def _is_rule(line: str) -> bool:
    return bool(_RULE_HEADER.match(line))


# a row can cover several rules: "2.12 Accounting records ... and 2.15 Accounting records ..."
_RULE_NO = re.compile(r"\b\d\.\d{1,2}[A-Z]?\b")


def _rule_sectors(headers: tuple[str, ...]) -> tuple[str, ...]:
    sectors: set[str] = set()
    for rule in _RULE_NO.findall(headers[1]):
        sectors.update(RULE_BOOK_SECTORS.get(rule, RB_ALL))
    if not sectors:
        return RB_ALL
    return tuple(sorted(sectors))


RbookGuidance = ToolBelt(
    document="Guidance on the Financial Services Rule Book 2016",
    hierarchy="guidance",
    sectors=_rule_sectors,
    input_url="https://www.iomfsa.im/media/1519/rulebook2016guidance.pdf",
    pdf_path=build_pdf_path("rbook_guidance"),
    use_ocr=False,
    use_layout=False,
    pdf_handlers=[rbook_guidance_unbox_one_row_tables],
    trimmer=_Trimmer,
    header_matchers=[
        starts_with(["## **Financial Services Act 2008", "## **PART"]),
        _is_rule,
    ],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
