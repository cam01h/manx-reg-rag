from config import PROJECT_ROOT
from core.sectors import LICENCE_CLASSES
from extraction_ops.models import (
    ChunkSplitters,
    DefinitionTools,
    SectionMarkers,
    ToolBelt,
)
from extraction_ops.toolbelts.exemptions.exemptions_flattener import (
    S3_SWITCHED,
    S3_WRONG,
    flatten_exemptions_table,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_body_cleaner,
    base_double_def_line,
    base_false_double_def,
    base_header_cleaner,
    base_text_cleaner,
    replace_from_dict,
    split_on_bracketed_letter,
    split_on_bracketed_num,
    starts_with,
    strip_footnote_markers,
)

_REPLACEMENT_DICT = {
    "## **2** \n\n## **Commencement": "## **2 Commencement",
    S3_WRONG: S3_SWITCHED,
    "## **SCHEDULE l** \n\nRegulation 4. \n\n## **EXEMPTIONS FROM LICENSING**": "## **SCHEDULE 1 - EXEMPTIONS FROM LICENSING**",
    "## **SCHEDULE 2** \n\nRegulation 5. \n\n## **USE OF EQUIPMENT ON THE ISLAND**": "## **SCHEDULE 2 - USE OF EQUIPMENT ON THE ISLAND**",
    "## **SCHEDULE 3** \n\nRegulation 3. \n\n## **INTERPRETATION**": "## **SCHEDULE 3 - INTERPRETATION**",
    "\n_Company officers and employees_": "\n## _Company officers and employees_",
    "\n_Corporate trustees, protectors": "\n## _Corporate trustees, protectors",
    "\n_Liquidators, receivers etc._": "\n## _Liquidators, receivers etc._",
    "Regulated Activities Order 201l": "Regulated Activities Order 2011",
    "- 4 SD 603/99 as amended by SD 407/00, 87/03, 347/03 and 806/07 \n": "",
}


def exemptions_text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = strip_footnote_markers(text)
    text = flatten_exemptions_table(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    return text


ExemptionsTrimmer = SectionMarkers(
    start=starts_with(["## **1 Title"]),
    end=starts_with(['- "trustee in bankruptcy"']),
)


ExemptionsPara3Defs = SectionMarkers(
    start=starts_with(['- "the Act" means the Financial']),
    end=starts_with(['- "class" References in these Regulations']),
)

ExemptionsClass4Defs = SectionMarkers(
    start=starts_with(['For the purpose of this Class "company" includes']),
    end=starts_with(["- (d) a foundation established"]),
)

ExemptionsSchedule3Defs = SectionMarkers(
    start=starts_with(['- "the Authority" means']),
    end=starts_with(['- "trustee in bankruptcy"']),
)

ExemptionsDefTools = DefinitionTools(
    section_markers=[
        ExemptionsPara3Defs,
        ExemptionsClass4Defs,
        ExemptionsSchedule3Defs,
    ],
    is_definition_line=starts_with(['- "', "For the purpose of this"]),
    is_double_def_line=base_double_def_line,
    is_false_dub_def=base_false_double_def,
)

ExemptionsSplitters = ChunkSplitters(
    primary=split_on_bracketed_num, fallback=split_on_bracketed_letter
)

EXEMPTIONS_SECTOR_DECT = {}


def exemptions_sector_matcher(headers: tuple[str, ...]) -> tuple[str, ...]:
    applicability: tuple[str, ...] = tuple(
        v for h in headers for k, v in EXEMPTIONS_SECTOR_DECT.items() if k in h
    )
    return applicability if applicability else LICENCE_CLASSES


Exemptions = ToolBelt(
    document="Financial Services (Exemptions) Regulations 2011",
    hierarchy="secondary legislation",
    sectors=exemptions_sector_matcher,
    input_url="https://www.iomfsa.im/media/1466/financialservicesexemptionsregs2011.pdf",
    pdf_path=PROJECT_ROOT / "data/raw/custom/exemptions.pdf",
    use_ocr=True,
    use_layout=True,
    pdf_handlers=None,
    trimmer=ExemptionsTrimmer,
    header_matchers=[
        lambda line: (
            line.startswith("## **SCHEDULE")
            or line.startswith("## **")
            and line[5:6].isdigit()
        ),
        starts_with(["## **CLASS"]),
        starts_with(["## _"]),
    ],
    definition_tools=ExemptionsDefTools,
    clean_text=exemptions_text_cleaner,
    re_pack_splitters=ExemptionsSplitters,
    clean_body=base_body_cleaner,
    clean_header=base_header_cleaner,
    min_body_len=40,
)
