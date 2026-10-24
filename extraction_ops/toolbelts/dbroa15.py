import re

from core.sectors import DESIGNATED_BUSINESSES
from extraction_ops.models import (
    ChunkSplitters,
    DefinitionTools,
    ToolBelt,
)
from extraction_ops.toolbelts.custom_flatteners import flatten_dbroa_schedule_table
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    rejoin_page_breaks,
    replace_from_dict,
    split_on_bracketed_letter,
    starts_with,
    strip_footnote_markers,
)

_REPLACEMENT_DICT = {
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


def _text_cleaner(text: str) -> str:
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
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    return text


_DbroaMarkers = build_simple_markers(
    "## **PART 1 - INTRODUCTORY**", "- (6) The factors set out"
)

_DbroaSec3DefMarkers = build_simple_markers(
    '- " **applicant** "', "- (l) any legislation in any other country"
)

_DbroaSchedule1DefMarkers = build_simple_markers(
    '- " **estate agent**', "- (e) participation in"
)

_DbroaDefTools = DefinitionTools(
    section_markers=[_DbroaSec3DefMarkers, _DbroaSchedule1DefMarkers],
    is_definition_line=starts_with(['- " **', '- (2) In this Act " **']),
)

_DbroaSplitters = ChunkSplitters(
    primary=lambda text: re.split(r"\n+(?=\s*(?:- )?\d+\.\s)", text),
    fallback=split_on_bracketed_letter,
)

Dbroa = ToolBelt(
    document="Designated Businesses (Registration and Oversight) Act 2015",
    hierarchy="primary legislation",
    sectors=fixed_sectors(DESIGNATED_BUSINESSES),
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/PRINCIPAL/2015/2015-0009/2015-0009_13.pdf",
    pdf_path=build_pdf_path("dbroa"),
    trimmer=_DbroaMarkers,
    header_matchers=[
        starts_with(["## **SCHEDULE"]),
        starts_with(["## **PART"]),
        starts_with(["## DIVISION"]),
        lambda line: line.startswith("## **") and line[5].isdigit(),
    ],
    definition_tools=_DbroaDefTools,
    clean_text=_text_cleaner,
    re_pack_splitters=_DbroaSplitters,
)
