import re

from core.sectors import ALL_SECTORS
from extraction_ops.models import ChunkSplitters, ToolBelt
from extraction_ops.toolbelts.fiu.fiu_shared import (
    FIU_GUIDANCE,
    close_punctuation_gaps,
    collapse_heading_spaces,
    demote_unnumbered_headings,
    drop_empty_bullets,
    drop_picture_markers,
    numbered_heading,
    strip_footnote_numbers,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    rejoin_page_breaks,
    replace_from_dict,
    split_on_paragraph_not_list,
    split_on_paragraph_or_list_item,
)

_REPLACEMENT_DICT = {
    # section 5's heading is set over two lines in a shaded bar; only its last words survive
    "## **Act 2016**": "## **5. Disclosing Information to the FIU Under Section 24 of the FIU Act 2016**",
    # a bold sentence that pymupdf4llm read as a heading, broken over three lines
    "## **It is important that every natural and legal person relevant to the narrative is uniquely** \n\n**identified and submitted as a 'subject'** . This enables the FIU to carry out searches and link SARs \n\nto related matters.": "**It is important that every natural and legal person relevant to the narrative is uniquely identified and submitted as a 'subject'.** This enables the FIU to carry out searches and link SARs to related matters.",
    # hyphens in links read as list markers
    "Authority - - - (https://www.iomfsa.im/media/3215/december 2023 handbook clean.pdf)": "Authority (https://www.iomfsa.im/media/3215/december-2023-handbook-clean.pdf)",
    "can be found - - - in the FIU Sanctions Reporting Guidance - https://fiu.im/media/1299/mlro sanctions reporting guidance-august-26.pdf .": "can be found in the FIU Sanctions Reporting Guidance - https://fiu.im/media/1299/mlro-sanctions-reporting-guidance-august-26.pdf.",
    "AntiTerrorism and Crime Act": "Anti-Terrorism and Crime Act",
    "anti-moneylaundering-guidance": "anti-money-laundering-guidance",
    "introduced on 1 August 2023 Regular telephone": "introduced on 1 August 2023 [Footnote: https://www.fiu.im/media/1189/mlro-sar-feedback-guidance.pdf]. Regular telephone",
}


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = drop_picture_markers(text)
    # footnotes are links to the legislation and FIU pages - the one with substance (the
    # feedback guidance) is moved inline by the dict
    text = re.sub(r"^> \d+ .*$\n?", "", text, flags=re.MULTILINE)
    text = strip_footnote_numbers(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    text = drop_empty_bullets(text)
    text = collapse_heading_spaces(text)
    text = close_punctuation_gaps(text)
    text = demote_unnumbered_headings(text)
    # "(Customs and Immigration retains / responsibility for ..." runs over a page break
    text = rejoin_page_breaks(text)
    return text


_Trimmer = build_simple_markers(
    "## **1. Introduction",
    "If you have a specific SAR(s) where you would like feedback",
)

_Splitters = ChunkSplitters(
    primary=split_on_paragraph_not_list, fallback=split_on_paragraph_or_list_item
)

SarGuidance = ToolBelt(
    document="FIU Guidance for Making Suspicious Activity Reports (and Other Disclosures) (August 2026)",
    hierarchy=FIU_GUIDANCE,
    sectors=fixed_sectors(ALL_SECTORS),
    input_url="https://www.fiu.im/media/1300/sar-guidance-updated-august-2026.pdf",
    pdf_path=build_pdf_path("fiu_sar_guidance"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[numbered_heading(1), numbered_heading(2), numbered_heading(3)],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
