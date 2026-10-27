import functools
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import fitz

logger = logging.getLogger(__name__)

"""<=== FITZ STYLE LOOKUP FOR THE NRAs ===>"""

# Every NRA is built from the same InDesign template, so a line's font size, weight and
# colour say what it is far more reliably than pymupdf4llm's markdown, which marks every
# heading as "##". The md stays the source of the text and of where headings sit; fitz is
# only consulted to decide what a md line is (heading level, figure caption, pull quote)
# and to supply the correct spelling of headings that pymupdf4llm mangles ("Fi ure g").

# role values that are not heading levels
CAPTION = "caption"  # figure / table titles: kept as a bold body line
PULL_QUOTE = "pull_quote"  # large blue quotes repeating body text: dropped

MAROON = ("7d1538", "760d3b")
BLUE = ("0081a8",)
WHITE = ("ffffff",)

# running header and footer band, in points from the top of the A4 page
_HEADER_BAND = 50
_FOOTER_BAND = 760
# smaller than the 8pt table text: footnotes (6.8pt) and chart labels
_MIN_STREAM_SIZE = 7.5


@dataclass(frozen=True)
class StyledLine:
    page: int  # 1-based
    text: str
    size: float
    weight: str  # Light, Medium, Bold, Book, LightItalic ...
    colour: str  # hex, eg "7d1538"


@dataclass(frozen=True)
class StyleRule:
    role: int | str  # heading level (1 = top) or CAPTION / PULL_QUOTE
    min_size: float
    max_size: float
    weights: tuple[str, ...] = ()  # empty matches any weight
    colours: tuple[str, ...] = ()  # empty matches any colour
    text: Callable[[str], bool] | None = None  # extra condition on the line's text


def match_key(text: str) -> str:
    """Comparison key: footnote markers and everything but letters and digits removed."""
    text = re.sub(r"\[\s*\d+\s*\]", "", text)
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _weight(font: str) -> str:
    # "GillSansNova-LightItalic" -> "LightItalic", "GillSansNova-MediumItali" -> "MediumItalic"
    weight = font.split("-")[-1] if "-" in font else font
    return "MediumItalic" if weight == "MediumItali" else weight


def _line_text(line: dict) -> str:
    # superscript spans (flag bit 0) are footnote markers - left out of the text
    return "".join(s["text"] for s in line["spans"] if not s["flags"] & 1).strip()


@functools.cache
def styled_lines(pdf_path: Path) -> tuple[StyledLine, ...]:
    """All text on every page, with consecutive lines of one style merged into one entry,
    so a heading wrapped over two lines is a single StyledLine."""
    lines: list[StyledLine] = []
    with fitz.open(pdf_path) as doc:
        for page_no in range(1, doc.page_count + 1):
            page = doc.load_page(page_no - 1)
            current: list = []  # [style key, text, bottom y]
            for block in cast(dict[str, Any], page.get_text("dict"))["blocks"]:
                for line in block.get("lines", []):
                    spans = [s for s in line["spans"] if s["text"].strip()]
                    if not spans:
                        continue
                    main = max(spans, key=lambda s: len(s["text"].strip()))
                    key = (
                        round(main["size"], 1),
                        _weight(main["font"]),
                        f"{main['color']:06x}",
                    )
                    text = _line_text(line)
                    if not text:
                        continue
                    gap = line["bbox"][1] - current[2] if current else 0
                    if current and current[0] == key and gap < main["size"] * 1.6:
                        current[1] += " " + text
                        current[2] = line["bbox"][3]
                        continue
                    if current:
                        lines.append(StyledLine(page_no, current[1], *current[0]))
                    current = [key, text, line["bbox"][3]]
            if current:
                lines.append(StyledLine(page_no, current[1], *current[0]))
    logger.debug("[%d] styled lines read from [%s]", len(lines), pdf_path.name)
    return tuple(lines)


@dataclass(frozen=True)
class PageText:
    """A page's words as match keys, the text block each word belongs to, and each block's
    place in the page's reading order (see reading_ranks)."""

    words: tuple[str, ...]
    word_block: tuple[int, ...]  # index into block_rank for each word
    block_rank: tuple[int, ...]  # reading-order rank of each block


# the two text columns of the A4 template meet around x = 297
_GUTTER = (285, 310)


def reading_ranks(
    boxes: list[tuple[float, float, float, float]], separators: list[bool]
) -> list[int]:
    """Reading order for the template's two-column pages. A block crossing the gutter (a
    title, a figure, a full-width table) splits the page into horizontal bands; within a
    band the left column is read top to bottom, then the right. Neither pymupdf4llm's
    order nor the PDF's own content order gets this right on every page."""
    order = sorted(range(len(boxes)), key=lambda i: boxes[i][1])
    cuts = sorted(boxes[i][1] for i in order if separators[i])
    ranked: list[tuple[tuple, int]] = []
    for i in order:
        x0, y0, x1, _ = boxes[i]
        # band k holds the blocks between the k-th separator and the next; a separator is
        # read after the two columns above it
        band = sum(1 for cut in cuts if cut < y0 - 1)
        if separators[i]:
            ranked.append(((band, 2, y0), i))
        else:
            column = 0 if (x0 + x1) / 2 < sum(_GUTTER) / 2 else 1
            ranked.append(((band, column, y0), i))
    ranks = [0] * len(boxes)
    for rank, (_, i) in enumerate(sorted(ranked)):
        ranks[i] = rank
    return ranks


def _is_separator(bbox: tuple[float, float, float, float], spans: list[dict]) -> bool:
    crosses = bbox[0] < _GUTTER[0] and bbox[2] > _GUTTER[1]
    # pull quotes float across the columns without interrupting the text flow
    pull_quote = any(s["size"] >= 14 and f"{s['color']:06x}" in BLUE for s in spans)
    return crosses and not pull_quote


@functools.cache
def page_texts(pdf_path: Path) -> dict[int, PageText]:
    pages: dict[int, PageText] = {}
    with fitz.open(pdf_path) as doc:
        for page_no in range(1, doc.page_count + 1):
            page = doc.load_page(page_no - 1)
            words: list[str] = []
            word_block: list[int] = []
            boxes: list[tuple[float, float, float, float]] = []
            separators: list[bool] = []
            for block in cast(dict[str, Any], page.get_text("dict"))["blocks"]:
                start = len(words)
                spans = []
                for line in block.get("lines", []):
                    if not _HEADER_BAND < line["bbox"][1] < _FOOTER_BAND:
                        continue
                    spans.extend(line["spans"])
                    # footnotes and chart labels sit between the end of one page's text
                    # and the start of the next in the content order - left out
                    if max(s["size"] for s in line["spans"]) < _MIN_STREAM_SIZE:
                        continue
                    for word in _line_text(line).split():
                        key = match_key(word)
                        if key:
                            words.append(key)
                            word_block.append(len(boxes))
                if len(words) > start:
                    bbox = cast(tuple[float, float, float, float], tuple(block["bbox"]))
                    boxes.append(bbox)
                    separators.append(_is_separator(bbox, spans))
            ranks = reading_ranks(boxes, separators)
            pages[page_no] = PageText(tuple(words), tuple(word_block), tuple(ranks))
    return pages


def body_words(pdf_path: Path) -> tuple[str, ...]:
    """The whole document's words in content order."""
    return tuple(
        w for _, page in sorted(page_texts(pdf_path).items()) for w in page.words
    )


def rule_matches(rule: StyleRule, line: StyledLine) -> bool:
    if not rule.min_size <= line.size <= rule.max_size:
        return False
    if rule.weights and line.weight not in rule.weights:
        return False
    if rule.colours and line.colour not in rule.colours:
        return False
    return rule.text is None or rule.text(line.text)


def role_of(line: StyledLine, rules: list[StyleRule]) -> int | str | None:
    for rule in rules:
        if rule_matches(rule, line):
            # a score or rating ("0.7 High") in heading colours is never a heading
            if isinstance(rule.role, int) and is_rating(line.text):
                return None
            return rule.role
    return None


# text conditions used by the rules
def is_caption_text(text: str) -> bool:
    return bool(
        re.match(r"(?:Fig(?:ure)?|Key for|Case Stud|Typology)\b", text, re.IGNORECASE)
    )


_RATING = re.compile(
    r"^(?:[\d.]+\s*)?(?:very |close to )?(?:low|medium|high|excellent|nothing|"
    r"medium[- ]high|medium[- ]low)$",
    re.IGNORECASE,
)


def is_rating(text: str) -> bool:
    return bool(_RATING.match(text.strip()) or re.fullmatch(r"[\d.,%\s]+", text))


def is_short_heading(text: str) -> bool:
    """Short line, or one that is mostly capitals - not a sentence styled as a heading,
    and not a score or rating ("0.7 High") picked out in heading colours."""
    if is_rating(text):
        return False
    letters = [c for c in text if c.isalpha()]
    upper = sum(c.isupper() for c in letters) / len(letters) if letters else 0
    return len(text) <= 70 or upper >= 0.6


def is_capitals_heading(text: str) -> bool:
    # "CHAPTER 3" beside a chapter title is a label, not a heading of its own
    return text.isupper() and len(text) <= 60 and not re.match(r"CHAPTER\s+\d+$", text)


def numbered_section(text: str) -> bool:
    """'3.1 Terrorist Financing NRA' rather than '3. Introduction'"""
    return bool(re.match(r"\d+\.\d+", text))


# Rules shared by every NRA, most specific first. Levels:
#   1 chapter        divider pages, and 49pt titles numbered "3." or unnumbered
#   2 numbered title 49pt titles numbered "3.1"
#   3 section        27pt
#   4 sub-section    27pt italic
#   5 sub-heading    12-16pt maroon (short or mostly capitals) and 12pt blue capitals
#   6 run-in heading 9.5pt maroon medium, 9.5pt maroon capitals, grey medium
NRA_STYLE_RULES: list[StyleRule] = [
    StyleRule(CAPTION, 16, 21, ("Light",), BLUE, is_caption_text),
    StyleRule(CAPTION, 10.5, 15, ("Medium", "SemiBold"), BLUE, is_caption_text),
    StyleRule(PULL_QUOTE, 14, 26, ("Light", "Book", "Medium"), BLUE),
    StyleRule(1, 36, 70, ("Light", "Medium"), WHITE),
    StyleRule(2, 30, 60, ("Light",), MAROON, numbered_section),
    StyleRule(1, 30, 60, ("Light",), MAROON),
    StyleRule(4, 22, 30, ("LightItalic",), MAROON),
    StyleRule(3, 22, 30, ("Light",), MAROON),
    StyleRule(5, 11, 13, ("Light", "Medium"), MAROON, is_short_heading),
    StyleRule(5, 13, 17.5, ("Light", "Medium"), MAROON, is_short_heading),
    StyleRule(5, 11.5, 13, ("Light",), BLUE, lambda t: t.isupper()),
    StyleRule(6, 9, 10.5, ("Medium", "Bold", "MediumItalic"), MAROON, is_short_heading),
    StyleRule(6, 9, 10.5, ("Light",), MAROON, is_capitals_heading),
    StyleRule(6, 9, 10.5, ("Medium",), ("4d4d4f",), lambda t: len(t) <= 60),
]
