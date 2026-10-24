from core.sectors import ALL_SECTORS
from extraction_ops.models import (
    ChunkSplitters,
    DefinitionTools,
    ToolBelt,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    replace_from_dict,
    replace_section,
    split_on_bracketed_amended_num,
    split_on_paragraph,
    starts_with,
    strip_footnote_bullets,
    strip_footnote_markers,
)

FINANCIAL_RESTRICTIONS_REPLACEMENT_DICT = {
    # header miniplulation
    "## **3** \n\n## **Interpretation**": "## **3 Interpretation**",
    "## **2** \n\n## **Commencement**": "## **2 Commencement**",
    "\nDIVISION": "\n## DIVISION",
    "\nSUB-DIVISION": "\n## SUB-DIVISION",
    "## **SCHEDULE 1A** \n\n[Section 5A(3)] \n\n## **RULES FOR INTERPRETATION": "## **SCHEDULE 1A - RULES FOR INTERPRETATION",
    "## **2** \n\n## **Joint": "## **2 Joint",
    "## **3** \n\n## **Joint": "## **3 Joint",
    "## **4** \n\n## **Calculating": "## **4 Calculating",
    "## **SCHEDULE 1** \n\n[Section 8] \n\n## **REQUIREMENTS OF": "## **SCHEDULE 1 - REQUIREMENTS OF",
    "## **6** \n\n## **Limiting": "## **6 Limiting",
    "## **SCHEDULE 2** \n\n[Section 13(7)] \n\n## **REQUIREMENTS": "## **SCHEDULE 2 - REQUIREMENTS",
    # definition miniplulation
    '\n## " **interim designation** " [Repealed] \n': "",
    '## " **relevant ': '- " **relevant ',
    "\nTynwald procedure - affirmative. \n\n- (3) [Repealed] \n": "",
    '\n- " **final designation** " [Repealed] \n': "",
    '\n## **4 Meaning of "financial services"** \n': "",
    '## **5 Meaning of "resident"** \n': '- " **resident** "\n',
    '## **5A Meaning of "owned or controlled directly or indirectly": persons** ': '- "owned or controlled directly or indirectly"',
    '## **5B Meaning of "owned, held or controlled": funds or economic resources**': '- " **owned, held or controlled** "',
    '\n- " **financial services** " has the meaning given by section 4; \n': "",
    # artifacts from pdf
    "\nTynwald procedure - negative. \n": "",
}


def _clean_text(text: str) -> str:
    text = base_text_cleaner(text)
    text = strip_footnote_markers(text)
    text = strip_footnote_bullets(text)
    text = replace_section(
        text, "## **71 Amendment to the Bail Act 1952", "## **SCHEDULE 1A"
    )
    text = replace_from_dict(text, FINANCIAL_RESTRICTIONS_REPLACEMENT_DICT)
    return text


_Trimmer = build_simple_markers(
    "## **PART 1 -", "- (3) This paragraph does not apply if"
)

_DefMarkersSec3 = build_simple_markers(
    '- " **action** "', "- (b) any tangible property (other"
)

_DefMarkersSchedule1A = build_simple_markers(
    '"Arrangement" includes', "- (b) any convention, custom"
)

_DefMarkersSchedule1 = build_simple_markers(
    '- " **business relationship', "- (iii) proliferation or"
)

_DefTools = DefinitionTools(
    section_markers=[
        _DefMarkersSec3,
        _DefMarkersSchedule1A,
        _DefMarkersSchedule1,
    ],
    is_definition_line=starts_with(['- " **', '- (1) In this Act " **', '- "', '"']),
)

_Splitters = ChunkSplitters(
    primary=split_on_bracketed_amended_num, fallback=split_on_paragraph
)

FinancialRestrictions = ToolBelt(
    document="Terrorism And Other Crime (Financial Restrictions) Act 2014",
    hierarchy="primary legislation",
    sectors=fixed_sectors(ALL_SECTORS),
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/PRINCIPAL/2014/2014-0013/2014-0013_13.pdf",
    pdf_path=build_pdf_path("terrorfr"),
    trimmer=_Trimmer,
    header_matchers=[
        starts_with(["## **PART", "## **SCHEDULE"]),
        starts_with(["## DIVISION"]),
        starts_with(["## SUB-DIVISION"]),
        lambda line: line.startswith("## **") and line[5].isdigit(),
    ],
    definition_tools=_DefTools,
    clean_text=_clean_text,
    re_pack_splitters=_Splitters,
)
