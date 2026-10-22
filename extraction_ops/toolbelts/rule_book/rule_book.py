import re

from config import PROJECT_ROOT
from core.sectors import ALL_SECTORS
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
    fixed_sectors,
    in_line,
    replace_from_dict,
    split_on_bracketed_num,
    starts_with,
    strip_footnote_markers,
)

from .rule_book_flattener import (
    fix_rule_3_24_table_order,
    flatten_appendix_2_table,
    flatten_appendix_3,
    flatten_appendix_4_table_b,
    flatten_definitions_table,
    flatten_rule_book_tables,
    strip_appendix_page_heads,
)
from .rule_book_handler import (
    rule_book_unbox_single_row_note_tables,
)

_RUNNING_HEAD = re.compile(
    r"^(?:"
    r"## (?:c SD No\.2016/0264 Page \d+|Page \d+ SD No\.2016/0264 c)"
    r"|(?:SCHEDULE|Index) Financial Services Rule Book 2016"
    r"|Financial Services Rule Book 2016(?: SCHEDULE| Index)?"
    r"|\(Rule [\d.]+\)(?: Financial Services Rule Book 2016)?"
    r"|\d{1,2} (?:SD \d+/\d+|AT \d+ of \d{4}|\d{4} c\.\d+)"
    r")[ \t]*$\n?",
    re.MULTILINE,
)

_REPLACEMENT_DICT = {
    "thatperson": "that person",
    "theperson": "the person",
    "offexchange": "off-exchange",
    "subparagraph": "sub-paragraph",
}


def fix_italics_spacing(text: str) -> str:
    return re.sub(r"([A-Za-z])_(?=[A-Z])", r"\1 _", text)


def typo_fix_on_icaap(text: str) -> str:
    return text.replace(
        '"internal capital adequacy assessment" process"',
        '"internal capital adequacy assessment process"',
    )


def _clean_text(text: str) -> str:
    text = base_text_cleaner(text)
    text = fix_italics_spacing(text)
    text = flatten_rule_book_tables(text)
    text = fix_rule_3_24_table_order(text)
    text = flatten_definitions_table(text)
    text = flatten_appendix_2_table(text)
    text = flatten_appendix_3(text)
    text = flatten_appendix_4_table_b(text)
    text = strip_appendix_page_heads(text)
    text = typo_fix_on_icaap(text)  # typo in orgional
    text = _RUNNING_HEAD.sub("", text)
    text = strip_footnote_markers(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    return text


TemplateMarkers = SectionMarkers(
    start=starts_with(["**1** **Title**"]),
    end=starts_with(["not exercised by the licenceholder."]),
)

TemplateDefTools = DefinitionTools(
    section_markers=[TemplateMarkers],
    is_definition_line=base_def_line,
    is_double_def_line=base_double_def_line,
    is_false_dub_def=base_false_double_def,
)

TemplateSplitters = ChunkSplitters(
    primary=split_on_bracketed_num, fallback=split_on_bracketed_num
)

RuleBook = ToolBelt(
    document="Financial Services Rule Book 2016",
    hierarchy="secondary legislation",
    sectors=fixed_sectors(ALL_SECTORS),
    input_url="https://www.iomfsa.im/media/1470/financialservicesrulebook20131.pdf",
    pdf_path=PROJECT_ROOT / "data/raw/custom/rule_book.pdf",
    use_ocr=True,
    use_layout=False,
    pdf_handlers=[rule_book_unbox_single_row_note_tables],
    trimmer=TemplateMarkers,
    header_matchers=[in_line(["header"])],
    definition_tools=TemplateDefTools,
    clean_text=_clean_text,
    re_pack_splitters=TemplateSplitters,
    clean_body=base_body_cleaner,
    clean_header=base_header_cleaner,
    min_body_len=40,
)
