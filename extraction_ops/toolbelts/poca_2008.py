import re

from core.sectors import ALL_SECTORS
from extraction_ops.models import (
    ChunkSplitters,
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
    replace_from_dict,
    split_on_bracketed_letter,
    split_on_bracketed_num,
    starts_with,
    strip_footnote_bullets,
    strip_footnote_markers,
)

POCA_REPLACEMENT_DICT = {
    # artifacts from pymupdf
    "\n- \n": "",
    "222ACompliance": "222A Compliance",
    '## " **tax adviser': '- " **tax adviser',
    "- **8 Exclusions": "## **8 Exclusions",
    # definition minipulation
    "References in those sections to a disclosure": '"disclosure" - References in those sections to a disclosure',
    "- (2) Criminal conduct": '- (2) "Criminal conduct"',
    "- (3) Property is criminal property": '- (3) "criminal property" - Property is criminal property',
    "- (9) Property is all": '- (9) "Property" is all',
    "- (11) Money laundering": '- (11) "Money laundering"',
    "- (12) For the purposes": '- (12) "disclosure" For the purposes',
}


def _clean_text(text: str) -> str:
    text = base_text_cleaner(text)
    # ammendment markers
    text = re.sub(r" *\[(?:P\d{4}|\d{4})/[^\]]*\]", "", text)
    text = re.sub(r" *\[(?!Repealed\])[^\]]{20,}\]", "", text)
    # pymupdf artifacts that split "\n- (d) \n\n - paragraph"
    text = re.sub(r"- \((\d{1,2})\)\s*\n\s*\n\s*- (?=\w)", r"- (\1) ", text)
    text = strip_footnote_bullets(text)
    text = strip_footnote_markers(text)
    text = replace_from_dict(text, POCA_REPLACEMENT_DICT)
    return text


_Trimmer = build_simple_markers(
    "## **PART 1 - CIVIL RECOVERY", "   - (w) the Law Society of Scotland"
)

_PocaIntroDefs = build_simple_markers(
    '## **2 "Unlawful', "   - (b) it is not necessary to"
)

_PocaChap2Defs = SectionMarkers(
    start=starts_with(['## **5 "Associated property']),
    end=in_line(["- (3) No property is to be treated"]),
)

_PocaSec65Defs = build_simple_markers('- " **the Attorney General', '- " **value**')

_PocaSec149Defs = build_simple_markers('- (3) "disclosure"', "- (4A) In those sections")

_PocaSec158P1Defs = build_simple_markers(
    '- (2) "Criminal conduct', "   - (b) the alleged"
)

_PocaSec158P2Defs = build_simple_markers(
    '- (9) "Property"', '- (15) " **the data protection'
)

_PocaSec222ADefs = build_simple_markers('- "FATF" means', '- "relevant international')

_PocaSched4Defs = build_simple_markers(
    '- the " **AML/CFT Code', "- (e) participation in"
)

POCA_DEF_MARKERS = [
    _PocaIntroDefs,
    _PocaChap2Defs,
    _PocaSec65Defs,
    _PocaSec149Defs,
    _PocaSec158P1Defs,
    _PocaSec158P2Defs,
    _PocaSec222ADefs,
    _PocaSched4Defs,
]

_Splitters = ChunkSplitters(
    primary=split_on_bracketed_letter,
    fallback=split_on_bracketed_num,
)

_DefinitionTools = DefinitionTools(
    section_markers=POCA_DEF_MARKERS,
    is_definition_line=in_line(
        [
            "## **",
            ') " **',
            '- " **',
            ') "',
            ") In those sections",
            '- "',
            '- the "',
            'definition " **',
        ]
    ),
)


Poca = ToolBelt(
    document="The Proceeds of Crime Act (POCA) 2008",
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/PRINCIPAL/2008/2008-0013/2008-0013_28.pdf",
    hierarchy="primary legislation",
    sectors=fixed_sectors(ALL_SECTORS),
    pdf_path=build_pdf_path("poca"),
    trimmer=_Trimmer,
    definition_tools=_DefinitionTools,
    header_matchers=[
        starts_with(["## **PART", "## **SCHEDULE"]),
        starts_with(["## CHAPTER"]),
        starts_with(["## _"]),
        lambda line: line.startswith("## **") and line[5].isdigit(),
    ],
    re_pack_splitters=_Splitters,
    clean_text=_clean_text,
)
