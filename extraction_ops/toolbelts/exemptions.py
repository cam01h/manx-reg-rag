from config import PROJECT_ROOT
from core.sectors import LICENCE_CLASSES
from extraction_ops.models import (
    ChunkSplitters,
    DefinitionTools,
    SectionMarkers,
    ToolBelt,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_body_cleaner,
    base_double_def_line,
    base_false_double_def,
    base_header_cleaner,
    base_text_cleaner,
    split_on_bracketed_amended_num,
    split_on_bracketed_letter,
    starts_with,
)


def exemptions_text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    return text


ExemptionsTrimmer = SectionMarkers(
    start=starts_with(["## **3 Interpretation"]),
    end=starts_with(["- (4) In determining for the"]),
)

ExemptionsDefMarkers = SectionMarkers(
    start=starts_with(['"accommodation address facilities" means']),
    end=starts_with(["(c) an instrument entitling"]),
)

ExemptionsDefTools = DefinitionTools(
    section_markers=[ExemptionsDefMarkers],
    is_definition_line=starts_with(['"']),
    is_double_def_line=base_double_def_line,
    is_false_dub_def=base_false_double_def,
)

ExemptionsSplitters = ChunkSplitters(
    primary=split_on_bracketed_amended_num, fallback=split_on_bracketed_letter
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
        starts_with(["## **Regulated activities", "## **Exclusion", "## **PART"]),
        starts_with(["## _", "_"]),
    ],
    definition_tools=ExemptionsDefTools,
    clean_text=exemptions_text_cleaner,
    re_pack_splitters=ExemptionsSplitters,
    clean_body=base_body_cleaner,
    clean_header=base_header_cleaner,
    min_body_len=40,
)
