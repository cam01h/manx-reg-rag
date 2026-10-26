from extraction_ops.models import ChunkSplitters, ToolBelt
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    replace_from_dict,
    split_on_paragraph,
    starts_with,
)

from .rule_summary_flattener import (
    flatten_summary_tables,
    rule_sectors,
    strip_summary_banner,
)

_HEADER = ("Event", "Rule", "Action", "Timing of communication with Authority")

_REPLACEMENT_DICT = {
    # the left edge of the first table is cut off on page 1
    "|**T 1 - Introductory**||||": "|**PART 1 - Introductory**||||",
    "|irmation of oral notification|": "|Confirmation of oral notification|",
    "|mencement of regulated activities|": "|Commencement of regulated activities|",
    # typo in the source, rule 7.20 is voluntary winding up
    "|Voluntary winding up|7.120|": "|Voluntary winding up|7.20|",
    # words run together in the table cells
    "(ii)from": "(ii) from",
    "(d)before re-domicilinga subsidiaryto anotherjurisdiction": "(d) before re-domiciling a subsidiary to another jurisdiction",
    "Authoritywith a copyof the amendedplan": "Authority with a copy of the amended plan",
    "daysin advanceif": "days in advance if",
    "anyother serious disciplinaryaction": "any other serious disciplinary action",
    "anyshares": "any shares",
    "bythis": "by this",
    "duringthat calendarquarter": "during that calendar quarter",
    "daysfollowingthe": "days following the",
    "existingemployees": "existing employees",
    "in(c)": "in (c)",
    "informationprovided underparagraph(1)": "information provided under paragraph (1)",
    "monthperiod": "month period",
}


def _render_row(cells: list[str]) -> tuple[str, list[str]]:
    event, rule, action, timing = cells
    # a full stop before the "; " that joins the cells reads badly
    action = action.rstrip(".")
    # the Appendix 3 rows are notes ("Note 4"), not rules
    ref = rule if rule.startswith("Note") else f"Rule {rule}"
    line = f"{ref} ({event}) - action: {action}; timing of communication with the Authority: {timing}"
    return f"{rule} - {event}", [line]


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    text = strip_summary_banner(text)
    text = flatten_summary_tables(text, _HEADER, 1, _render_row)
    return text


_Trimmer = build_simple_markers(
    "## **Financial Services Rule Book 2016", "Note 17 (Exceptional and extraordinary"
)

_Splitters = ChunkSplitters(primary=split_on_paragraph, fallback=split_on_paragraph)

# one row per rule, each tagged with that rule's sectors from the Rule Book map
ConsentNotify = ToolBelt(
    document="Financial Services Rule Book 2016 - Consent and Information Summary Table",
    hierarchy="guidance",
    sectors=rule_sectors,
    input_url="https://www.iomfsa.im/media/1540/consentandinformationsummarytabl.pdf",
    pdf_path=build_pdf_path("consent_notify"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[starts_with(["## **"]), starts_with(["### **"])],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
