from core.sectors import ALL_SECTORS
from extraction_ops.models import DefinitionTools, SectionMarkers, ToolBelt
from extraction_ops.toolbelts.fiu.fiu_shared import FIU_SUPPLEMENTAL
from extraction_ops.toolbelts.fiu.fiu_typologies import (
    TYPOLOGY_SPLITTERS,
    build_typology_cleaner,
    definitions_to_lines,
    is_introduction,
)
from extraction_ops.toolbelts.nra.nra_base import is_glossary_line
from extraction_ops.toolbelts.shared_funcs import (
    build_pdf_path,
    fixed_sectors,
    starts_with,
)

# read from the image on page 6 - the diagram has no text layer
_PF_STAGES = """from raising funds to paying for goods and services.

[Editors note: the below is transcribed from an image]

- Program fundraising: A proliferating country raises financial resources for in-country costs.
- Disguising the funds: The proliferating state moves assets into the international financial system, often involving a foreign exchange transaction, for trade purposes.
- Materials and technology procurement: The proliferating state or its agents uses these resources for procurement of materials and technology within the international financial system.
"""

# read from the image on page 16
_AI_METHODS = """[Editors note: the below is transcribed from an image]
Artificial Intelligence:

- AI-Enhanced Social Engineering: AI-generated phishing emails that mimic internal communications in order to gain system access by proliferators.
- AI-Powered Virtual Currency Transactions: Automated routing of payments and instantaneous fragmenting of funds by AI to streamline the layering of illicit funds in initial PF fund generation.
- AI-Fabricated Documentation: Realistic but false AI-created trade documents that are used by PF networks to deceive companies, regulators and law enforcement.
- AI-Scaled PF Networks: Large scale synthetic PF networks constructed by AI to include fictitious personas and corporate entities that obfuscate the true end-user.
- AI-Generated Deepfakes: AI-based face-swapping in live video calls that enables applicants linked to proliferating states to obscure their identity during the recruitment process.

*Note: These examples were extracted from a PF document published by Saudi Arabia's Ministry"""

_FUNDRAISING_TABLE = """|**Illicit Fundraising Activities**|**Licit Fundraising Activities**|
|---|---|
|Fraud<br>Cybertheft<br>Arms Trafficking<br>Illegal Wildlife Trade<br>Drugs Smuggling<br>Forgery|Charitable Donations<br>Government Funding<br>Sale of Non-Nuclear Military Equipment<br>Sale of Natural Resources<br>Foreign/Commercial Trade<br>Legitimate Business (restaurants, construction etc.)|"""

_FUNDRAISING_FLAT = """[Editors note: the below is a flattened table]

- Illicit fundraising activities: Fraud; Cybertheft; Arms Trafficking; Illegal Wildlife Trade; Drugs Smuggling; Forgery
- Licit fundraising activities: Charitable Donations; Government Funding; Sale of Non-Nuclear Military Equipment; Sale of Natural Resources; Foreign/Commercial Trade; Legitimate Business (restaurants, construction etc.)"""

_REPLACEMENTS = {
    "from raising funds to paying for goods and services. ": _PF_STAGES,
    "*Note: These examples were extracted from a PF document published by Saudi Arabia's Ministry": _AI_METHODS,
    _FUNDRAISING_TABLE: _FUNDRAISING_FLAT,
    # words hyphenated across a line of the FATF definition's box
    "pur-<br>poses": "purposes",
    "contra-<br>vention": "contravention",
}

_LAST_LINE = '"Zero Day Vulnerabilities"'

_Trimmer = SectionMarkers(
    start=is_introduction,
    end=starts_with([_LAST_LINE]),
)

# the glossary of acronyms and the cyber terms defined after it
_Glossary = SectionMarkers(
    start=starts_with(['"AI" Artificial Intelligence']),
    end=starts_with([_LAST_LINE]),
)

_PDF_PATH = build_pdf_path("fiu_pf_typologies")

PfTypologies = ToolBelt(
    document="FIU Proliferation Financing Typologies and Red Flags (August 2026)",
    hierarchy=FIU_SUPPLEMENTAL,
    # the typologies cover every sector - a case set in a bank still teaches a TCSP
    sectors=fixed_sectors(ALL_SECTORS),
    input_url="https://www.fiu.im/media/1303/proliferation-financing-typology-august-2026.pdf",
    pdf_path=_PDF_PATH,
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[starts_with(["# "]), starts_with(["## "])],
    clean_text=build_typology_cleaner(_PDF_PATH, _REPLACEMENTS, definitions_to_lines),
    re_pack_splitters=TYPOLOGY_SPLITTERS,
    definition_tools=DefinitionTools(
        section_markers=[_Glossary], is_definition_line=is_glossary_line
    ),
)
