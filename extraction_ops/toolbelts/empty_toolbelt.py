from pathlib import Path
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
    in_line,
    split_on_bracketed_num,
    starts_with,
)


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

Template = ToolBelt(
    document="",
    hierarchy="",
    input_url="",
    pdf_path=Path("~/path/to.pdf"),
    use_ocr=True,
    pdf_handlers=None,
    trimmer=TemplateMarkers,
    header_matchers=[in_line(["header"])],
    definition_tools=TemplateDefTools,
    clean_text=base_text_cleaner,
    re_pack_splitters=TemplateSplitters,
    clean_body=base_body_cleaner,
    clean_header=base_header_cleaner,
    min_body_len=40,
)
