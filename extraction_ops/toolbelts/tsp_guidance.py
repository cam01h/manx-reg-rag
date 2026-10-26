from core.sectors import CLASS_5
from extraction_ops.models import ChunkSplitters, ToolBelt
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    rejoin_page_breaks,
    split_on_paragraph,
    split_on_paragraph_not_list,
    starts_with,
)


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    # the nominee settlors paragraph runs over a page break
    text = rejoin_page_breaks(text)
    return text


_Trimmer = build_simple_markers(
    "## **Introduction", "Should you wish to discuss any matters relating to this paper"
)

_Splitters = ChunkSplitters(
    primary=split_on_paragraph_not_list, fallback=split_on_paragraph
)

# trustee and trust administration services
TspGuidance = ToolBelt(
    document="Guidelines on Expected Practice for Trust Service Providers",
    hierarchy="guidance",
    sectors=fixed_sectors((CLASS_5,)),
    input_url="https://www.iomfsa.im/media/1518/trustguidelinesonexpectedpractic.pdf",
    pdf_path=build_pdf_path("tsp_guidance"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[starts_with(["## **"])],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
