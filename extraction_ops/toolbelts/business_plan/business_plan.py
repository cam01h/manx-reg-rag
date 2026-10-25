import re

from core.sectors import (
    CLASS_1,
    CLASS_2,
    CLASS_3,
    CLASS_7,
    CLASS_8,
    FSA08_SECTORS,
    INSURERS,
    RAO_CLASSES,
    TCSP,
)
from extraction_ops.models import (
    ChunkSplitters,
    DefinitionTools,
    ToolBelt,
)
from extraction_ops.toolbelts.business_plan.business_plan_table_flatteners import (
    flatten_2p2_table,
    flatten_3p1_table,
    flatten_3p2_table,
    flatten_appendix_1_table,
    flatten_appendix_3_table,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    header_sectors,
    replace_from_dict,
    starts_with,
    strip_footnote_bullets,
    strip_footnote_markers,
)

_CONTROL_MIXED = """**Controlled** any of the functions set out in Appendix 2 of the Authority's Regulatory **Function/Controlled** Guidance - Fitness and Propriety/holder of a controlled function role **Function Role Holder** """
_CONTROL_FIXED = """- "Controlled Function" or "Controlled Function Role Holder" any of the functions set out in Appendix 2 of the Authority's Regulatory Guidance - Fitness and Propriety/holder of a controlled function role"""

_REGISTERD_INSURANCE_MIXED = """**Registered insurance** an insurance manager which is registered under Part 6 of the Insurance Act **manager** 2008 """
_REGISTERED_INSURANCE_FIXED = """- "Registered insurance manager" an insurance manager which is registered under Part 6 of the Insurance Act 2008"""

_REG_INSURANCE = """**Regulated insurance** the insurance activities in respect of which this application is being made **activities** """
_REG_INSURANCE_FIXED = """- "Regulated insurance activities" the insurance activities in respect of which this application is being made"""


_REPLACEMENT_DICT = {
    "**Applicant** a person": '- "Applicant" a person',
    "- **Authority** the Isle": '- "Authority" the Isle',
    "   - **CGC** the Corporate": '- "CGC" the Corporate',
    _CONTROL_MIXED: _CONTROL_FIXED,
    "- **firm(s)** Any person (legal": '- "firm" Any person (legal',
    "**FSA08** Financial Services": '- "FSA08" Financial Services',
    "   - **Fully managed** an applicant that": '- "Fully managed" an applicant that',
    "         - **IA08** Insurance": '- "IA08" Insurance',
    "            - **IT** information": '- "IT" information',
    "   - **Licenceholder** a person": '- "Licenceholder" a person',
    "      - **Long-term** those applicants": '- "Long-term" those applicants',
    "         - **MCR** Minimum Capital": '- "MCR" Minimum Capital',
    "   - **Non long-term** those applicants": '- "Non long-term" those applicants',
    "- **Partially managed** an applicant that outsources": '- "Partially managed" an applicant that outsources',
    "**PCC** Protected Cell": '- "PCC" Protected Cell',
    "**PCC Act** Protected Cell": '- "PCC Act" Protected Cell',
    "**PII** Professional Indemnity": '- "PII" Professional Indemnity',
    _REGISTERD_INSURANCE_MIXED: _REGISTERED_INSURANCE_FIXED,
    _REG_INSURANCE: _REG_INSURANCE_FIXED,
    "**Regulations** Insurance": '- "Regulations" Insurance',
    "**Rule/Rule Book** Financial Services": '- "Rule" or "Rule Book" Financial Services',
    "**SCR** relevant Solvency": '- "SCR" relevant Solvency',
    # fixing headers
    "## It is appreciated that": "It is appreciated that",
    "**(iv) Class 3 (Services to Collective": "## **(iv) Class 3 (Services to Collective",
    "## **(iv) Underwriting Summary** \n\n**IA08 applicants:** ": "## **(iv) Underwriting Summary - IA08 applicants:** ",
    "**(iii) Class 3 (Services to Collective": "## **(iii) Class 3 (Services to Collective",
    "**(viii) Class 8 (Money Transmission": "## **(viii) Class 8 (Money Transmission",
    # tables
    "<br>": " ",
    # missed footnotes
    "\n\n18 If the application is for a cell only, provide details of any proposed changes to the Controlled Function Role Holders and key operational functions of the PCC as a result of the addition of the cell. \n": "",
    "\n21 An original insured includes any person to be insured under a direct policy written by the applicant and any person to be insured under a direct policy which is to be directly or indirectly reinsured by the applicant, as the case may be. \n": "",
    "\n20 Risk management system comprises strategies, processes and reporting procedures necessary to measure, monitor, manage and report reasonably foreseeable, relevant and material risks which the applicant could be exposed to. \n": "",
    "\n16 For Class 3(1), (2), (6) or (7). \n\n17 Rule Book requirement. \n": "",
}

_SECTOR_MATCHERS = {
    "FSA08": FSA08_SECTORS,
    "IA08": INSURERS,
    "Appendix 3": INSURERS,
    "Class 1 (Deposit": (CLASS_1,),
    "Class 2 (Investment": (CLASS_2,),
    "Class 3 (Services": (CLASS_3,),
    "Class 4 and Class 5": TCSP,
    "Class 7 Management": (CLASS_7,),
    "Class 8 (Money": (CLASS_8,),
}


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = strip_footnote_markers(text)
    text = strip_footnote_bullets(text)
    text = re.sub(r" +([.,;:])", r"\1", text)
    text = flatten_2p2_table(text)
    text = flatten_3p1_table(text)
    text = flatten_3p2_table(text)
    text = flatten_appendix_1_table(text)
    text = flatten_appendix_3_table(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    return text


_Trimmer = build_simple_markers(
    '- "Applicant" a person applying for',
    "- Provide copies of the year 1 realistic and pessimistic",
)

_DefMarkers = build_simple_markers(
    '- "Applicant" a person applying for authorisation',
    '- "SCR" relevant Solvency Capital',
)

_DefTools = DefinitionTools(
    section_markers=[_DefMarkers], is_definition_line=starts_with(['- "'])
)

_LIST_START = r"[ \t]*(?:- )?(?:\d+\.\s|\(\w+\)|[a-z]\.\s)"


def split_on_non_list_new_para(text: str) -> list[str]:
    return re.split(rf"\n[ \t]*\n(?!{_LIST_START})", text)


_Splitters = ChunkSplitters(
    primary=split_on_non_list_new_para, fallback=split_on_non_list_new_para
)

_SINGLE_DIGIT_HEADER = re.compile(r"^## \*\*\d+\.\s")
_SUB_HEADER = re.compile(r"^## \*\*(?:\d+\.\d+|\([ivx]+\))\s")


def _is_top_header(line: str) -> bool:
    return bool(_SINGLE_DIGIT_HEADER.match(line)) or line.startswith(
        ("## Appendix", "## **Appendix")
    )


def _is_sub_header(line: str) -> bool:
    return bool(_SUB_HEADER.match(line))


BusinessPlan = ToolBelt(
    document="Business Plan Guidance",
    hierarchy="guidance",
    sectors=header_sectors(_SECTOR_MATCHERS, RAO_CLASSES + INSURERS),
    input_url="https://www.iomfsa.im/media/3511/business-plan-guidance.pdf",
    pdf_path=build_pdf_path("business_plan"),
    trimmer=_Trimmer,
    header_matchers=[
        _is_top_header,
        _is_sub_header,
        starts_with(
            [
                "## **All applicants",
                "## **All FSA08",
                "## **FSA08 applicants",
                "## **IA08 applicants",
                "## **Class 12",
                "## **Non-Class 12",
                "## **Long-term",
                "## **Fully managed",
                "## **PCC applicants",
            ]
        ),
    ],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
    definition_tools=_DefTools,
)
