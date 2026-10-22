import logging
import re
from pathlib import Path

import fitz

logger = logging.getLogger(__name__)

"""<=== UNBOX ONE-ROW NOTE TABLES (APPENDIX 3) ===>"""

# In layout-off mode pymupdf4llm drops tables that have a single row. Two of Appendix 3's
# notes are the last row of a notes table that runs onto the next page, leaving a one-row
# table on its own: Note 4 (page 206) and Note 5 (page 208). Removing their borders keeps
# the text but stops it being read as a table, so it comes through as plain text.
#
# The boxes are found with cluster_drawings() (groups a page's border lines into boxes),
# not find_tables(): importing pymupdf4llm switches its layout model on, which changes what
# find_tables() reports - with it on, the page 208 table is not detected at all.
# A one-row note table is a box that contains exactly one "Note N" label; every other
# notes table holds several.
_NOTE_LABEL = re.compile(r"^Note \d+$")
_EXPECTED_NOTE_TABLES = 2
_BORDER_MARGIN = 2  # pt - the borders are thin filled rectangles on the box edge


def _note_labels(page: fitz.Page) -> list[fitz.Rect]:
    labels: list[fitz.Rect] = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = "".join(span["text"] for span in line["spans"]).strip()
            if _NOTE_LABEL.match(text):
                labels.append(fitz.Rect(line["bbox"]))
    return labels


def _single_note_boxes(page: fitz.Page) -> list[fitz.Rect]:
    labels = _note_labels(page)
    if not labels:
        return []
    boxes: list[fitz.Rect] = []
    for box in page.cluster_drawings():
        inside = [label for label in labels if box.contains(label)]
        if len(inside) == 1:
            boxes.append(box)
    return boxes


def rule_book_unbox_single_row_note_tables(path: Path) -> None:
    logger.info("Removing borders from one-row note tables")
    doc = fitz.open(path)

    # pass 1: find every target before changing anything
    targets: list[tuple[int, fitz.Rect]] = []
    for page_number, page in enumerate(doc):
        for box in _single_note_boxes(page):
            targets.append((page_number, box))

    if not targets:
        # --handle-pdfs edits the PDF in place, so a second run finds nothing left to do
        logger.warning("no one-row note tables found - PDF already handled?")
        doc.close()
        return
    if len(targets) != _EXPECTED_NOTE_TABLES:
        # any other count means the document has changed - check before trusting the output
        logger.error(
            "expected [%d] one-row note tables, found [%d]",
            _EXPECTED_NOTE_TABLES,
            len(targets),
        )
        raise ValueError(
            f"expected {_EXPECTED_NOTE_TABLES} one-row note tables, found {len(targets)}"
        )

    # pass 2: remove the borders, keep the text and images
    margin = (-_BORDER_MARGIN, -_BORDER_MARGIN, _BORDER_MARGIN, _BORDER_MARGIN)
    for page_number, box in targets:
        page = doc[page_number]
        page.add_redact_annot(box + margin)
        page.apply_redactions(
            images=fitz.PDF_REDACT_IMAGE_NONE,
            graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
            text=fitz.PDF_REDACT_TEXT_NONE,
        )
        logger.debug("unboxed note table on page [%d]", page_number + 1)

    tmp_path = path.with_suffix(".tmp.pdf")
    doc.save(tmp_path, garbage=4, deflate=True)
    doc.close()
    tmp_path.replace(path)
