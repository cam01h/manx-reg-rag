from config import PROJECT_ROOT
from extraction_ops.models import (
    ChunkSplitters,
    DefinitionTools,
    SectionMarkers,
    ToolBelt,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_body_cleaner,
    base_double_def_line,
    base_false_double_def,
    base_header_cleaner,
    base_text_cleaner,
    in_line,
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


def terror_financial_restrictions_text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = strip_footnote_markers(text)
    text = strip_footnote_bullets(text)
    text = replace_section(
        text, "## **71 Amendment to the Bail Act 1952", "## **SCHEDULE 1A"
    )
    text = replace_from_dict(text, FINANCIAL_RESTRICTIONS_REPLACEMENT_DICT)
    return text


FinancialRestrictionsTrimmer = SectionMarkers(
    start=starts_with(["## **PART 1 -"]),
    end=starts_with(["- (3) This paragraph does not apply if"]),
)

FinancialRestrictionsDefMarkersSec3 = SectionMarkers(
    start=starts_with(['- " **action** "']),
    end=starts_with(["- (b) any tangible property (other"]),
)

FinancialRestrictionsDefMarkersSchedule1A = SectionMarkers(
    start=starts_with(['"Arrangement" includes']),
    end=starts_with(["- (b) any convention, custom"]),
)

FinancialRestrictionsDefMarkersSchedule1 = SectionMarkers(
    start=starts_with(['- " **business relationship']),
    end=in_line(["- (iii) proliferation or"]),
)

FinancialRestrictionsDefTools = DefinitionTools(
    section_markers=[
        FinancialRestrictionsDefMarkersSec3,
        FinancialRestrictionsDefMarkersSchedule1A,
        FinancialRestrictionsDefMarkersSchedule1,
    ],
    is_definition_line=starts_with(['- " **', '- (1) In this Act " **', '- "', '"']),
    is_double_def_line=base_double_def_line,
    is_false_dub_def=base_false_double_def,
)

FinancialRestrictionsSplitters = ChunkSplitters(
    primary=split_on_bracketed_amended_num, fallback=split_on_paragraph
)

FinancialRestrictions = ToolBelt(
    document="Terrorism And Other Crime (Financial Restrictions) Act 2014",
    hierarchy="primary legislation",
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/PRINCIPAL/2014/2014-0013/2014-0013_13.pdf",
    pdf_path=PROJECT_ROOT / "data/raw/custom/terror_financial_restrictions.pdf",
    use_ocr=True,
    pdf_handlers=None,
    trimmer=FinancialRestrictionsTrimmer,
    header_matchers=[
        starts_with(["## **PART", "## **SCHEDULE"]),
        starts_with(["## DIVISION"]),
        starts_with(["## SUB-DIVISION"]),
        lambda line: line.startswith("## **") and line[5].isdigit(),
    ],
    definition_tools=FinancialRestrictionsDefTools,
    clean_text=terror_financial_restrictions_text_cleaner,
    re_pack_splitters=FinancialRestrictionsSplitters,
    clean_body=base_body_cleaner,
    clean_header=base_header_cleaner,
    min_body_len=40,
)
