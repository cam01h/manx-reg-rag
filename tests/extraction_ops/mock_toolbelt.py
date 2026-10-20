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
    fixed_sectors,
    in_line,
    split_on_bracketed_letter,
    split_on_bracketed_num,
    starts_with,
)


def clean_text(text: str) -> str:
    text = base_text_cleaner(text)
    return text


TestDefMarkers = SectionMarkers(
    start=in_line(
        ["definition0", "definition1", "definition2", "definition3", "definition4"]
    ),
    end=in_line(
        ["definition5", "definition6", "definition7", "definition8", "definition9"]
    ),
)


TestDefs = DefinitionTools(
    section_markers=[TestDefMarkers],
    is_definition_line=base_def_line,
    is_double_def_line=base_double_def_line,
    is_false_dub_def=base_false_double_def,
)

TestTrimmer = SectionMarkers(
    start=in_line(["chunks0", "chunks1", "chunks2", "chunks3", "chunks4"]),
    end=in_line(["chunks5", "chunks6", "chunks7", "chunks8", "chunks9"]),
)

TestSplitters = ChunkSplitters(
    primary=split_on_bracketed_num,
    fallback=split_on_bracketed_letter,
)

TestToolBelt = ToolBelt(
    document="test model",
    hierarchy="placeholder",
    sectors=fixed_sectors(tuple("test_sector")),
    input_url="https://fake.url",
    pdf_path=PROJECT_ROOT / "fake/path.txt",
    use_ocr=True,
    pdf_handlers=None,
    trimmer=TestTrimmer,
    header_matchers=[starts_with(["##"]), starts_with(["**"])],
    definition_tools=TestDefs,
    clean_text=clean_text,
    re_pack_splitters=TestSplitters,
    clean_body=base_body_cleaner,
    clean_header=base_header_cleaner,
    min_body_len=40,
)
