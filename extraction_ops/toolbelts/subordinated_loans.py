from core.sectors import NON_BANK
from extraction_ops.models import ChunkSplitters, ToolBelt
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    replace_from_dict,
    split_on_paragraph,
    split_on_paragraph_not_list,
    starts_with,
)

_REPLACEMENT_DICT = {
    # hyphen lost at a line wrap
    "selffinancing": "self-financing",
}


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    return text


_Trimmer = build_simple_markers(
    "## **STATUS OF GUIDANCE", "This proforma agreement has been prepared specifically"
)

_Splitters = ChunkSplitters(
    primary=split_on_paragraph_not_list, fallback=split_on_paragraph
)

# rule 2.30: Class 2, 3, 4, 5, 8(2)(a) or 8(4) (Rule Book sectors map it to NON_BANK)
SubordinatedLoans = ToolBelt(
    document="Guidance on Rule 2.30 and Appendix 3 (Note 4) - Qualifying Subordinated Loans",
    hierarchy="guidance",
    sectors=fixed_sectors(NON_BANK),
    input_url="https://www.iomfsa.im/media/1722/qualifyingsubordinatedloans.pdf",
    pdf_path=build_pdf_path("subordinated_loans"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[starts_with(["## **"])],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
