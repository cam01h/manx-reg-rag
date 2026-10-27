from core.sectors import ALL_SECTORS
from extraction_ops.models import ChunkSplitters, ToolBelt
from extraction_ops.toolbelts.fiu.fiu_shared import (
    FIU_GUIDANCE,
    demote_unnumbered_headings,
    drop_picture_markers,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    replace_from_dict,
    split_on_paragraph_not_list,
    split_on_paragraph_or_list_item,
    starts_with,
)

_THEMIS_OPTIONS_TABLE = """|**Legislation Option**|**When to Use**|
|---|---|
|**IOM/UK/UN Sanctions**<br>**Breach (or Attempted Breach)**|Where you know or suspect a breach of IOM/UK/UN sanctions has<br>occurred or been attempted.|
|**Sanctions - Frozen Assets**|To inform the FIU of assets frozen in relation to a sanctions designation.|
|**POCA/ATCA/S24**|For reports relating to other non-IOM/UK/UN sanctions regimes including<br>OFAC and international national level designations.|"""

_THEMIS_OPTIONS_FLAT = """[Editors note: the below is a flattened table]

Legislation option - when to use:

- IOM/UK/UN Sanctions Breach (or Attempted Breach): Where you know or suspect a breach of IOM/UK/UN sanctions has occurred or been attempted.
- Sanctions - Frozen Assets: To inform the FIU of assets frozen in relation to a sanctions designation.
- POCA/ATCA/S24: For reports relating to other non-IOM/UK/UN sanctions regimes including OFAC and international national level designations."""

_REPLACEMENT_DICT = {
    _THEMIS_OPTIONS_TABLE: _THEMIS_OPTIONS_FLAT,
    # hyphens in the link read as list markers
    "Customs and Immigration - - - - - - - Sanctions Lists Webpage: https://www.gov.im/categories/tax vat and your money/sanctions and export - control/sanctions lists/": "Customs and Immigration Sanctions Lists Webpage: https://www.gov.im/categories/tax-vat-and-your-money/sanctions-and-export-control/sanctions-lists/",
    # bullet character left inside a list item
    "- • ": "- ",
    "Section 24., POCA or ATCA": "Section 24, POCA or ATCA",
    "A clear outline the activity": "A clear outline of the activity",
    "undertake a transaction** .": "undertake a transaction**.",
    # sub-headings within "Financial Sanctions Reporting via Themis"
    "## **Reporting Obligations under Sanctions Legislation**": "### **Reporting Obligations under Sanctions Legislation**",
    "## **Reporting via Themis**": "### **Reporting via Themis**",
}

# the shaded title bars; every other "## **" line is a bold statement or an example box
_SECTION_TITLES = [
    "## **Introduction",
    "## **Financial Sanctions**",
    "## **Financial Sanctions Reporting via Themis",
    "## **Financial Sanctions Breach Reporting",
    "## **Reporting Frozen Assets",
    "## **Reporting Related to Non-IOM/UK/UN Financial Sanctions",
    "## **Further Guidance and Contacts",
]


def _demote_statements(text: str) -> str:
    lines = text.split("\n")
    keep = [
        line
        if line.startswith(tuple(_SECTION_TITLES))
        else demote_unnumbered_headings(line)
        for line in lines
    ]
    return "\n".join(keep)


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = drop_picture_markers(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    text = _demote_statements(text)
    return text


_Trimmer = build_simple_markers(
    "## **Introduction",
    "Customs and Immigration retain responsibility for investigating suspected breaches",
)

_Splitters = ChunkSplitters(
    primary=split_on_paragraph_not_list, fallback=split_on_paragraph_or_list_item
)

SanctionsReporting = ToolBelt(
    document="FIU Guidance: Financial Sanctions Reporting (August 2026)",
    hierarchy=FIU_GUIDANCE,
    sectors=fixed_sectors(ALL_SECTORS),
    input_url="https://www.fiu.im/media/1299/mlro-sanctions-reporting-guidance-august-26.pdf",
    pdf_path=build_pdf_path("fiu_sanactions_reporting"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[starts_with(_SECTION_TITLES), starts_with(["### **"])],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
