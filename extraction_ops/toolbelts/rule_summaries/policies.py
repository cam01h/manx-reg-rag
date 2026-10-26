from extraction_ops.models import ChunkSplitters, ToolBelt
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
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

_HEADER = ("Rule Title", "Rule", "Responsibility", "Applies To", "Comment")

# footnote 1 is moved inline at its marker; the footnote line is then stripped
_REPLACEMENT_DICT = {
    "appropriate under 8.47.1|": "appropriate under 8.47 [Footnote: The Authority's Consent and Notification Summary Table provides further information regarding the various types of events which licenceholders are required to inform the Authority of, either on a notification basis, or prior consent before an action can proceed basis.].|",
}


def _render_row(cells: list[str]) -> tuple[str, list[str]]:
    title, rule, responsibility, applies_to, comment = cells
    # a full stop before the "; " that joins the cells reads badly
    responsibility, applies_to = responsibility.rstrip("."), applies_to.rstrip(".")
    line = f"Rule {rule} ({title}) - responsibility: {responsibility}; applies to: {applies_to}; comment: {comment}"
    return f"{rule} - {title}", [line]


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    text = strip_summary_banner(text)
    text = flatten_summary_tables(text, _HEADER, 1, _render_row)
    text = strip_footnote_bullets(text)
    return text


_Trimmer = build_simple_markers(
    "## **Financial Services Rule Book 2016", "Rule 9.21 (Conflicts of Interest)"
)

_Splitters = ChunkSplitters(primary=split_on_paragraph, fallback=split_on_paragraph)

# one row per rule, each tagged with that rule's sectors from the Rule Book map
Policies = ToolBelt(
    document="Financial Services Rule Book 2016 - Rules relating to policies",
    hierarchy="guidance",
    sectors=rule_sectors,
    input_url="https://www.iomfsa.im/media/1538/rulebookobligationstomaintainpo.pdf",
    pdf_path=build_pdf_path("policies"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[starts_with(["## **"]), starts_with(["### **"])],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
