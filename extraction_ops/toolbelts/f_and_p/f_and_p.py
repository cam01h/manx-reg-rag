import re

from core.sectors import FI_SECTORS, IA08_FIRMS, INSURERS
from extraction_ops.models import ChunkSplitters, DefinitionTools, ToolBelt
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    header_sectors,
    rejoin_page_breaks,
    replace_from_dict,
    replace_section,
    split_on_paragraph_not_list,
    split_on_paragraph_or_list_item,
    starts_with,
    strip_footnote_bullets,
)

from .f_and_p_flattener import flatten_appendices

# "Regulated entity" is kept on one line: it is the end marker, and lines after the end
# marker go to the chunks rather than the definition
GLOSSARY = """- "AML/CFT Code" The current Anti-Money Laundering and Countering the Financing of Terrorism Code
- "Authority" Isle of Man Financial Services Authority
- "CISA2008" Collective Investment Schemes Act 2008
- "Connected person" Persons required to be notified to the Authority under section 29 of the IA2008
- "Controlled Function" Any of the functions set out at Appendix 2 of this document
- "DBROA15" Designated Businesses (Registration & Oversight) Act 2015
- "Designated insurer" See Appendix 9
- "DMLRO" Deputy money laundering reporting officer
- "FSA2008" Financial Services Act 2008
- "Governing body" In relation to any regulated entity, or controller of such, the body responsible for the direction and management of the business (for example a company's governing body will be its board of directors and a trust's governing body will be its trustees)
- "IA2008" Insurance Act 2008
- "Intermediate controller" Any controller (as defined in the regulatory legislation) which is not a controller of the regulated entity, its immediate parent, or an ultimate beneficial owner
- "ISPV" Insurance Special Purpose Vehicle
- "MLRO" Money laundering reporting officer
- "Notified and accepted Controlled Function" Any of the functions set out at in the table at Appendix 2 of this document as notified and accepted
- "Notified only Controlled Function" Any of the functions set out at in the table at Appendix 2 of this document as notified only
- "RBSA2000" Retirement Benefits Schemes Act 2000
- "Regulated entity" This term is used to mean any of the following: a licenceholder under the FSA2008; persons authorised or registered under the IA2008; permit holders, other than EU permit holders, under the IA2008; persons registered under the RBSA2000; corporate trustees of authorised retirement benefits schemes; the governing bodies of certain collective investment schemes in connection with Controlled Function R5 only; designated insurers where the Controlled Function is R30 - Group Actuary (see Appendix 9); or applicants to become regulated entities where the context requires.

"""

# footnotes are moved inline at their marker; the footnote lines are then stripped
_REPLACEMENT_DICT = {
    "regulatory objectives[1] .": "regulatory objectives [Footnote: Financial Services Act 2008 - section 2(2)(b)].",
    "by the regulated entity[2] that": "by the regulated entity [Footnote: For entities under the RBSA2000, where an individual trustee is being appointed, the Empowered Person must sign the declaration (see the form for definition); where a director is appointed to a corporate trustee of a retirement benefits scheme then the corporate trustee must sign, and where a director is appointed to a corporate administrator the administrator must sign.] that",
    # footnote 3 is dropped by pymupdf4llm, text taken from the PDF
    "certain Controlled Functions[3] within": "certain Controlled Functions [Footnote: R1, R2, R4, R6, R7, R8] within",
    "directly to the Authority[4] .": "directly to the Authority [Footnote: The Rehabilitation of Offenders Act (Exceptions) Order 2001 allows the Authority to take account of convictions which would otherwise be treated as spent under the Rehabilitation of Offenders Act 2001].",
    "entity as a whole[5] ,": "entity as a whole [Footnote: NB for Independent Non-executive Directors, the business knowledge is likely to be broader and less specific to the regulated entity],",
    "Authority in writing[7] ,": "Authority in writing [Footnote: It is expected that notification will take the form of an email or letter],",
    "likely to be non-individuals[8] but": "likely to be non-individuals [Footnote: The Authority would always expect an auditor of an authorised insurer to be a non-individual. If an individual is appointed as a regulated entity's auditor, an F&P 1 should be provided to the Authority.] but",
    "the intended appointment[9] ,": "the intended appointment [Footnote: As required by section 29(1) of the IA2008],",
    # headings that lost their "##"
    "**8. How should a regulated entity": "## **8. How should a regulated entity",
    "**9. How long do the fitness": "## **9. How long do the fitness",
    "**13. What if an individual is being appointed": "## **13. What if an individual is being appointed",
    "**14. What if a director is retiring": "## **14. What if a director is retiring",
    # question under the Appendix 8 heading, folded into it
    "## **Appendix 8 - Section 29 of the IA2008** \n\n**1. How does a corporate person have its fitness and propriety assessed?**": "## **Appendix 8 - Section 29 of the IA2008 - How does a corporate person have its fitness and propriety assessed?**",
    # list items run together / spaces left before punctuation
    "undischarged bankrupt; b) has entered": "undischarged bankrupt;\n\n- b) has entered",
    "under the IA2008** .": "under the IA2008**.",
    "determines its categorisation_ .": "determines its categorisation_.",
    "a retrospective exercise_ .": "a retrospective exercise_.",
    "criminal-records-checks-foroverseas-applicants": "criminal-records-checks-for-overseas-applicants",
    "I …………[NAME]… .. …… holding": "I [NAME] holding",
}

# sentence split by a page break with footnote 2 in between (left once the footnote is gone)
_PAGE_BREAK_DICT = {
    "notified and accepted Controlled \n\n\nFunction (preferably": "notified and accepted Controlled Function (preferably",
}


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_section(text, "## **Contents", "## **Glossary")
    text = replace_section(text, "|**Glossary**||", "## **1. Introduction", GLOSSARY)
    text = flatten_appendices(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    text = strip_footnote_bullets(text)
    text = replace_from_dict(text, _PAGE_BREAK_DICT)
    # paragraphs that run over a page break
    text = rejoin_page_breaks(text)
    return text


_Trimmer = build_simple_markers(
    "## **Glossary", "- Not serving in an independent capacity as director"
)

_DefMarkers = build_simple_markers('- "AML/CFT Code"', '- "Regulated entity"')

_DefTools = DefinitionTools(
    section_markers=[_DefMarkers], is_definition_line=starts_with(['- "'])
)

_Splitters = ChunkSplitters(
    primary=split_on_paragraph_not_list, fallback=split_on_paragraph_or_list_item
)

_SECTION = re.compile(r"^## \*\*\d+\. ")
# "## **a) Regulated entity" / "## **A. Integrity"
_SUB_SECTION = re.compile(r"^## \*\*(?:[a-z]\)|[A-D]\.) ")


def _is_section(line: str) -> bool:
    return bool(_SECTION.match(line)) or line.startswith(
        ("## **Glossary", "## **Appendix")
    )


def _is_sub_section(line: str) -> bool:
    # plain "## " headings: the Appendix 2 table groups, the Appendix 3 headings and
    # "## _Indicators of independence_". "## **Please note: ..." in Appendix 6 is body text
    if _SUB_SECTION.match(line):
        return True
    return line.startswith("## ") and not line.startswith("## **")


_SECTOR_MATCHERS = {
    "What about section 29 of the IA2008": IA08_FIRMS,
    "Appendix 8 - Section 29 of the IA2008": IA08_FIRMS,
    "Appendix 9 - Insurance - Group Supervision": INSURERS,
}

# FSA08 licenceholders, IA08 insurers / managers / intermediaries and RBSA2000 schemes (no
# sector yet); not designated businesses under the DBROA15
FAndP = ToolBelt(
    document="Regulatory Guidance - Fitness and Propriety",
    hierarchy="guidance",
    sectors=header_sectors(_SECTOR_MATCHERS, FI_SECTORS),
    input_url="https://www.iomfsa.im/media/3289/regulatoryguidancefitnessandpropriety.pdf",
    pdf_path=build_pdf_path("f_and_p"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[_is_section, _is_sub_section],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
    definition_tools=_DefTools,
)
