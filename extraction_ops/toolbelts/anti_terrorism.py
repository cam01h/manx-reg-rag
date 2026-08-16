import re
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
    redact_md_tables,
    rejoin_page_breaks,
    replace_from_dict,
    replace_section,
    starts_with,
    strip_footnote_bullets,
    strip_footnote_markers,
    strip_square_bracket_legislation_ids,
)

SEC72A_TABLE_RAW = (
    "_Offence_ \n"
    "\n"
    "## _Items liable to forfeiture_ \n"
    "\n"
    "Section 42 (weapons training) Anything that the court considers to have been in the possession of the person for purposes connected with the offence. Section 45 (possession for Any article that is the subject matter of the terrorist purposes) offence. Section 46 (collection of Any document or record containing information) information of the kind mentioned in subsection (1)(a) of that section. Section 46A (eliciting, Any document or record containing publishing or communicating information of the kind mentioned in information about members of subsection (1)(a) of that section. armed forces etc)"
)

SEC72A_TABLE_NORMALISED = (
    "[The following is a two-column table: offence provision, and items liable to forfeiture]\n"
    "\n"
    "Section 42 (weapons training) - Anything that the court considers to have been in the possession of the person for purposes connected with the offence.\n"
    "\n"
    "Section 45 (possession for terrorist purposes) - Any article that is the subject matter of the offence.\n"
    "\n"
    "Section 46 (collection of information) - Any document or record containing information of the kind mentioned in subsection (1)(a) of that section.\n"
    "\n"
    "Section 46A (eliciting, publishing or communicating information about members of armed forces etc) - Any document or record containing information of the kind mentioned in subsection (1)(a) of that section."
)


ANTI_TERROR_REPLACEMENT_DICT = {
    # fixing line breaks
    "_Proceeds_ . \n\n- _of": "_Proceeds of",
    "shall be \n\nliable": "shall be liable",
    "days \n\nbeginning": "days beginning",
    "Security_ \n\n- _Act 1995_": "Security Act 1995_",
    # fixing quotes
    '## " **explosive': '- " **explosive',
    # fixing headers
    "\n_General_ ": "\n## _General_ ",
    "## **OFFENCES WHERE TERRORIST CONNECTION TO BE CONSIDERED**": "## _OFFENCES WHERE TERRORIST CONNECTION TO BE CONSIDERED_",
    "## **TRAVEL RESTRICTION ORDERS**": "## _TRAVEL RESTRICTION ORDERS_",
    "_Introductory_": "",
    "_Power to extend Schedule": "## _Power to extend Schedule",
    "- **1 Terrorism: interpretation**": "## _1 Terrorism: interpretation_",
    "- **8 Use": "## **8 Use",
    "- **10 Money": "## **10 Money",
    "- **74 Security of pathogens and toxins** Schedule": "## **74 Security of pathogens and toxins**\n\nSchedule",
    "INFORMATION OR**\n\n## **EVIDENCE**": "INFORMATION OR EVIDENCE**",
    "_Interpretation_ \n": "## _Interpretation_\n",
    "**PART 1 - PATHOGENS": "## **PART 1 - PATHOGENS",
    "## VIRUSES": "## _VIRUSES_",
    "## RICKETTSIAE": "## _RICKETTSIAE_",
    "## BACTERIA": "## _BACTERIA_",
    "## TOXINS": "## _TOXINS_",
    # artifacts from pdf
    "[P/] ": "",
    "[P/(2) and (3)]": "",
    "[P/(4) and (5)]": "",
    "[P/ and 71]": "",
    "##  \n": "",
    "\nSection 18U \n": "",
    "\n[Section 33(7)] \n": "",
    "Section 16(8)": "",
    "Sections 16A, 18C, 72B and 72C ": "",
    "Section 17 ": "",
    "Section 18 ": "",
    "Section 24 ": "",
    "## Section 25 ": "",
    "Section 28(1) ": "",
    "Section 30(2) and para 4(3) of Sch 7 ": "",
    "## Section 65 ": "",
    "Section 74 ": "",
    "Section 75(1) ": "",
    # table normalisation
    SEC72A_TABLE_RAW: SEC72A_TABLE_NORMALISED,
    # must run last
    "8B** \n\n## **SEARCHES": "8B - SEARCHES",
}


def anti_terror_text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = strip_footnote_markers(text)
    text = strip_footnote_bullets(text)
    text = strip_square_bracket_legislation_ids(text)
    text = rejoin_page_breaks(text)
    text = re.sub(r" *\[(?!Repealed\])[^\]]{20,}\]", "", text)
    text = redact_md_tables(text)
    # joins schedule titles
    text = re.sub(
        r"^## \*\*(SCHEDULE \d+[A-Z]?)\*\* *\n\s*\n## (?:\*\*|_)(?!SCHEDULE \d)(.+?)(?:\*\*|_) *$",
        r"## **\1 - \2**",
        text,
        flags=re.MULTILINE,
    )
    text = replace_section(text, "# **SCHEDULE 9**", "## **SCHEDULE 12")
    text = replace_from_dict(text, ANTI_TERROR_REPLACEMENT_DICT)
    return text


AntiTerrorMarkers = SectionMarkers(
    start=starts_with(["## **PART I - INTRODUCTORY"]),
    end=in_line(["- (c) make supplemental, incidental"]),
)

AntiTerrorSec3Defs1 = SectionMarkers(
    start=starts_with(['- (1) In this Act " **terrorism']),
    end=starts_with(["- (3) The use or threat"]),
)

AntiTerrorSec3Defs2 = SectionMarkers(
    start=starts_with(['- (4) In subsection (2) "proscribed"']),
    end=in_line(["- (i) the Northern Ireland (Emergency"]),
)

AntiTerrorSec6Defs = SectionMarkers(
    start=starts_with(['- (1) In this Act " **terrorist']),
    end=in_line(["- (b) the reference to an organisation's"]),
)

AntiTerrorSec18VDefs = SectionMarkers(
    start=starts_with(['- " **country** "']),
    end=starts_with(['- " **release** "']),
)

AntiTerrorSec19Defs = SectionMarkers(
    start=starts_with(['In this Act " **terrorist investigation']),
    end=starts_with(["- (d) the commission, preparation"]),
)

AntiTerrorSec29Defs = SectionMarkers(
    start=starts_with(['- (1) In this Part, " **terrorist']),
    end=starts_with(["- (2) The reference in"]),
)

AntiTerrorSec43Defs = SectionMarkers(
    start=starts_with(['- "biological weapon" means']),
    end=starts_with(['- "radioactive material"']),
)

AntiTerrorSec75Defs = SectionMarkers(
    start=starts_with(['- " **act** " and']),
    end=starts_with(["   - (b) except in construing"]),
)

AntiTerrorSch2Defs = SectionMarkers(
    start=starts_with(['- " **charging order** "']),
    end=starts_with(['- " **restraint order** "']),
)

AntiTerrorSch4Defs = SectionMarkers(
    start=in_line(['- " **the court** "']),
    end=in_line(["- (2) The Treasury may by order"]),
)

AntiTerrorSch12Defs = SectionMarkers(
    start=in_line(['- " **dangerous substance*']),
    end=in_line(['- " **relevant premises**']),
)

AntiTerrorDefTools = DefinitionTools(
    section_markers=[
        AntiTerrorSec3Defs1,
        AntiTerrorSec3Defs2,
        AntiTerrorSec6Defs,
        AntiTerrorSec18VDefs,
        AntiTerrorSec19Defs,
        AntiTerrorSec29Defs,
        AntiTerrorSec43Defs,
        AntiTerrorSec75Defs,
        AntiTerrorSch2Defs,
        AntiTerrorSch4Defs,
        AntiTerrorSch12Defs,
    ],
    is_definition_line=lambda line: len(line.split('"')) == 3,
    is_double_def_line=base_double_def_line,
    is_false_dub_def=base_false_double_def,
)

AntiTerrorSplitters = ChunkSplitters(
    primary=lambda text: re.split(r"\n+(?=\s*(?:- )?\d+\.\s)", text),
    fallback=lambda text: re.split(r"\n+(?=\s*(?:- )?\(\d+\))", text),
)

AntiTerror = ToolBelt(
    document="ANTI-TERRORISM AND CRIME ACT 2003",
    hierarchy="primary legislation",
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/PRINCIPAL/2003/2003-0006/2003-0006_15.pdf",
    pdf_path=PROJECT_ROOT / "data/raw/custom/anti_terror.pdf",
    use_ocr=True,
    pdf_handlers=None,
    trimmer=AntiTerrorMarkers,
    header_matchers=[
        starts_with(["## **SCHEDULE"]),
        starts_with(["## **PART"]),
        starts_with(["## _"]),
        lambda line: (
            (line.startswith("## **") and line[5:6].isdigit())
            or bool(re.match(r"\s*\d+\.\s*$", line))
        ),
    ],
    definition_tools=AntiTerrorDefTools,
    clean_text=anti_terror_text_cleaner,
    re_pack_splitters=AntiTerrorSplitters,
    clean_body=base_body_cleaner,
    clean_header=base_header_cleaner,
    min_body_len=40,
)
