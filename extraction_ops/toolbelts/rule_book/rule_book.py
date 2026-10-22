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
    split_on_bracketed_num,
    starts_with,
)

from .rule_book_flattener import (
    fix_rule_3_24_table_order,
    flatten_rule_book_tables,
)


def _clean_text(text: str) -> str:
    text = base_text_cleaner(text)
    text = flatten_rule_book_tables(text)
    text = fix_rule_3_24_table_order(text)
    return text


TemplateMarkers = SectionMarkers(start=starts_with(["start"]), end=starts_with(["end"]))

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
    pdf_handlers=None,
    trimmer=TemplateMarkers,
    header_matchers=[in_line(["header"])],
    definition_tools=TemplateDefTools,
    clean_text=_clean_text,
    re_pack_splitters=TemplateSplitters,
    clean_body=base_body_cleaner,
    clean_header=base_header_cleaner,
    min_body_len=40,
)
