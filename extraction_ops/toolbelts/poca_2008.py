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
    replace_from_dict,
    split_on_bracketed_letter,
    split_on_bracketed_num,
    starts_with,
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


def re_steps(text: str) -> str:
    text = base_text_cleaner(text)
    # ammendment markers
    text = re.sub(r" *\[(?:P\d{4}|\d{4})/[^\]]*\]", "", text)
    text = re.sub(r" *\[(?!Repealed\])[^\]]{20,}\]", "", text)
    # pymupdf artifacts that split "\n- (d) \n\n - paragraph"
    text = re.sub(r"- \((\d{1,2})\)\s*\n\s*\n\s*- (?=\w)", r"- (\1) ", text)
    text = re.sub(r"^> *(?:\*\*)?\d+(?:\*\*)? .*$\n?", "", text, flags=re.MULTILINE)
    text = strip_footnote_markers(text)
    text = replace_from_dict(text, POCA_REPLACEMENT_DICT)
    return text


PocaMarkers = SectionMarkers(
    start=starts_with(["## **PART 1 - CIVIL RECOVERY"]),
    end=starts_with(["   - (w) the Law Society of Scotland"]),
)

PocaIntroDefs = SectionMarkers(
    start=starts_with(['## **2 "Unlawful']),
    end=starts_with(["   - (b) it is not necessary to"]),
)

PocaChap2Defs = SectionMarkers(
    start=starts_with(['## **5 "Associated property']),
    end=in_line(["- (3) No property is to be treated"]),
)

PocaSec65Defs = SectionMarkers(
    start=starts_with(['- " **the Attorney General']),
    end=starts_with(['- " **value**']),
)

PocaSec149Defs = SectionMarkers(
    start=starts_with(['- (3) "disclosure"']),
    end=starts_with(["- (4A) In those sections"]),
)

PocaSec158P1Defs = SectionMarkers(
    start=starts_with(['- (2) "Criminal conduct']),
    end=starts_with(["   - (b) the alleged"]),
)

PocaSec158P2Defs = SectionMarkers(
    start=starts_with(['- (9) "Property"']),
    end=starts_with(['- (15) " **the data protection']),
)

PocaSec222ADefs = SectionMarkers(
    start=starts_with(['- "FATF" means']),
    end=starts_with(['- "relevant international']),
)

PocaSched4Defs = SectionMarkers(
    start=starts_with(['- the " **AML/CFT Code']),
    end=in_line(["- (e) participation in"]),
)

POCA_DEF_MARKERS = [
    PocaIntroDefs,
    PocaChap2Defs,
    PocaSec65Defs,
    PocaSec149Defs,
    PocaSec158P1Defs,
    PocaSec158P2Defs,
    PocaSec222ADefs,
    PocaSched4Defs,
]

PocaSplitters = ChunkSplitters(
    # primary=lambda text: re.split(r"\n(?=- )", text), fallback=split_on_paragraph
    primary=split_on_bracketed_letter,
    fallback=split_on_bracketed_num,
)

PocaDefinitionTools = DefinitionTools(
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
    is_double_def_line=base_double_def_line,
    is_false_dub_def=base_false_double_def,
)


Poca = ToolBelt(
    document="The Proceeds of Crime Act (POCA) 2008",
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/PRINCIPAL/2008/2008-0013/2008-0013_28.pdf",
    hierarchy="legislation",
    use_ocr=True,
    pdf_handlers=None,
    pdf_path=PROJECT_ROOT / "data/raw/custom/poca.pdf",
    trimmer=PocaMarkers,
    definition_tools=PocaDefinitionTools,
    header_matchers=[
        starts_with(["## **PART", "## **SCHEDULE"]),
        starts_with(["## CHAPTER"]),
        starts_with(["## _"]),
        lambda line: line.startswith("## **") and line[5].isdigit(),
    ],
    re_pack_splitters=PocaSplitters,
    clean_text=re_steps,
    clean_header=base_header_cleaner,
    clean_body=base_body_cleaner,
    min_body_len=40,
)
"""
    is_definition_line=lambda line: (
        '- **"' in line or '## **"' in line or line.startswith('**"')
    ),
    is_double_def_line=lambda segs: len(segs) == 5 and segs[2].strip() in ("or", "and"),
    is_false_dub_def=lambda segs: len(segs) == 5 and segs[2].strip() != "or",
"""
