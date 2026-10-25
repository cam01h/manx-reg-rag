import re

from core.sectors import CLASS_1, RAO_CLASSES
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
    starts_with,
)

from .nb_governance_flattener import flatten_appendix_1_table

_REPLACEMENT_DICT = {
    # sub-section heading that came through as a bold list item
    "- **3.3. General guidance for small licenceholders**": "## **3.3. General guidance for small licenceholders**",
    # page break mid-sentence
    "does not function \n\neffectively.": "does not function effectively.",
    "mediumsized": "medium-sized",
}


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_section(text, "## Contents", "## **1. Introduction")
    text = flatten_appendix_1_table(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    return text


_Trimmer = build_simple_markers(
    "## **Guidance on Corporate Governance", "- Higgs (2003"
)

_Splitters = ChunkSplitters(
    primary=split_on_paragraph_not_list, fallback=split_on_paragraph
)

_SECTION = re.compile(r"^## \*\*\d\. ")
_SUB_SECTION = re.compile(r"^## \*\*\d\.\d\. ")


def _is_section(line: str) -> bool:
    return bool(_SECTION.match(line)) or line.startswith(
        (
            "## **Guidance on Corporate Governance",
            "## **STATUS OF GUIDANCE",
            "## **Appendix 1",
        )
    )


def _is_sub_section(line: str) -> bool:
    return bool(_SUB_SECTION.match(line))


# "For all licenceholders except for Deposit Takers (Class 1) and Professional Officers".
# Professional officers sit inside Classes 4 and 5, so they can't be excluded at class level
_NON_BANK = tuple(s for s in RAO_CLASSES if s != CLASS_1)

NbGovernance = ToolBelt(
    document="Guidance on Corporate Governance (all licenceholders except Deposit Takers and Professional Officers)",
    hierarchy="guidance",
    sectors=fixed_sectors(_NON_BANK),
    input_url="https://www.iomfsa.im/media/1543/corporategovernancenonbanksfinal.pdf",
    pdf_path=build_pdf_path("nb_governance"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[
        _is_section,
        _is_sub_section,
        starts_with(["## Objective"]),
    ],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
