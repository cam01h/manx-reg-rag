import re

from core.sectors import ALL_SECTORS
from extraction_ops.models import (
    DefaultSplitter,
    DefinitionTools,
    SectionMarkers,
    ToolBelt,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    in_line,
    rejoin_page_breaks,
    replace_from_dict,
    starts_with,
    strip_footnote_markers,
)

_REPLACEMENT_DICT = {'## " **initial provider**': '- " **initial provider**'}


def _text_cleaner(text: str) -> str:
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
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    return text


_FiuTrimmer = SectionMarkers(
    start=in_line(["## **PART 1 - INTRODUCTORY"]),
    end=starts_with(["- (4) In this paragraph references"]),
)

_FiuDefinitionSec3Markers = build_simple_markers(
    '- " **Board**', '- " **the police force**'
)

_FiuDefinitionSec10Markers = build_simple_markers(
    '- " **assigned matters', "   - (b) the Income Tax"
)

_FiuDefinitionSec21Markers = build_simple_markers(
    '- " **AML/CFT', "- (f) a person representing"
)

_FiuDefinitionTools = DefinitionTools(
    section_markers=[
        _FiuDefinitionSec3Markers,
        _FiuDefinitionSec10Markers,
        _FiuDefinitionSec21Markers,
    ],
    is_definition_line=starts_with(['- " **']),
)


FiuAct = ToolBelt(
    document="The Financial Intelligence Unit Act 2016",
    hierarchy="primary legislation",
    sectors=fixed_sectors(ALL_SECTORS),
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/PRINCIPAL/2016/2016-0005/2016-0005_6.pdf",
    pdf_path=build_pdf_path("fiu"),
    trimmer=_FiuTrimmer,
    header_matchers=[
        starts_with(["## **SCHEDULE"]),
        starts_with(["## **PART"]),
        lambda line: (
            line.startswith("## **") and line[5].isdigit() or line.startswith("- **")
        ),
    ],
    definition_tools=_FiuDefinitionTools,
    clean_text=_text_cleaner,
    re_pack_splitters=DefaultSplitter,
)
