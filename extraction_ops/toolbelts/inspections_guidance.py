import re

from core.sectors import ALL_SECTORS
from extraction_ops.models import ChunkSplitters, ToolBelt
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    replace_from_dict,
    replace_section,
    split_on_paragraph,
    split_on_paragraph_not_list,
    strip_footnote_bullets,
)

_REPLACEMENT_DICT = {
    # footnote moved inline at its marker, the footnote line is stripped below
    "little or no prior notice[1] .": 'little or no prior notice [Footnote: The Acts set out that, when exercising powers of inspection, the Authority is entitled to "rights of entry and access" (to the Firm\'s premises and records) "during reasonable hours".].',
    # the italic run is broken around the defined term
    '("_ _**the Authority** ")': '("the Authority")',
    "inspection report) _**.**_": "inspection report).",
    "our pre- \n\ninspection review": "our pre-inspection review",
}

# defined terms in bold inside quotes: '(the " **FSA08** ")' -> '(the "FSA08")'
_BOLD_TERM = re.compile(r'" \*\*([^*]+)\*\* "')


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_section(text, "## **Contents", "## **1. Background")
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    text = strip_footnote_bullets(text)
    text = _BOLD_TERM.sub(r'"\1"', text)
    # "_**pre-inspection**_ , _**on-site**_" -> "pre-inspection, on-site"
    text = re.sub(r"(\*\*_?|_) +([.,;:)])", r"\1\2", text)
    return text


_Trimmer = build_simple_markers(
    "## **STATUS OF GUIDANCE",
    "If it subsequently transpires that the remediation plan",
)

_Splitters = ChunkSplitters(
    primary=split_on_paragraph_not_list, fallback=split_on_paragraph
)

_SECTION = re.compile(r"^## \*\*\d\. ")
_SUB_SECTION = re.compile(r"^## \*\*\d\.\d ")


def _is_section(line: str) -> bool:
    return bool(_SECTION.match(line)) or line.startswith("## **STATUS OF GUIDANCE")


def _is_sub_section(line: str) -> bool:
    return bool(_SUB_SECTION.match(line))


# covers every Firm the Authority can inspect: FSA08, IA08, RBSA, DBROA and BOA
InspectionsGuidance = ToolBelt(
    document="Inspections Guidance for Firms",
    hierarchy="guidance",
    sectors=fixed_sectors(ALL_SECTORS),
    input_url="https://www.iomfsa.im/media/2898/external-inspections-guidance.pdf",
    pdf_path=build_pdf_path("inspections_guidance"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[_is_section, _is_sub_section],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
