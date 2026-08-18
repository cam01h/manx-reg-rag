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
    replace_from_dict,
    replace_section,
    split_on_bracketed_num,
    starts_with,
    strip_footnote_bullets,
    strip_footnote_markers,
)

SANCTIONS_REPLACEMNENT_DICT = {
    "- **4 Implementation of UK sanctions": "## **4 Implementation of UK sanctions"
}


def sanctions_text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = re.sub(
        # fixes ## **2** \n\n ## **commencement** and similar
        r"## \*\*(\d+[A-Z]?)\*\*\s*\n\s*## \*\*([^\n*]+)\*\*",
        r"## **\1 \2**",
        text,
    )
    text = re.sub(
        # pdf artifacts
        r"^[#\-\s]*"
        r"(?:\d+ \d{4} c\.\d+.*"
        r"|(?:P|J)\d{4}/\d+/\d+(?:\(\d+\))?(?:\s*to\s*\(\d+\))?(?:\s*(?:and|&)\s*\S+)*"
        r")\s*$\n?"
        # tynwald proceedure comes out weird from the pdf
        r"^[#\-\s]*Tynwald procedure - .*$\n?",
        "",
        text,
        flags=re.MULTILINE,
    )
    text = strip_footnote_markers(text)
    text = strip_footnote_bullets(text)
    text = replace_section(text, '6 "Territorial sea" is', "      - (e) require a")
    text = replace_from_dict(text, SANCTIONS_REPLACEMNENT_DICT)
    return text


SanctionsTrimmer = SectionMarkers(
    start=starts_with(["## _Introductory_"]),
    end=starts_with(['- (4) In this section "the Crown"']),
)

SactionsSec3Markers = SectionMarkers(
    start=starts_with(['- " **Guernsey** " means']),
    end=starts_with(['- " **UK sanctions provision** "']),
)

SanctionsDefTools = DefinitionTools(
    section_markers=[SactionsSec3Markers],
    is_definition_line=starts_with(['- " **']),
    is_double_def_line=base_double_def_line,
    is_false_dub_def=base_false_double_def,
)

SanctionsSplitters = ChunkSplitters(
    primary=split_on_bracketed_num, fallback=split_on_bracketed_num
)

Sanctions = ToolBelt(
    document="Sanctions Act 2024",
    hierarchy="primary legislation",
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/PRINCIPAL/2024/2024-0002/2024-0002_1.pdf",
    pdf_path=PROJECT_ROOT / "data/raw/custom/sanctions.pdf",
    use_ocr=True,
    pdf_handlers=None,
    trimmer=SanctionsTrimmer,
    header_matchers=[
        starts_with(["## _"]),
        lambda line: line.startswith("## **") and line[5].isdigit(),
    ],
    definition_tools=SanctionsDefTools,
    clean_text=sanctions_text_cleaner,
    re_pack_splitters=SanctionsSplitters,
    clean_body=base_body_cleaner,
    clean_header=base_header_cleaner,
    min_body_len=40,
)
