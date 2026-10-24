import re

from core.sectors import ALL_SECTORS
from extraction_ops.models import (
    DefinitionTools,
    ToolBelt,
)
from extraction_ops.toolbelts.defaults import DefaultSplitter
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    replace_from_dict,
    replace_section,
    starts_with,
    strip_footnote_bullets,
    strip_footnote_markers,
)

SANCTIONS_REPLACEMNENT_DICT = {
    "- **4 Implementation of UK sanctions": "## **4 Implementation of UK sanctions"
}


def _clean_text(text: str) -> str:
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


_Trimmer = build_simple_markers(
    "## _Introductory_", '- (4) In this section "the Crown"'
)

_SactionsSec3Markers = build_simple_markers(
    '- " **Guernsey** " means', '- " **UK sanctions provision** "'
)

SanctionsDefTools = DefinitionTools(
    section_markers=[_SactionsSec3Markers],
    is_definition_line=starts_with(['- " **']),
)


Sanctions = ToolBelt(
    document="Sanctions Act 2024",
    hierarchy="primary legislation",
    sectors=fixed_sectors(ALL_SECTORS),
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/PRINCIPAL/2024/2024-0002/2024-0002_1.pdf",
    pdf_path=build_pdf_path("sanctions"),
    trimmer=_Trimmer,
    header_matchers=[
        starts_with(["## _"]),
        lambda line: line.startswith("## **") and line[5].isdigit(),
    ],
    definition_tools=SanctionsDefTools,
    clean_text=_clean_text,
    re_pack_splitters=DefaultSplitter,
)
