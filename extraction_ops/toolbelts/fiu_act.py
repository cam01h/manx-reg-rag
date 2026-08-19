import re
from config import PROJECT_ROOT
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
    in_line,
    rejoin_page_breaks,
    replace_from_dict,
    split_on_bracketed_letter,
    split_on_bracketed_num,
    starts_with,
    strip_footnote_markers,
)

FIU_REPLACEMENT_DICT = {'## " **initial provider**': '- " **initial provider**'}


def fiu_text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    # citation trailing a header
    text = re.sub(r" +P\d{4}/\d+/\d+(?:\(\d+\))?\s*$", "", text, flags=re.MULTILINE)
    # citation alone on a line
    text = re.sub(
        r"^[#\-\s]*P\d{4}/\d+/\d+(?:\(\d+\))?\s*$\n?", "", text, flags=re.MULTILINE
    )
    # Rejoins number to para name
    text = re.sub(
        r"## \*\*(\d+[A-Z]?)\*\*\s*\n\s*## \*\*([^\n*]+)\*\*",
        r"## **\1 \2**",
        text,
    )
    text = strip_footnote_markers(text)
    text = rejoin_page_breaks(text)
    text = replace_from_dict(text, FIU_REPLACEMENT_DICT)
    return text


FiuMarkers = SectionMarkers(
    start=in_line(["## **PART 1 - INTRODUCTORY"]),
    end=starts_with(["- (4) In this paragraph references"]),
)

FiuDefinitionSec3Markers = SectionMarkers(
    start=starts_with(['- " **Board**']), end=starts_with(['- " **the police force**'])
)

FiuDefinitionSec10Markers = SectionMarkers(
    start=starts_with(['- " **assigned matters']),
    end=starts_with(["   - (b) the Income Tax"]),
)

FiuDefinitionSec21Markers = SectionMarkers(
    start=starts_with(['- " **AML/CFT']),
    end=starts_with(["- (f) a person representing"]),
)

FiuDefinitionTools = DefinitionTools(
    section_markers=[
        FiuDefinitionSec3Markers,
        FiuDefinitionSec10Markers,
        FiuDefinitionSec21Markers,
    ],
    is_definition_line=starts_with(['- " **']),
    is_double_def_line=base_double_def_line,
    is_false_dub_def=base_false_double_def,
)

FiuSplitters = ChunkSplitters(
    primary=split_on_bracketed_num, fallback=split_on_bracketed_letter
)

FiuAct = ToolBelt(
    document="The Financial intelligence Unit Act 2016",
    hierarchy="primary legislation",
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/PRINCIPAL/2016/2016-0005/2016-0005_6.pdf",
    pdf_path=PROJECT_ROOT / "data/raw/custom/fiu_act.pdf",
    use_ocr=True,
    pdf_handlers=None,
    trimmer=FiuMarkers,
    header_matchers=[
        starts_with(["## **SCHEDULE"]),
        starts_with(["## **PART"]),
        lambda line: (
            line.startswith("## **") and line[5].isdigit() or line.startswith("- **")
        ),
    ],
    definition_tools=FiuDefinitionTools,
    clean_text=fiu_text_cleaner,
    re_pack_splitters=FiuSplitters,
    clean_body=base_body_cleaner,
    clean_header=base_header_cleaner,
    min_body_len=40,
)

# is_definition_line=lambda line: bool('- " **' in line),
# is_double_def_line=lambda segs: len(segs) == 5 and segs[2].strip() in ("or", "and"),
# is_false_dub_def=lambda segs: len(segs) == 5 and segs[2].strip() != "or",
# re_pack_splitter=lambda text: re.split( r"\n(?=- \(\d+\)|\d+[A-Z]?\.\s*\(\d+\)|\(\d+\)\s|\d+[A-Z]?\.\s)", text),
