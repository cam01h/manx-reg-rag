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
    base_def_line,
    base_double_def_line,
    base_false_double_def,
    base_header_cleaner,
    base_text_cleaner,
    rejoin_page_breaks_with_marker,
    replace_from_dict,
    split_on_bracketed_num,
    starts_with,
    strip_footnote_bullets,
    strip_footnote_markers,
)

PENALTY_TABLE_RAW = (
    "|**Table**||\n"
    "|---|---|\n"
    "|**CIVIL PENALTY**|**Amount of penalty**|\n"
    "|**Level 1**<br>A penalty may be imposed at this level if the Authority is<br>satisfied that none of the factors specified in regulation 5(3)<br>is present.|Up to 5% of the relevant<br>person's income|\n"
    "|**Level 2**<br>A penalty may be imposed at this level if the Authority is<br>satisfied that any of the factors listed in regulation 5(3) is<br>present.|Up to 8% of the relevant<br>person's income|"
)

PENALTY_TABLE_CLEAN = (
    "[The following is a table with columns: penalty level, description, maximum amount]\n"
    "Civil Penalty\n"
    "Level 1 - A penalty may be imposed at this level if the Authority is satisfied that none of the factors specified in regulation 5(3) is present. Up to 5% of the relevant person's income\n"
    "Level 2 - A penalty may be imposed at this level if the Authority is satisfied that any of the factors listed in regulation 5(3) is present. Up to 8% of the relevant person's income"
)

TERROR_CIV_PEN_REPLACEMENT_DICT = {
    PENALTY_TABLE_RAW: PENALTY_TABLE_CLEAN,
    "## **CIVIL PENALTIES**": "",
    "Regulation 5": "",
    "## **Table**": "",
}


def terror_civ_pen_text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = rejoin_page_breaks_with_marker(text)
    text = strip_footnote_bullets(text)
    text = strip_footnote_markers(text)
    text = replace_from_dict(text, TERROR_CIV_PEN_REPLACEMENT_DICT)
    return text


TerrorCivPenMarkers = SectionMarkers(
    start=starts_with(["## **3 Interpretation"]),
    end=starts_with(["Level 2 - A penalty may"]),
)

TerrorCivPenDefMarkers = SectionMarkers(
    start=starts_with(['- " **accounting year']),
    end=starts_with(['- " **senior management']),
)

TerrorCivPenDefTools = DefinitionTools(
    section_markers=[TerrorCivPenDefMarkers],
    is_definition_line=starts_with(['- " **']),
    is_double_def_line=base_double_def_line,
    is_false_dub_def=base_false_double_def,
)

TerrorCivPenSplitters = ChunkSplitters(
    primary=split_on_bracketed_num, fallback=split_on_bracketed_num
)

TerrorCivPen = ToolBelt(
    document="The Terrorism and Crime act 2008",
    hierarchy="secondary legislation",
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/SUBORDINATE/2019/2019-0201/2019-0201_1.pdf",
    pdf_path=PROJECT_ROOT / "data/raw/custom/terror_civ_pen.pdf",
    use_ocr=True,
    pdf_handlers=None,
    trimmer=TerrorCivPenMarkers,
    header_matchers=[
        lambda line: (
            line.startswith("## **")
            and line[5].isdigit()
            or line.startswith("## **SCHEDULE")
        ),
    ],
    definition_tools=TerrorCivPenDefTools,
    clean_text=terror_civ_pen_text_cleaner,
    re_pack_splitters=TerrorCivPenSplitters,
    clean_body=base_body_cleaner,
    clean_header=base_header_cleaner,
    min_body_len=40,
)
