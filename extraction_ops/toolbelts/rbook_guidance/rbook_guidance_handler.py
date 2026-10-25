import logging
from pathlib import Path

import fitz

logger = logging.getLogger(__name__)

"""<=== UNBOX ONE-ROW TABLES ===>"""

# Same problem as the Rule Book: in layout-off mode pymupdf4llm drops a table that has a
# single row. Two rules fill a whole page on their own (2.30 on page 5, 3.12 on page 11), so
# their page is one box with no row lines inside it and the text disappears. Removing the
# borders keeps the text, which then comes through as plain lines (see promote_unboxed_rules).
#
# Rows are counted from the horizontal border lines that span the box: a one-row table only
# has its top and bottom edge.
_EXPECTED_ONE_ROW_TABLES = 2
_MIN_TABLE_WIDTH = 500  # pt - skips the logo and the boxes around title words on page 1
_BORDER_MARGIN = 2  # pt - the borders are thin filled rectangles on the box edge
_SAME_LINE = 2  # pt - top/bottom edges are drawn as two rects a fraction apart


def _row_count(page: fitz.Page, box: fitz.Rect) -> int:
    edges: list[float] = []
    for drawing in page.get_drawings():
        rect = drawing["rect"]
        if box.contains(rect) and rect.width > box.width * 0.6 and rect.height < 3:
            edges.append((rect.y0 + rect.y1) / 2)
    edges.sort()
    lines = [y for i, y in enumerate(edges) if i == 0 or y - edges[i - 1] > _SAME_LINE]
    return len(lines) - 1


def _one_row_tables(page: fitz.Page) -> list[fitz.Rect]:
    boxes: list[fitz.Rect] = []
    for box in page.cluster_drawings():
        if box.width > _MIN_TABLE_WIDTH and _row_count(page, box) == 1:
            boxes.append(box)
    return boxes


def rbook_guidance_unbox_one_row_tables(path: Path) -> None:
    logger.info("Removing borders from one-row tables")
    doc = fitz.open(path)

    # pass 1: find every target before changing anything
    targets: list[tuple[int, fitz.Rect]] = []
    for page_number, page in enumerate(doc):
        for box in _one_row_tables(page):
            targets.append((page_number, box))

    if not targets:
        logger.warning("no one-row tables found - PDF already handled?")
        doc.close()
        return
    if len(targets) != _EXPECTED_ONE_ROW_TABLES:
        # any other count means the document has changed - check before trusting the output
        logger.error(
            "expected [%d] one-row tables, found [%d]",
            _EXPECTED_ONE_ROW_TABLES,
            len(targets),
        )
        raise ValueError(
            f"expected {_EXPECTED_ONE_ROW_TABLES} one-row tables, found {len(targets)}"
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
        logger.debug("unboxed one-row table on page [%d]", page_number + 1)

    tmp_path = path.with_suffix(".tmp.pdf")
    doc.save(tmp_path, garbage=4, deflate=True)
    doc.close()
    tmp_path.replace(path)
