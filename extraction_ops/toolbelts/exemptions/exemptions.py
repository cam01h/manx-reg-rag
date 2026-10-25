from core.sectors import (
    CLASS_1,
    CLASS_2,
    CLASS_3,
    CLASS_4,
    CLASS_5,
    CLASS_6,
    CLASS_7,
    CLASS_8,
    CLASS_9,
    RAO_CLASSES,
)
from extraction_ops.models import (
    DefaultSplitter,
    DefinitionTools,
    ToolBelt,
)
from extraction_ops.toolbelts.exemptions.exemptions_flattener import (
    S3_SWITCHED,
    S3_WRONG,
    flatten_exemptions_table,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    replace_from_dict,
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


def _clean_text(text: str) -> str:
    text = base_text_cleaner(text)
    text = strip_footnote_markers(text)
    text = flatten_exemptions_table(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    return text


_Trimmer = build_simple_markers("## **1 Title", '- "trustee in bankruptcy"')


_ExemptionsPara3Defs = build_simple_markers(
    '- "the Act" means the Financial', '- "class" References in these Regulations'
)

_ExemptionsClass4Defs = build_simple_markers(
    'For the purpose of this Class "company" includes', "- (d) a foundation established"
)

_ExemptionsSchedule3Defs = build_simple_markers(
    '- "the Authority" means', '- "trustee in bankruptcy"'
)

_DefTools = DefinitionTools(
    section_markers=[
        _ExemptionsPara3Defs,
        _ExemptionsClass4Defs,
        _ExemptionsSchedule3Defs,
    ],
    is_definition_line=starts_with(['- "', "For the purpose of this"]),
)


EXEMPTIONS_SECTOR_DICT = {
    "CLASS 1": CLASS_1,
    "CLASS 2": CLASS_2,
    "CLASS 3": CLASS_3,
    "CLASS 4": CLASS_4,
    "CLASS 5": CLASS_5,
    "CLASS 6": CLASS_6,
    "CLASS 7": CLASS_7,
    "CLASS 8": CLASS_8,
    "CLASS 9": CLASS_9,
}


def exemptions_sector_matcher(headers: tuple[str, ...]) -> tuple[str, ...]:
    applicability: tuple[str, ...] = tuple(
        v for h in headers for k, v in EXEMPTIONS_SECTOR_DICT.items() if k in h
    )
    return applicability if applicability else RAO_CLASSES


Exemptions = ToolBelt(
    document="Financial Services (Exemptions) Regulations 2011",
    hierarchy="secondary legislation",
    sectors=exemptions_sector_matcher,
    input_url="https://www.iomfsa.im/media/1466/financialservicesexemptionsregs2011.pdf",
    pdf_path=build_pdf_path("exemptions"),
    use_ocr=True,
    use_layout=True,
    pdf_handlers=None,
    trimmer=_Trimmer,
    header_matchers=[
        lambda line: (
            line.startswith("## **SCHEDULE")
            or line.startswith("## **")
            and line[5:6].isdigit()
        ),
        starts_with(["## **CLASS"]),
        starts_with(["## _"]),
    ],
    definition_tools=_DefTools,
    clean_text=_clean_text,
    re_pack_splitters=DefaultSplitter,
)
