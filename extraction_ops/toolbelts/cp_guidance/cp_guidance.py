import re

from core.sectors import FI_SECTORS
from extraction_ops.models import ChunkSplitters, DefinitionTools, ToolBelt
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    rejoin_page_breaks,
    replace_from_dict,
    replace_section,
    split_on_paragraph_not_list,
    split_on_paragraph_or_list_item,
    starts_with,
    strip_footnote_bullets,
)

from .cp_guidance_flattener import (
    flatten_appendices,
    flatten_regime_tables,
    flatten_staged_approach,
)

_GLOSSARY = """- "Authority" Isle of Man Financial Services Authority
- "EDMP" Enforcement Decision-Making Process
- "FSA08" Financial Services Act 2008
- "FSC" Financial Supervision Commission
- "IA08" Insurance Act 2008
- "Tribunal" Financial Services Tribunal

"""

# footnotes are moved inline at their marker; the footnote lines are then stripped
_REPLACEMENT_DICT = {
    "current and former licenceholders:[1]": "current and former licenceholders [Footnote: Any reference in this document to 'regulations' refers to a provision of either or both of the Financial Services (Civil Penalties) Regulations 2015 or the Insurance (Civil Penalties) Regulations 2022, as applicable.]:",
    "taken under the EDMP.[2]": "taken under the EDMP [Footnote: https://www.iomfsa.im/enforcement/enforcement-action/].",
    "international financial centre.[3]": "international financial centre [Footnote: Section 2 of the FSA08 and section 1 of the IA08.].",
    "entity's 'relevant income'.[4]": "entity's 'relevant income' [Footnote: 'Relevant income' is defined in regulation 3 (Interpretation) of each of the Financial Services (Civil Penalties) Regulations 2015 and the Insurance (Civil Penalties) Regulations 2022.].",
    "regulated entity under the IA08.[5]": "regulated entity under the IA08 [Footnote: Rule 2.8 of the Financial Services Rule Book 2016 and section 14(3) of the IA08.].",
    "to the Authority's satisfaction.[6]": "to the Authority's satisfaction [Footnote: For avoidance of doubt, under the Regulations a 30% discount is either applied or it is not. The percentage cannot be altered. By contrast, regulation 5(4) of the Anti-Money Laundering and Countering the Financing of Terrorism (Civil Penalties) Regulations 2019 allow for a penalty to be reduced by 'up to 30%'.].",
    # sentence split by a page break with footnote 6 in between; moved down to its second half
    "administrative). Section 32 of the": "administrative).",
    "FSA08 specifies the decisions": "Section 32 of the FSA08 specifies the decisions",
}


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_section(text, "## **Contents", "## **Glossary")
    text = replace_section(text, "## **Glossary", "## **Update Notes", _GLOSSARY)
    text = flatten_regime_tables(text)
    text = flatten_staged_approach(text)
    text = flatten_appendices(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    text = strip_footnote_bullets(text)
    # paragraphs that run over a page break, with a footnote in between
    text = rejoin_page_breaks(text)
    return text


_Trimmer = build_simple_markers(
    "## **Discretionary Civil Penalties under", "- Uncorrected: Left faulty or wrong"
)

_DefMarkers = build_simple_markers(
    '- "Authority" Isle of Man', '- "Tribunal" Financial Services'
)

_DefTools = DefinitionTools(
    section_markers=[_DefMarkers], is_definition_line=starts_with(['- "'])
)

_Splitters = ChunkSplitters(
    primary=split_on_paragraph_not_list, fallback=split_on_paragraph_or_list_item
)

_SECTION = re.compile(r"^## \*\*\d\. ")
_SUB_SECTION = re.compile(r"^## \*\*\d\.\d ")
_SUB_SUB_SECTION = re.compile(r"^## \*\*\d\.\d\.\d ")


def _is_section(line: str) -> bool:
    return bool(_SECTION.match(line)) or line.startswith(
        (
            "## **Discretionary Civil Penalties under",
            "## **Update Notes",
            "## **Appendix",
        )
    )


def _is_sub_section(line: str) -> bool:
    return bool(_SUB_SECTION.match(line))


def _is_sub_sub_section(line: str) -> bool:
    return bool(_SUB_SUB_SECTION.match(line))


# FSA08 licenceholders and other permitted persons; IA08 authorised insurers, registered
# insurance managers and registered insurance intermediaries
CpGuidance = ToolBelt(
    document="Discretionary Civil Penalties under the Financial Services Act 2008 and the Insurance Act 2008 - Guidance Note",
    hierarchy="guidance",
    sectors=fixed_sectors(FI_SECTORS),
    input_url="https://www.iomfsa.im/media/1582/directorshipsguidancemar2015.pdf",
    pdf_path=build_pdf_path("cp_guidance"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[_is_section, _is_sub_section, _is_sub_sub_section],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
    definition_tools=_DefTools,
)
