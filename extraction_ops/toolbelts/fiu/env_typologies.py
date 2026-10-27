import re

from core.sectors import ALL_SECTORS
from extraction_ops.models import SectionMarkers, ToolBelt
from extraction_ops.toolbelts.fiu.fiu_shared import FIU_SUPPLEMENTAL
from extraction_ops.toolbelts.fiu.fiu_typologies import (
    TYPOLOGY_SPLITTERS,
    build_typology_cleaner,
    is_introduction,
)
from extraction_ops.toolbelts.shared_funcs import (
    build_pdf_path,
    fixed_sectors,
    replace_section,
    starts_with,
)

# the four sector boxes on page 5 - read from the image, which has no text layer
_SECTOR_BOXES = """conduit for environmental crime proceeds.

[Editors note: the below is transcribed from an image]

- Trust and Corporate Services Providers: International nature of business; Potential misuse of complex structures to obscure ownership and underlying activity of structure.
- Life Insurance/ Assurance: International nature of business; Activity in jurisdictions with higher EWC risk; Use of intermediaries.
- Banking Sector: International client base; Activity in jurisdictions with higher EWC risk; Provision of services to international legal persons and arrangements.
- Online Gaming Sector: Customers are often located internationally; Previous identified links between gaming sector and transnational organised crime in jurisdictions that are higher risk for EWC.
"""

_REPLACEMENTS = {
    # the legend of the bar chart beside it is read into the paragraph
    "When asked how well they felt they **Banking █** and their colleagues     understand the **DNFPB █** different types of EWC, the majority of **Gaming █** respondents (97) said somewhat. More **Insurance █** respondents said they understood   a **Other Financial Services █** little (69) or not at all (9) than said **TCSP █** they understood quite well (44) or very well (8).": "When asked how well they felt they and their colleagues understand the different types of EWC, the majority of respondents (97) said somewhat. More respondents said they understood a little (69) or not at all (9) than said they understood quite well (44) or very well (8).",
    # the end of typology 1's red flags repeated in the source after typology 3's last one
    "understanding across                                 different": "understanding across different",
    "regulatory sanctions and reported earnings, adverse media": "regulatory sanctions",
    "conduit for environmental crime proceeds.": _SECTOR_BOXES,
    # "Agricultural Non compliance - covering ..." heading read with its hyphens as list markers
    "## **- - Agricultural Non compliance covering": "**Agricultural Non-compliance - covering",
}


def _contact_labels(text: str) -> str:
    # the key contacts' headings are labels for a phone number each - kept together in one
    # section rather than a chunk per number
    head, _, contacts = text.partition("# Key Contacts")
    contacts = re.sub(r"^## (.+?)[ \t]*$", r"**\1:**", contacts, flags=re.MULTILINE)
    return f"{head}# Key Contacts{contacts}"


def _extra_cleaner(text: str) -> str:
    # a list of links, between Project Anton and the key contacts
    text = replace_section(text, "# Resources and Links", "# Key Contacts")
    return _contact_labels(text)


_Trimmer = SectionMarkers(
    start=is_introduction,
    end=starts_with(["DEFA Forestry:"]),
)

_PDF_PATH = build_pdf_path("fiu_enviromental_typologies")

EnvTypologies = ToolBelt(
    document="FIU Environmental Crime Typologies and Red Flags (December 2025)",
    hierarchy=FIU_SUPPLEMENTAL,
    # the typologies cover every sector - a case set in a bank still teaches a TCSP
    sectors=fixed_sectors(ALL_SECTORS),
    input_url="https://www.fiu.im/media/1251/environmental-crime-typology-december-2025.pdf",
    pdf_path=_PDF_PATH,
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[starts_with(["# "]), starts_with(["## "])],
    clean_text=build_typology_cleaner(_PDF_PATH, _REPLACEMENTS, _extra_cleaner),
    re_pack_splitters=TYPOLOGY_SPLITTERS,
)
