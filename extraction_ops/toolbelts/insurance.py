import re

from core.sectors import (
    IA08_FIRMS,
    INSURANCE_INTERMEDIARY,
    INSURANCE_MANAGER,
    INSURERS,
    LIFE_CO,
)
from extraction_ops.models import ChunkSplitters, DefinitionTools, ToolBelt
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    rejoin_page_breaks,
    replace_from_dict,
    replace_section,
    split_on_bracketed_num,
    starts_with,
    strip_footnote_markers,
)

_REPLACEMENT_DICT = {
    # footnote marker and a stray "]" left in the heading
    "## _Capital requirements_ _**[22]** ]_": "## _Capital requirements_",
    "## _Winding up of insurer_ _**[243]** ]_": "## _Winding up of insurer_",
    # chapter subtitles that lost their "##"
    "## CHAPTER II \n\n_General requirements that apply to all authorised insurers_": "## CHAPTER II \n\n## _General requirements that apply to all authorised insurers_",
    "## CHAPTER III \n\n_Requirements that apply to all insurers carrying on long-term business_": "## CHAPTER III \n\n## _Requirements that apply to all insurers carrying on long-term business_",
    "## CHAPTER I \n\n_The powers of the Authority_ _**[122]**_": "## CHAPTER I \n\n## _The powers of the Authority_",
    # section heading that became a list item
    "- **8 Authorisation**": "## **8 Authorisation**",
    # definitions that became headings
    '## " **annual accounts** " means': '- " **annual accounts** " means',
    '## " **prescribed** " means': '- " **prescribed** " means',
    # repealed definitions with no body
    '## " **Insurance Tribunal** " [Repealed] **[211]** \n\n': "",
    '- " **long-term business fund** " [Repealed] **[212]** \n\n': "",
    '## " **Retirement Benefits Schemes Tribunal** " [Repealed] **[217]** \n\n': "",
    '- " **Supervisor** " [Repealed] **[218]** ': "",
}

# provenance citations on their own line: "[1986/24/3(1) and (3)]", "- [1986/24/12]",
# "## [1996/4/1(1)]", "1986/24/9(1) and (2)"
_CITATION_LINE = re.compile(r"^(?:## |- )?\[?\d{4}/\d+/[^\n]*$\n?", re.MULTILINE)
# "## **SCHEDULE 2** / ## **TRANSFER OF LONG-TERM BUSINESS**" (not the empty Schedule 1)
_SCHEDULE_TITLE = re.compile(
    r"^## \*\*((?:SCHEDULE|Schedule) \d+)\*\* *\n\s*\n## \*\*(?!SCHEDULE|Schedule)(.+?)\*\* *$",
    re.MULTILINE,
)
# "## **9** / ## **Alteration of conditions of existing authorisations**"
_NUMBER_ONLY_HEADING = re.compile(
    r"^## \*\*(\d+[A-Z]*)\*\* *\n\s*\n## \*\*", re.MULTILINE
)


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    text = strip_footnote_markers(text)
    # Schedules 8 and 9 are amendments and repeals of other enactments
    text = replace_section(text, "## **Schedule 8", "## **Schedule 10")
    text = _CITATION_LINE.sub("", text)
    text = _NUMBER_ONLY_HEADING.sub(r"## **\1 ", text)
    text = _SCHEDULE_TITLE.sub(r"## **\1 - \2**", text)
    text = rejoin_page_breaks(text)
    return text


_Trimmer = build_simple_markers(
    "## **PART 1 - REGULATORY OBJECTIVES",
    "2. This Schedule is without prejudice to the operation of section 16",
)

_DefMarkers = build_simple_markers(
    '- " **actuary to the insurer', '- " **subsidiary** " has the meaning'
)

_DefTools = DefinitionTools(
    section_markers=[_DefMarkers],
    is_definition_line=starts_with(['- " **']),
)


# Schedule paragraphs are numbered "13. Provision ..." rather than "(1)"
def _split_on_letter_or_numbered_dot(text: str) -> list[str]:
    return re.split(r"\n(?=[ \t]*(?:- )?(?:\([a-z]+\)|\d+\.\s))", text)


_Splitters = ChunkSplitters(
    primary=split_on_bracketed_num, fallback=_split_on_letter_or_numbered_dot
)

# the most specific heading wins: a section takes its chapter's sectors over its part's
_SECTOR_MATCHERS = {
    "Insurance Managers": (INSURANCE_MANAGER,),
    "Insurance Intermediaries": (INSURANCE_INTERMEDIARY,),
    "Requirements that apply to all insurers carrying on long-term business": (
        LIFE_CO,
    ),
    "Continuation of long-term business of insurers in liquidation": (LIFE_CO,),
    "Insurers only": INSURERS,
    "Insurance managers and insurance intermediaries only": (
        INSURANCE_MANAGER,
        INSURANCE_INTERMEDIARY,
    ),
    "PART 3 - AUTHORISATION OF INSURERS": INSURERS,
    "PART 4 - REQUIREMENTS FOR AUTHORISED INSURERS": INSURERS,
    "PART 4A - GROUP SUPERVISION": INSURERS,
    "PART 5 - FOREIGN INSURERS": INSURERS,
    "PART 6 - INSURANCE MANAGERS AND INSURANCE INTERMEDIARIES": (
        INSURANCE_MANAGER,
        INSURANCE_INTERMEDIARY,
    ),
    "PART 6A - REQUIREMENTS FOR REGISTERED INSURANCE MANAGERS": (
        INSURANCE_MANAGER,
        INSURANCE_INTERMEDIARY,
    ),
    "SCHEDULE 2 - TRANSFER OF LONG-TERM BUSINESS": (LIFE_CO,),
    "SCHEDULE 3 - INSOLVENCY AND WINDING UP": INSURERS,
    "SCHEDULE 4 - CONTINUATION AND DISCONTINUATION OF INSURANCE COMPANIES": INSURERS,
}


def _sectors(headers: tuple[str, ...]) -> tuple[str, ...]:
    for header in reversed(headers):
        for pattern, sectors in _SECTOR_MATCHERS.items():
            if pattern in header:
                return sectors
    return IA08_FIRMS


Insurance = ToolBelt(
    document="Insurance Act 2008",
    hierarchy="primary legislation",
    sectors=_sectors,
    input_url="https://www.iomfsa.im/media/2383/insuranceact2008.pdf",
    pdf_path=build_pdf_path("insurance"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[
        starts_with(["## **PART", "## **SCHEDULE", "## **Schedule"]),
        starts_with(["## CHAPTER"]),
        starts_with(["## _"]),
        lambda line: line.startswith("## **") and line[5:6].isdigit(),
    ],
    definition_tools=_DefTools,
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
