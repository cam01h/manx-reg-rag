import logging
import re

from core.sectors import ALL_SECTORS
from extraction_ops.models import ChunkSplitters, ToolBelt
from extraction_ops.toolbelts.fiu.fiu_shared import (
    FIU_GUIDANCE,
    drop_picture_markers,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    replace_from_dict,
    split_on_paragraph_not_list,
    split_on_paragraph_or_list_item,
    starts_with,
)

logger = logging.getLogger(__name__)

"""<=== QUESTION AND ANSWER TABLES ===>"""

# Every FAQ is a row of a two column table (Question | Response) that runs over six pages.
# Each row becomes a "### **question**" heading with the response as its body, so every
# question is its own chunk.

_TABLE_ROW = re.compile(r"^\|.*\|[ \t]*$", re.MULTILINE)
_SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")
_TITLE_CELLS = {"Question", "Response", "Consent Request Frequently Asked Questions"}
# a line ending a sentence or an introduction starts a new paragraph
_ENDS_PARAGRAPH = re.compile(r"[.:?!)]$")

_EXPECTED_QUESTIONS = 18


def _cells(row: str) -> list[str]:
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    return [c for c in cells if c and not _SEPARATOR_CELL.match(c)]


def _plain(cell: str) -> str:
    # "A**Protected Disclosure**as per Section 153" - bold run into the words around it
    cell = re.sub(r"(?<=\w)\*\*(?=\w)", " ", cell)
    return cell.replace("**", "").strip()


def _reflow(cell: str) -> str:
    """Cell lines are the column's line wraps, not paragraphs. Lines are joined back up,
    with a new paragraph after a sentence ends and a list item for each bullet."""
    paragraphs: list[str] = []
    for line in (_plain(part) for part in cell.split("<br>")):
        if not line:
            continue
        bullet = line.startswith("•")
        if bullet:
            line = "- " + line.lstrip("• ").strip()
        if (
            not paragraphs
            or bullet
            or line == "Example"
            or _ENDS_PARAGRAPH.search(paragraphs[-1])
            or paragraphs[-1] == "Example"
        ):
            paragraphs.append(line)
        else:
            paragraphs[-1] = f"{paragraphs[-1]} {line}"
    return "\n\n".join(paragraphs)


def faq_tables_to_sections(text: str) -> str:
    def repl(match: re.Match) -> str:
        out = []
        for row in _TABLE_ROW.findall(match.group()):
            cells = [c for c in _cells(row) if _plain(c) not in _TITLE_CELLS]
            if not cells:
                continue
            question = _plain(cells[0].replace("<br>", " "))
            answer = "\n\n".join(_reflow(c) for c in cells[1:])
            out.append(f"### **{question}**\n\n{answer}")
        return "\n\n".join(out) + "\n\n"

    text = re.sub(r"(?:^\|.*\|[ \t]*\n?)+", repl, text, flags=re.MULTILINE)
    found = len(re.findall(r"^### \*\*", text, flags=re.MULTILINE))
    if found != _EXPECTED_QUESTIONS:
        # any other count means a row was split or the document has changed
        logger.error("expected [%d] questions, found [%d]", _EXPECTED_QUESTIONS, found)
        raise ValueError(f"expected {_EXPECTED_QUESTIONS} questions, found {found}")
    return text


"""<=== CLEANER ===>"""

_REPLACEMENT_DICT = {
    # spaces left inside brackets by the bold markers
    "( **FIU** )": "(**FIU**)",
    '(" **FAQs** ")': '("**FAQs**")',
    '(" **IOMFCP** ")': '("**IOMFCP**")',
    # link labels left in the middle of a response
    "updated in June 2024:\n\nFIU SAR Guidance Please ensure": "updated in June 2024 (FIU SAR Guidance).\n\nPlease ensure",
    "for more information on suspicion:\n\nFIU Suspicion Guidance": "for more information on suspicion (FIU Suspicion Guidance).",
    '("IOM C&I").\n\nIOM C&I Sanctions Licences The consent regime': '("IOM C&I") (IOM C&I Sanctions Licences).\n\nThe consent regime',
    # typos in the source
    "the requestor in in possession": "the requestor is in possession",
    "create a table or matrix or the transactions": "create a table or matrix of the transactions",
}


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = drop_picture_markers(text)
    # page footer
    text = re.sub(r"^Official[ \t]*$\n?", "", text, flags=re.MULTILINE)
    text = faq_tables_to_sections(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    return text


_Trimmer = build_simple_markers(
    "## **Introduction",
    "Sharing a consent request/response without a clear legal basis",
)

_Splitters = ChunkSplitters(
    primary=split_on_paragraph_not_list, fallback=split_on_paragraph_or_list_item
)

ConsentFaqs = ToolBelt(
    document="FIU Consent Request Frequently Asked Questions (January 2026)",
    hierarchy=FIU_GUIDANCE,
    sectors=fixed_sectors(ALL_SECTORS),
    input_url="https://www.fiu.im/media/1254/isle-of-man-fiu-consent-faq-january-2026.pdf",
    pdf_path=build_pdf_path("fiu_consent_faqs"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[starts_with(["## **"]), starts_with(["### **"])],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
