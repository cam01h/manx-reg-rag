from config import PROJECT_ROOT
from extraction_ops.models import (
    DefinitionTools,
    ToolBelt,
    ChunkSplitters,
    SectionMarkers,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_body_cleaner,
    base_header_cleaner,
    base_text_cleaner,
    split_on_bracketed_letter,
    split_on_bracketed_num,
    base_def_line,
    base_double_def_line,
    base_false_double_def,
)


def clean_text(text: str) -> str:
    text = base_text_cleaner(text)
    return text


TestDefMarkers = SectionMarkers(
    start=lambda line: line.startswith("placeholder"),
    end=lambda line: line.startswith("placeholder"),
)


TestDefs = DefinitionTools(
    section_markers=[TestDefMarkers],
    is_definition_line=base_def_line,
    is_double_def_line=base_double_def_line,
    is_false_dub_def=base_false_double_def,
)

TestTrimmer = SectionMarkers(
    start=lambda text: text.startswith("place holder"),
    end=lambda text: text.startswith("place holder"),
)

TestSplitters = ChunkSplitters(
    primary=split_on_bracketed_num,
    fallback=split_on_bracketed_letter,
)

TestToolBelt = ToolBelt(
    document="test model",
    hierarchy="placeholder",
    input_url="https://fake.url",
    pdf_path=PROJECT_ROOT / "fake/path.txt",
    use_ocr=True,
    pdf_handlers=None,
    trimmer=TestTrimmer,
    header_matchers=[
        lambda line: line.startswith("placeholder"),
        lambda line: line.startswith("placeholder"),
    ],
    definition_tools=TestDefs,
    clean_text=clean_text,
    re_pack_splitters=TestSplitters,
    clean_body=base_body_cleaner,
    clean_header=base_header_cleaner,
    min_body_len=40,
)
