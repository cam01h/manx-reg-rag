import re
from config import PROJECT_ROOT
from extraction_ops.models import (
    ChunkSplitters,
    DefinitionTools,
    SectionMarkers,
    ToolBelt,
)
from extraction_ops.toolbelts.custom_flatteners import flatten_dbroa_schedule_table
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
    starts_with,
    strip_footnote_markers,
)

DBROA_REPLACEMENT_DICT = {
    # definition minipulation
    '## " **associate**': '- " **associate**',
    '\n## " **Commission** " [Repealed] \n': "",
    # pdf artifacts
    "requested, \n\nis guilty": "requested, is guilty",
    "the Authority, \n\nand must": "the Authority, and must",
    "\n1 SD 671/00 as amended by SD 850/02. \n": "",
    # header minipulation
    "## **SCHEDULE 1** \n\n[Section 4] \n\n## **DESIGNATED BUSINESSES": "## **SCHEDULE 1 - DESIGNATED BUSINESSES",
    "## **SCHEDULE 2** \n\n[Section 22(1)(b)] \n\n## **EXCEPTIONS": "## **SCHEDULE 2 - EXCEPTIONS",
}


def dbroa_text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = strip_footnote_markers(text)
    # fixes ## **2** \n\n ## **commencement** and similar
    text = re.sub(
        r"## \*\*(\d+[A-Z]?)\*\*\s*\n\s*## \*\*([^\n*]+)\*\*",
        r"## **\1 \2**",
        text,
    )
    text = rejoin_page_breaks(text)
    text = flatten_dbroa_schedule_table(text)
    text = replace_from_dict(text, DBROA_REPLACEMENT_DICT)
    return text


DbroaMarkers = SectionMarkers(
    start=starts_with(["## **PART 1 - INTRODUCTORY**"]),
    end=starts_with(["- (6) The factors set out"]),
)

DbroaSec3DefMarkers = SectionMarkers(
    start=starts_with(['- " **applicant** "']),
    end=in_line(["- (l) any legislation in any other country"]),
)

DbroaSchedule1DefMarkers = SectionMarkers(
    start=starts_with(['- " **estate agent**']),
    end=in_line(["- (e) participation in"]),
)

DbroaDefTools = DefinitionTools(
    section_markers=[DbroaSec3DefMarkers, DbroaSchedule1DefMarkers],
    is_definition_line=starts_with(['- " **', '- (2) In this Act " **']),
    is_double_def_line=base_double_def_line,
    is_false_dub_def=base_false_double_def,
)

DbroaSplitters = ChunkSplitters(
    primary=lambda text: re.split(r"\n+(?=\s*(?:- )?\d+\.\s)", text),
    fallback=split_on_bracketed_letter,
)

Dbroa = ToolBelt(
    document="Designated Businesses (Registration and Oversight) Act 2015",
    hierarchy="primary legislation",
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/PRINCIPAL/2015/2015-0009/2015-0009_13.pdf",
    pdf_path=PROJECT_ROOT / "data/raw/custom/dbroa.pdf",
    use_ocr=True,
    pdf_handlers=None,
    trimmer=DbroaMarkers,
    header_matchers=[
        starts_with(["## **SCHEDULE"]),
        starts_with(["## **PART"]),
        starts_with(["## DIVISION"]),
        lambda line: line.startswith("## **") and line[5].isdigit(),
    ],
    definition_tools=DbroaDefTools,
    clean_text=dbroa_text_cleaner,
    re_pack_splitters=DbroaSplitters,
    clean_body=base_body_cleaner,
    clean_header=base_header_cleaner,
    min_body_len=40,
)
