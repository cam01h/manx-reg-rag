from core.sectors import ALL_SECTORS
from extraction_ops.models import DefinitionTools, SectionMarkers, ToolBelt
from extraction_ops.toolbelts.fiu.fiu_shared import FIU_SUPPLEMENTAL
from extraction_ops.toolbelts.fiu.fiu_typologies import (
    TYPOLOGY_SPLITTERS,
    build_typology_cleaner,
    is_introduction,
)
from extraction_ops.toolbelts.nra.nra_base import is_glossary_line
from extraction_ops.toolbelts.shared_funcs import (
    build_pdf_path,
    fixed_sectors,
    starts_with,
)

# the page of icons on page 9 - read from the image, which has no text layer
_HIGHER_RISK_INDUSTRIES = """[Editors note: the below is transcribed from an image]
Higher risk industries:

- Construction
- Crop and Animal Production
- Forestry and Logging
- Fishing and Aquaculture
- Mining of Coal, Metal Ores or Precious Stones
- Manufacture of Tabacco Products
- Human Health and Social Care Services
- Health and Beauty Services
- IT Infrastructure or Support Services
- Travel or Tour Operation Services
- Manufacture of Textile Products
- Video, Sound or Music Production
- E-Gaming Software Supply Services
- Food and Beverage Service Activities
- Commercial Cleaning Services
- Manufacture of Food Products, such as Processing and Preserving of Meat, Fish, Crustaceans, Fruits and Vegetables
- Warehouse Activities to Support Cargo Handling
- Temporary Employment Agency Services
- Land and Water Freight Transport Services
- Other Personal Service Activities such as Activities Related to the Red-Light Industry, Massage Salons, Escort Services or Dating Services
"""

_REPLACEMENTS = {
    "## **[Higher Risk Industries ]** ": _HIGHER_RISK_INDUSTRIES,
}

_LAST_LINE = '"TF" Terrorism Financing'

_Trimmer = SectionMarkers(
    start=is_introduction,
    end=starts_with([_LAST_LINE]),
)

_Glossary = SectionMarkers(
    start=starts_with(['"AI" Artificial Intelligence']),
    end=starts_with([_LAST_LINE]),
)

_PDF_PATH = build_pdf_path("fiu_ms_typologies")

MsTypologies = ToolBelt(
    document="FIU Human Trafficking and Modern Day Slavery Typologies and Red Flags (June 2026)",
    hierarchy=FIU_SUPPLEMENTAL,
    # the typologies cover every sector - a case set in a bank still teaches a TCSP
    sectors=fixed_sectors(ALL_SECTORS),
    input_url="https://www.fiu.im/media/1268/human-trafficking-and-modern-slavery-typology-2026.pdf",
    pdf_path=_PDF_PATH,
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[starts_with(["# "]), starts_with(["## "])],
    clean_text=build_typology_cleaner(_PDF_PATH, _REPLACEMENTS),
    re_pack_splitters=TYPOLOGY_SPLITTERS,
    definition_tools=DefinitionTools(
        section_markers=[_Glossary], is_definition_line=is_glossary_line
    ),
)
