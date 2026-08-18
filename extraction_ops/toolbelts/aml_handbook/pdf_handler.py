import re
from pathlib import Path
from typing import Any, cast
import fitz
import logging

logger = logging.getLogger(__name__)

"""<=== REMOVAL OF MARGIN CITATIONS ===>"""

MARGIN_RIGHT_EDGE = 120.0
MARGIN_FONT_SIZE = 8.1
LARGE_MARGIN_FONT_SIZE = 12.5

# citation labels: "Code", "POCA", "ATCA", etc. at the start of a fragment
CITATION_PREFIX = re.compile(r"^(?:Code|POCA|ATCA|TOCFRA|DBROA|POC|IA)\b")
# a fragment that's purely numbers/punctuation, no real words at all
PURE_CITATION_SHAPE = re.compile(r"^[\d\(\)\[\]\,\.\s\-\u2013]+$")
# guards: protect these even when they're small and margin-confined
TOC_NUMBER_SHAPE = re.compile(r"^\d+\.(?:\d+)?$")  # bare "1.1", "4."
GLOSSARY_YEAR_SHAPE = re.compile(r"^\d{4}\)?,?$")  # "2011", "2023)"


def _is_margin_citation(text: str, x1: float, size: float) -> bool:
    if x1 >= MARGIN_RIGHT_EDGE:
        return False
    if size <= MARGIN_FONT_SIZE:
        return True
    if size <= LARGE_MARGIN_FONT_SIZE:
        if TOC_NUMBER_SHAPE.match(text) or GLOSSARY_YEAR_SHAPE.match(text):
            return False
        if CITATION_PREFIX.match(text) or PURE_CITATION_SHAPE.match(text):
            return True
    return False


def handbook_redact_margin_citations(path: Path) -> None:
    logger.info("Redacting margin citations")
    doc = fitz.open(path)
    for page in doc:
        page_dict = cast(dict[str, Any], page.get_text("dict"))
        rects = []
        for block in page_dict["blocks"]:
            if block["type"] != 0:  # 0 = text block, 1 = image
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    x0, y0, x1, y1 = span["bbox"]
                    text = span["text"].strip()
                    if not text:
                        continue
                    size = round(span["size"], 2)
                    if _is_margin_citation(text, x1, size):
                        rects.append(fitz.Rect(x0, y0, x1, y1))
        for rect in rects:
            page.add_redact_annot(rect)
        if rects:
            page.apply_redactions()
            logger.debug("[%d] margin quotes redacted", len(rects))

    tmp_path = path.with_suffix(".tmp.pdf")
    doc.save(tmp_path, garbage=4, deflate=True)
    doc.close()
    tmp_path.replace(path)


"""<=== REMOVAL OF LEGISLATION QUOTES ===>"""

LEGEND_COLOURS = [
    (0.871, 0.918, 0.965),  # AML/CFT Code 2019
    (1.0, 0.949, 0.8),  # POCA 2008
    (0.886, 0.941, 0.851),  # DBROA 2015
    (0.984, 0.898, 0.839),  # AML/CFT (Civil Penalties Regulations) 2019
]
COLOUR_TOLERANCE = (
    0.02  # per channel - exact == fails, confirmed ~0.004 drift in the wild
)
MIN_QUOTE_WIDTH = (
    300  # real quotes measured at 408pt; the sector-table false positive was 208-218pt
)


def _is_channel_match(colour: tuple[float, float, float]) -> bool:
    return any(
        all(abs(lc[i] - colour[i]) <= COLOUR_TOLERANCE for i in range(3))
        for lc in LEGEND_COLOURS
    )


def _is_quote_match(drawing: dict[str, Any]) -> bool:
    if drawing.get("fill") is None:
        return False
    if not _is_channel_match(drawing["fill"]):
        return False
    box = drawing["rect"]
    width = box[2] - box[0]
    return width >= MIN_QUOTE_WIDTH


def handbook_redact_legislation_quoted(path: Path) -> None:
    logger.info("Redacting Code quotes in the handbook")
    doc = fitz.open(path)
    for page in doc:
        quotes_for_redaction = []
        drawings = page.get_drawings()
        for drawing in drawings:
            if _is_quote_match(drawing):
                quotes_for_redaction.append(drawing["rect"])
        for quote in quotes_for_redaction:
            page.add_redact_annot(quote)
        if quotes_for_redaction:
            page.apply_redactions()
            logger.debug("[%d] quotations redacted", len(quotes_for_redaction))

    tmp_path = path.with_suffix(".tmp.pdf")
    doc.save(tmp_path, garbage=4, deflate=True)
    doc.close()
    tmp_path.replace(path)


"""<=== REMOVAL OF LEGISLATION QUOTES ===>"""

DIVIDER_MAX_LENGTH = 200  # in chars


def handbook_remove_cover_and_dividers(path: Path) -> None:
    logger.info("Redacting handbook cover pages and dividers")
    doc = fitz.open(path)
    to_delete = [0] + [
        p
        for p in range(1, len(doc))
        if len(cast(str, doc[p].get_text()).strip()) < DIVIDER_MAX_LENGTH
    ]
    for p in sorted(to_delete, reverse=True):
        doc.delete_page(p)
    tmp_path = path.with_suffix(".tmp.pdf")
    doc.save(tmp_path, garbage=4, deflate=True)
    doc.close()
    tmp_path.replace(path)
