import re

from core.sectors import CLASS_1
from extraction_ops.models import ChunkSplitters, ToolBelt
from extraction_ops.toolbelts.rule_book.rule_book_sectors import RB_ALL
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    header_sectors,
    replace_from_dict,
    split_on_paragraph,
    split_on_paragraph_not_list,
    starts_with,
    strip_footnote_bullets,
)

# footnotes carry real content (definitions, which F&P forms to use) so they are moved
# inline at their marker; the footnote lines themselves are then stripped
_REPLACEMENT_DICT = {
    "licenceholder[1] which": 'licenceholder [Footnote: "licenceholder" has the same meaning as in section 7(7) of the Financial Services Act 2008.] which',
    "subsidiaries[2] ;": 'subsidiaries [Footnote: "Subsidiary" is defined in the Financial Services Act 2008 principally by reference to section 1 of the Companies Act 1974.];',
    "new controllers[3] ;": "new controllers [Footnote: See Regulatory Guidance - Fitness and Propriety (especially Appendices 3 and 6)];",
    "Controlled Functions[4] ;": "Controlled Functions [Footnote: See Regulatory Guidance - Fitness and Propriety];",
    "their subsidiaries)[5] ;": "their subsidiaries) [Footnote: In very large groups, a selective chart showing the relevant entities can be supplied by mutual agreement];",
    # list item picked up as a header after the page break
    "## 6.2. Any changes to nominee companies.": "- 6.2. Any changes to nominee companies.",
    "assessment forms  for": "assessment forms for",
}


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    text = strip_footnote_bullets(text)
    # "in **appendix 1** ." -> "in appendix 1."
    text = re.sub(r"\*\* +([.,;:)])", r"**\1", text)
    return text


_Trimmer = build_simple_markers(
    "## **Introduction",
    "- Consideration of any change in the responsibilities of overseas regulators",
)

_Splitters = ChunkSplitters(
    primary=split_on_paragraph_not_list, fallback=split_on_paragraph
)

_NUMBERED_HEADER = re.compile(r"^## \*\*\d\. ")


def _is_numbered(line: str) -> bool:
    return bool(_NUMBERED_HEADER.match(line))


# Rules 7.3 to 7.8 between them apply to every Rule Book class; Appendix 1 is Class 1 only
_SECTOR_MATCHERS = {
    "Appendix 1": (CLASS_1,),
}

ChangeOwnership = ToolBelt(
    document="Guidance on Rules 7.3 to 7.8 - Changes in Ownership and Structure",
    hierarchy="guidance",
    sectors=header_sectors(_SECTOR_MATCHERS, RB_ALL),
    input_url="https://www.iomfsa.im/media/1727/74changesinownership.pdf",
    pdf_path=build_pdf_path("change_ownership"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[
        starts_with(
            [
                "## **Introduction",
                "## **STATUS OF GUIDANCE",
                "## **Information to be provided",
                "## **Appendix 1",
            ]
        ),
        _is_numbered,
    ],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
