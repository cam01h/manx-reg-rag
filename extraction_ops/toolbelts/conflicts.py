from core.sectors import LICENCE_CLASSES
from extraction_ops.models import (
    ChunkSplitters,
    ToolBelt,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    split_on_bracketed_letter,
    split_on_bracketed_num,
    starts_with,
)


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    return text


_Trimmer = build_simple_markers("start", "end")

_Splitters = ChunkSplitters(
    primary=split_on_bracketed_num, fallback=split_on_bracketed_letter
)

Conflicts = ToolBelt(
    document="Conflicts of Interest Policy - Guidance Note - Rule 8.9",
    hierarchy="guidance",
    sectors=fixed_sectors(LICENCE_CLASSES),
    input_url="https://www.iomfsa.im/media/1720/rule87conflictsofinterestjuly.pdf",
    pdf_path=build_pdf_path("conflicts"),
    trimmer=_Trimmer,
    header_matchers=[starts_with(["header"])],
    definition_tools=None,
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
