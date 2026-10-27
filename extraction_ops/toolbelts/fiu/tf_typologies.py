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

# read from the image on page 11 - the four boxes have no text layer
_APPROACH_BOXES = """Isle of Man based financial institutions can strengthen their approach by:
[Editors note: the below is transcribed from an image]

- Incorporating contextual open-source review into onboarding and periodic due diligence.
- Training frontline and investigations staff on dual-use symbols and evolving extremist imagery.
- Integrating behavioural, transactional and network analysis within existing TF risk frameworks.
- Maintaining dynamic internal guidance reflecting emerging symbol trends.
"""

# three columns of names read across the page, so multi-word names run together
_LIST_BI = "Bulgaria Monaco South Sudan Burkina Faso Syrian Arab Republic Mozambique Cameroon Namibia United Republic of Tanzania Democratic Republic of the Congo Nigeria Bolivarian Republic of Venezuela Croatia Philippines Vietnam Haiti Russian Federation Yemen Kenya Senegal Mali South Africa"

_LIST_BII = """|Afghanistan|Eritrea|Pakistan|
|---|---|---|
|Angola|Eswatini|Sierra Leone|
|Belarus|Ethiopia|Solomon Islands|
|Plurinational State of Bolivia|Guinea|Somalia|
|Burundi|Guinea-Bissau|Sudan|
|Central African Republic|Iraq|Tajikistan|
|Chad|Kyrgyzstan|Togo|
|Comoros|Lebanon|Türkiye|
|Congo|Liberia|Turkmenistan|
|Cuba|Libya|Ukraine|
|Djibouti|Mauritania|Zimbabwe|
|Egypt|Republic of Moldova||
|Equatorial Guinea|Niger||"""

_REPLACEMENTS = {
    "Isle of Man based financial institutions can strengthen their approach by: ": _APPROACH_BOXES,
    _LIST_BI: "Bulgaria, Burkina Faso, Cameroon, Croatia, Democratic Republic of the Congo, Haiti, Kenya, Mali, Monaco, Mozambique, Namibia, Nigeria, Philippines, Russian Federation, Senegal, South Africa, South Sudan, Syrian Arab Republic, United Republic of Tanzania, Bolivarian Republic of Venezuela, Vietnam, Yemen",
    _LIST_BII: "Afghanistan, Angola, Belarus, Plurinational State of Bolivia, Burundi, Central African Republic, Chad, Comoros, Congo, Cuba, Djibouti, Egypt, Equatorial Guinea, Eritrea, Eswatini, Ethiopia, Guinea, Guinea-Bissau, Iraq, Kyrgyzstan, Lebanon, Liberia, Libya, Mauritania, Republic of Moldova, Niger, Pakistan, Sierra Leone, Solomon Islands, Somalia, Sudan, Tajikistan, Togo, Türkiye, Turkmenistan, Ukraine, Zimbabwe",
    # the "Typologies:" title is black text on a white panel and does not come through
    "**----- Start of picture text -----**<br>\nTypology 1:<br>": "# Typologies\n\n**----- Start of picture text -----**<br>\nTypology 1:<br>",
    # links read with their hyphens as list markers
    "## - - - - -- https://www.gov.uk/government/publications/proscribed terror groups or organisations 2": "https://www.gov.uk/government/publications/proscribed-terror-groups-or-organisations",
    "## - - - https://www.gov.uk/government/publications/the uk sanctions list": "https://www.gov.uk/government/publications/the-uk-sanctions-list",
    '"14" (referencing': '- "14" (referencing',
    "(TBML )": "(TBML)",
    "Northern Ireland- related": "Northern Ireland-related",
    # the second page of high risk countries repeats the section title
    "**----- Start of picture text -----**<br>\nHigh Risk Countries (cont.):<br>**----- End of picture text -----**<br>": "",
}

_LAST_LINE = '"IVTs" Informal Value Transfer Systems'

_Trimmer = SectionMarkers(
    start=is_introduction,
    end=starts_with([_LAST_LINE]),
)

_Glossary = SectionMarkers(
    start=starts_with(['"AML" Anti-Money Laundering']),
    end=starts_with([_LAST_LINE]),
)

_PDF_PATH = build_pdf_path("fiu_tf_typologies")

TfTypologies = ToolBelt(
    document="FIU Terrorist Financing Typologies and Red Flags (May 2026)",
    hierarchy=FIU_SUPPLEMENTAL,
    # the typologies cover every sector - a case set in a bank still teaches a TCSP
    sectors=fixed_sectors(ALL_SECTORS),
    input_url="https://www.fiu.im/media/1266/terrorist-financing-typology-2026.pdf",
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
