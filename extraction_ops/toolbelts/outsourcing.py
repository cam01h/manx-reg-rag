from core.sectors import CLASS_4
from extraction_ops.models import ChunkSplitters, ToolBelt
from extraction_ops.toolbelts.rule_book.rule_book_sectors import RB_ALL
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    header_sectors,
    rejoin_page_breaks,
    replace_from_dict,
    replace_section,
    split_on_paragraph_not_list,
    split_on_paragraph_or_list_item,
    starts_with,
    strip_footnote_bullets,
)

# footnotes are moved inline at their marker; the footnote line is then stripped
_REPLACEMENT_DICT = {
    "including cloud computing[1]": "including cloud computing",
    "increasingly IT-reliant.": "increasingly IT-reliant [Footnote: Advice and guidance can be found on the website of the Cyber Security Centre for the Isle of Man (https://csc.gov.im).].",
    "other regulators.[2 ]": "other regulators [Footnote: See 'FG16/5: Guidance for firms outsourcing to the 'cloud' and other third party IT services' issued by the UK Financial Conduct Authority (https://www.fca.org.uk).].",
    # bullet character left inside a list item
    "- • ": "- ",
    # lead-in to the numbered headings that follow; on its own it is an empty chunk
    "The following principles are also relevant: \n\n": "",
    # appendix number and title on separate headings
    "## **APPENDIX 1** \n\n## **Typical questions": "## **APPENDIX 1 - Typical questions",
    "## **APPENDIX 2** \n\n## **Typical conditions": "## **APPENDIX 2 - Typical conditions",
    "## **APPENDIX 3** \n\n## **Use of overseas": "## **APPENDIX 3 - Use of overseas",
}


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_section(text, "## **Contents", "## **Relevant policies and rules")
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    text = strip_footnote_bullets(text)
    # "the Authority's principal / consideration" runs over a page break
    text = rejoin_page_breaks(text)
    return text


_Trimmer = build_simple_markers(
    "## **STATUS OF GUIDANCE", "- Ongoing contact with the client or beneficial owner"
)

_Splitters = ChunkSplitters(
    primary=split_on_paragraph_not_list, fallback=split_on_paragraph_or_list_item
)


def _is_sub_section(line: str) -> bool:
    # "## 1. Consent to outsource ..." / "## Details of the proposed outsourcing"
    return line.startswith("## ") and not line.startswith("## **")


_SECTOR_MATCHERS = {
    "Use of overseas company formation agents by Class 4": (CLASS_4,),
}

# rule 8.16: all classes except Class 8(1), 8(2)(b) or 8(3); not professional officers
Outsourcing = ToolBelt(
    document="Guidance on Rule 8.16 - Outsourcing and Delegation of Functions",
    hierarchy="guidance",
    sectors=header_sectors(_SECTOR_MATCHERS, RB_ALL),
    input_url="https://www.iomfsa.im/media/1541/guidancenoteonoutsourcing2012.pdf",
    pdf_path=build_pdf_path("outsourcing"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[starts_with(["## **"]), _is_sub_section],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
