import re

from core.sectors import FI_SECTORS
from extraction_ops.models import ChunkSplitters, DefinitionTools, ToolBelt
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    rejoin_page_breaks,
    replace_from_dict,
    replace_section,
    split_on_paragraph_not_list,
    split_on_paragraph_or_list_item,
    starts_with,
)

from .cyber_security_flattener import GLOSSARY, flatten_appendices

# version history printed at the foot of every page, sometimes as a "> " quote line
_VERSION_FOOTER = re.compile(r"^>? *V\.0\d issued .*$\n?", re.MULTILINE)

_REPLACEMENT_DICT = {
    # the malware bullet is one 2,000+ char paragraph; break it where it moves on to Trojans
    "backup copy.  A Trojan horse": "backup copy.\n\nA Trojan horse",
}


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_section(text, "|**Term**|", "## **1. Cyber security", GLOSSARY)
    text = flatten_appendices(text)
    text = _VERSION_FOOTER.sub("", text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    # the malware bullet runs over a page break
    text = rejoin_page_breaks(text)
    return text


_Trimmer = build_simple_markers(
    "## **Glossary", "- PwC (2016) Turnaround and transformation"
)

_DefMarkers = build_simple_markers(
    '- "Authority" Isle of Man', '- "Rule Book" Financial'
)

_DefTools = DefinitionTools(
    section_markers=[_DefMarkers], is_definition_line=starts_with(['- "'])
)

_Splitters = ChunkSplitters(
    primary=split_on_paragraph_not_list, fallback=split_on_paragraph_or_list_item
)

_SECTION = re.compile(r"^## \*\*\d\. ")
_SUB_SECTION = re.compile(r"^## \*\*\d\.\d\. ")


def _is_section(line: str) -> bool:
    return bool(_SECTION.match(line)) or line.startswith(
        ("## **Glossary", "## **Appendix")
    )


def _is_sub_section(line: str) -> bool:
    # "### " = the Appendix 1 sections and Appendix 2 examples written by the flattener
    return bool(_SUB_SECTION.match(line)) or line.startswith("### ")


# FSA08 licenceholders (Rule Book) and IA08 insurers, insurance managers and intermediaries
# (CGCs). Retirement benefits schemes are also covered but have no sector yet
CyberSecurity = ToolBelt(
    document="Regulatory Guidance - Cyber Security",
    hierarchy="guidance",
    sectors=fixed_sectors(FI_SECTORS),
    input_url="https://www.iomfsa.im/media/1694/141216finalisedguidancecyberse1.pdf",
    pdf_path=build_pdf_path("cyber_security"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[_is_section, _is_sub_section],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
    definition_tools=_DefTools,
)
