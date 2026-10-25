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
    split_on_numbered_dot,
    split_on_paragraph,
    starts_with,
)


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    return text


_Trimmer = build_simple_markers(
    "## **Introduction", "8. If necessary, withdrawing from one"
)

_Splitters = ChunkSplitters(primary=split_on_numbered_dot, fallback=split_on_paragraph)

BusinessPlan = ToolBelt(
    document="Business Plan Guidance",
    hierarchy="guidance",
    sectors=fixed_sectors(LICENCE_CLASSES),
    input_url="https://www.iomfsa.im/media/3511/business-plan-guidance.pdf",
    pdf_path=build_pdf_path("rule_book"),
    trimmer=_Trimmer,
    header_matchers=[
        starts_with(["## **", "## **APPENDIX"]),
        lambda line: line.startswith("##") and line[3].isdigit(),
    ],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
