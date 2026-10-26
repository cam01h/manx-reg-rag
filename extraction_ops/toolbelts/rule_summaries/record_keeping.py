from extraction_ops.models import ChunkSplitters, ToolBelt
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    rejoin_page_breaks,
    replace_from_dict,
    split_on_paragraph,
    starts_with,
    strip_footnote_bullets,
)

from .rule_summary_flattener import (
    flatten_summary_tables,
    rule_sectors,
    strip_summary_banner,
)

_HEADER = ("Rule", "Summary of cover", "Applies to")

_REPLACEMENT_DICT = {
    # footnotes are moved inline at their marker; the footnote lines are then stripped
    "licenceholders[1] to": "licenceholders [Footnote: The Rule Book applies to every licenceholder except those licensed to carry on regulated activities of Class 1(3) or Class 6. In addition, this piece of guidance does not apply to Professional Officers.] to",
    "agreements[2] .": 'agreements [Footnote: The Electronic Transactions Act further extends this by statute to "a transaction of a non-commercial nature".].',
    "_General Data Protection Regulation_ ,": "_General Data Protection Regulation_,",
    # heading that lost its "##"
    "**Table B - Rules which set out more specific requirements**": "## **Table B - Rules which set out more specific requirements**",
    # words run together in the table cells
    "onlybasis": "only basis",
    "or(12)": "or (12)",
    "thirdparties": "third parties",
    "timelymanner": "timely manner",
    "trainingrecord": "training record",
    "8(3_) _": "8(3)",
    "8.5(5)Continuing": "8.5(5) Continuing",
}


def _render_row(cells: list[str]) -> tuple[str, list[str]]:
    rule, cover, applies_to = cells
    # a full stop before the "; " that joins the cells reads badly
    cover = cover.rstrip(".")
    line = f"Rule {rule} - summary of cover: {cover}; applies to: {applies_to}"
    return rule, [line]


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    text = strip_summary_banner(text)
    text = flatten_summary_tables(text, _HEADER, 0, _render_row)
    text = strip_footnote_bullets(text)
    # the intro paragraph runs over a page break with footnote 1 in between
    text = rejoin_page_breaks(text)
    return text


_Trimmer = build_simple_markers(
    "## **Financial Services Rule Book 2016", "Rule 8.58 Retention of client records"
)

_Splitters = ChunkSplitters(primary=split_on_paragraph, fallback=split_on_paragraph)

# one row per rule, each tagged with that rule's sectors from the Rule Book map
RecordKeeping = ToolBelt(
    document="Financial Services Rule Book 2016 - Rules relating to record keeping",
    hierarchy="guidance",
    sectors=rule_sectors,
    input_url="https://www.iomfsa.im/media/1696/824and825recordkeeping.pdf",
    pdf_path=build_pdf_path("record_keeping"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[starts_with(["## **"]), starts_with(["### **"])],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
