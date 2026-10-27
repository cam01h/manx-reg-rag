import difflib
import logging
import re
from collections import defaultdict
from pathlib import Path

from extraction_ops.toolbelts.nra.nra_styles import (
    CAPTION,
    PULL_QUOTE,
    PageText,
    StyledLine,
    StyleRule,
    body_words,
    match_key,
    page_texts,
    role_of,
    styled_lines,
)

logger = logging.getLogger(__name__)

# pymupdf4llm's page separator, switched on by NRA_MD_OPTIONS. It ends each page.
_SEPARATOR = re.compile(r"^--- end of page\.page_number=(\d+) ---[ \t]*$", re.MULTILINE)
_MD_HEADING = re.compile(r"^#{1,6} ")
_CHAPTER_LABEL = re.compile(r"^CHAPTER\s+(\d+)$")
# pymupdf4llm drops descenders from large headings, leaving them at the end: "Fi ure 3 ... g g"
_STRAY_DESCENDERS = re.compile(r"(?:\s+[gjpqy])+\s*$")

_FUZZY_RATIO = 0.85
_MIN_PULL_QUOTE_KEY = 25
_JOIN_WORDS = 6  # words compared either side of a break when rejoining split paragraphs
_JOIN_WINDOW = 30  # paragraphs either side a split's tail may be found


def is_heading(line: str) -> bool:
    return bool(_MD_HEADING.match(line))


def is_structural(paragraph: str) -> bool:
    """Headings, tables and bold captions - never merged into or out of."""
    return paragraph.startswith(("#", "|", "**", "[")) or not paragraph.strip()


def strip_markup(line: str) -> str:
    line = re.sub(r"^#{1,6} ", "", line)
    return line.replace("**", "").replace("_", "").strip()


def split_pages(md: str) -> list[tuple[int, str]]:
    pages: list[tuple[int, str]] = []
    start = 0
    for m in _SEPARATOR.finditer(md):
        pages.append((int(m.group(1)), md[start : m.start()]))
        start = m.end()
    if md[start:].strip():
        pages.append(((pages[-1][0] + 1) if pages else 1, md[start:]))
    if not pages:
        logger.warning(
            "no page separators found - is page_separators set in md_options?"
        )
        pages = [(0, md)]
    return pages


"""<=== HEADINGS ===>"""


def _chapter_numbers(lines: tuple[StyledLine, ...]) -> dict[int, str]:
    # divider pages carry "CHAPTER 6" beside the title: page -> "6"
    found: dict[int, str] = {}
    for line in lines:
        m = _CHAPTER_LABEL.match(line.text.replace("\x07", "").strip())
        if m:
            found[line.page] = m.group(1)
    return found


def _classified(
    pdf_path: Path, rules: list[StyleRule]
) -> dict[int, list[tuple[StyledLine, int | str]]]:
    by_page: dict[int, list[tuple[StyledLine, int | str]]] = defaultdict(list)
    for line in styled_lines(pdf_path):
        role = role_of(line, rules)
        if role is not None:
            by_page[line.page].append((line, role))
    return by_page


def _ratio(text: str, candidate: tuple[StyledLine, int | str]) -> float:
    return difflib.SequenceMatcher(
        None, match_key(text), match_key(candidate[0].text)
    ).ratio()


def _best_match(
    key: str, candidates: list[tuple[StyledLine, int | str]]
) -> tuple[StyledLine, int | str] | None:
    if not key:
        return None
    for cand in candidates:
        if match_key(cand[0].text) == key:
            return cand
    best, best_ratio = None, 0.0
    for cand in candidates:
        ratio = difflib.SequenceMatcher(None, key, match_key(cand[0].text)).ratio()
        if ratio > best_ratio:
            best, best_ratio = cand, ratio
    return best if best_ratio >= _FUZZY_RATIO else None


# "6.3.2 Banking Sector", "3.1Terrorist Financing NRA" (sic)
_SECTION_NUMBER = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){1,3})\.?(?=\s|[A-Z])\s*")


def _split_merged(
    key: str, candidates: list[tuple[StyledLine, int | str]]
) -> list[tuple[StyledLine, int | str]] | None:
    """pymupdf4llm can put two headings on one md line: "6.1 Financial Institutions (FIs)
    6.1.1 Banking Sector". Split the line into consecutive fitz headings if it is exactly that."""
    parts: list[tuple[StyledLine, int | str]] = []
    rest = key
    while rest:
        prefix = max(
            (
                c
                for c in candidates
                if match_key(c[0].text) and rest.startswith(match_key(c[0].text))
            ),
            key=lambda c: len(match_key(c[0].text)),
            default=None,
        )
        if prefix is None:
            return None
        parts.append(prefix)
        rest = rest[len(match_key(prefix[0].text)) :]
    return parts if len(parts) > 1 else None


def _render(line: StyledLine, role: int | str, chapters: dict[int, str]) -> str | None:
    text = re.sub(r"[\x07\t ]+", " ", line.text).strip()
    text = re.sub(r"^[●○■•◦]\s*", "", text)
    if role == PULL_QUOTE:
        return None
    if role == CAPTION:
        return f"**{text}**"
    assert isinstance(role, int)
    level = role
    number = chapters.get(line.page)
    if level == 1 and number and not text.startswith(number):
        text = f"{number}. {text}"
    numbered = _SECTION_NUMBER.match(text)
    if numbered and level <= 5:
        # the numbering is more consistent than the type sizes: 6.3.2 is level 3 whatever
        # size it was set in
        level = numbered.group(1).count(".") + 1
        text = f"{numbered.group(1)} {text[numbered.end() :]}"
    return f"{'#' * level} {text}"


def relevel_page(
    page_md: str,
    page_no: int,
    by_page: dict[int, list[tuple[StyledLine, int | str]]],
    chapters: dict[int, str],
) -> str:
    """Rewrite each md heading using the style and text of the matching fitz line; md
    headings with no matching heading style become plain text. Plain lines that are
    exactly a heading are promoted."""
    here = by_page.get(page_no, [])
    near = here + by_page.get(page_no - 1, []) + by_page.get(page_no + 1, [])
    lines = page_md.split("\n")
    out: list[str] = []
    # a chapter divider page that pymupdf4llm gave no heading still opens the chapter
    used = {match_key(strip_markup(line)) for line in lines if is_heading(line)}
    for styled, role in here:
        if role == 1 and styled.colour == "ffffff":
            key = match_key(styled.text)
            if not any(
                key == u
                or difflib.SequenceMatcher(None, key, u).ratio() >= _FUZZY_RATIO
                for u in used
            ):
                rendered = _render(styled, role, chapters)
                if rendered:
                    out.append(rendered)
                    out.append("")
    i = 0
    while i < len(lines):
        line = lines[i]
        if is_heading(line):
            text = _STRAY_DESCENDERS.sub("", strip_markup(line))
            match = _best_match(match_key(text), here) or _best_match(
                match_key(text), near
            )
            # a heading wrapped onto two md heading lines
            nxt = next(
                (j for j in range(i + 1, min(i + 4, len(lines))) if lines[j].strip()),
                None,
            )
            if nxt is not None and is_heading(lines[nxt]):
                joined = f"{text} {_STRAY_DESCENDERS.sub('', strip_markup(lines[nxt]))}"
                joined_match = _best_match(match_key(joined), here)
                if joined_match and (
                    match is None or _ratio(joined, joined_match) > _ratio(text, match)
                ):
                    match = joined_match
                    i = nxt
            merged = _split_merged(match_key(text), here) if match is None else None
            if merged:
                for styled, role in merged:
                    rendered = _render(styled, role, chapters)
                    if rendered is not None:
                        out.extend([rendered, ""])
            elif match is None:
                out.append(f"[demoted] {strip_markup(line)}")
            else:
                rendered = _render(match[0], match[1], chapters)
                if rendered is not None:
                    out.append(rendered)
        elif (
            line.strip()
            and not line.startswith(("|", "- ", ">", "**==>", "**-----"))
            and len(line) < 160
        ):
            key = match_key(line)
            promoted = next(
                (
                    (sl, role)
                    for sl, role in here
                    if role != PULL_QUOTE
                    and (role == CAPTION or (isinstance(role, int) and role <= 5))
                    and match_key(sl.text) == key
                ),
                None,
            )
            out.append(_render(*promoted, chapters) or line if promoted else line)
        else:
            out.append(line)
        i += 1
    return "\n".join(out)


def tidy_headings(md: str) -> str:
    """Drop repeated headings (divider page + chapter page), bare "CHAPTER 6" labels, and
    join runs of demoted short lines (eg a score bar: "Module 3", "Asset Forfeiture", "0.7")."""
    paragraphs = re.split(r"\n\s*\n", md)
    out: list[str] = []
    for para in paragraphs:
        para = para.strip("\n")
        if not para.strip():
            continue
        if _CHAPTER_LABEL.match(para.strip()):
            continue
        if para.startswith("[demoted] "):
            text = para.removeprefix("[demoted] ").strip()
            if not text or _CHAPTER_LABEL.match(text):
                continue
            if (
                out
                and out[-1].startswith("[demoted] ")
                and len(out[-1]) < 200
                and len(text) < 100
            ):
                out[-1] = f"{out[-1]} {text}"
                continue
            out.append(f"[demoted] {text}")
            continue
        if is_heading(para) and out:
            previous = next(
                (p for p in reversed(out) if not p.startswith("[demoted] ")), ""
            )
            # fuzzy: the divider and the chapter page can spell the title differently
            # ("Law Enforement" / "Law Enforcement")
            if is_heading(previous) and (
                difflib.SequenceMatcher(
                    None,
                    match_key(strip_markup(previous)),
                    match_key(strip_markup(para)),
                ).ratio()
                >= 0.9
            ):
                continue
        out.append(para)
    joined = "\n\n".join(out)
    return re.sub(r"^\[demoted\] ", "", joined, flags=re.MULTILINE)


"""<=== READING ORDER ===>"""

_ANCHOR_WORDS = 6


def _positions(keys: list[str], words: tuple[str, ...]) -> list[int]:
    if not keys:
        return []
    probe = keys[:_ANCHOR_WORDS]
    n = len(probe)
    return [i for i in range(len(words) - n + 1) if words[i : i + n] == tuple(probe)]


def reorder_page(page_md: str, page: PageText | None) -> str:
    """pymupdf4llm sometimes reads a two-column page in horizontal bands, interleaving the
    columns. Each paragraph is found on the page by its opening words and placed by the
    reading order of the block it sits in (columns within bands - see reading_ranks), then
    by its position within that block. A paragraph that cannot be placed (a table, an
    ambiguous heading) stays directly after the paragraph it followed."""
    paragraphs = [p for p in re.split(r"\n\s*\n", page_md) if p.strip()]
    if len(paragraphs) < 2 or page is None or not page.words:
        return page_md
    # pass 1: every placement a paragraph could have; unambiguous ones are fixed
    options: list[list[tuple[float, float]]] = []
    fixed: list[tuple[float, float] | None] = []
    for para in paragraphs:
        keys = _keys(para)
        # tables hold cells in row order, the PDF in column order - not comparable
        candidates = [] if para.startswith("|") else _positions(keys, page.words)
        if len(keys) < _ANCHOR_WORDS:
            # a short heading ("Banking") also turns up in body text - a heading starts a block
            starts = [
                c
                for c in candidates
                if c == 0 or page.word_block[c - 1] != page.word_block[c]
            ]
            candidates = starts or candidates
        ranked = sorted(
            (float(page.block_rank[page.word_block[c]]), float(c)) for c in candidates
        )
        options.append(ranked)
        fixed.append(
            ranked[0]
            if len(ranked) == 1 or (ranked and len(keys) >= _ANCHOR_WORDS)
            else None
        )

    # pass 2: an ambiguous paragraph (usually a short heading) goes just before the next
    # fixed paragraph, as a heading precedes its body; unplaceable ones follow their predecessor
    placed: list[tuple[tuple[float, float], int, str]] = []
    last: tuple[float, float] = (-1.0, -1.0)
    for order, para in enumerate(paragraphs):
        position = fixed[order]
        if position is None and options[order]:
            following = next((f for f in fixed[order + 1 :] if f is not None), None)
            before = [r for r in options[order] if following is None or r < following]
            after = [r for r in options[order] if r > last]
            position = (
                before[-1] if before else (after[0] if after else options[order][0])
            )
        if position is None:
            position = (last[0], last[1] + 0.001)
        placed.append((position, order, para))
        last = position
    reordered = [p for _, _, p in sorted(placed)]
    if reordered == paragraphs:
        return page_md
    return "\n\n".join(reordered)


def relevel_headings(md: str, pdf_path: Path, rules: list[StyleRule]) -> str:
    by_page = _classified(pdf_path, rules)
    chapters = _chapter_numbers(styled_lines(pdf_path))
    texts = page_texts(pdf_path)
    pages = [
        relevel_page(reorder_page(text, texts.get(no)), no, by_page, chapters)
        for no, text in split_pages(md)
    ]
    return tidy_headings("\n\n".join(pages))


"""<=== PULL QUOTES ===>"""


def drop_pull_quotes(md: str, pdf_path: Path, rules: list[StyleRule]) -> str:
    """Pull quotes repeat a sentence from the body in large blue type. A paragraph is only
    dropped when it sits inside a pull quote AND its text also appears in another paragraph,
    so a quote that is not repeated in the body is kept."""
    # one quote can be several styled lines, so each page's quotes are also joined up
    by_page: dict[int, list[str]] = defaultdict(list)
    for line in styled_lines(pdf_path):
        if role_of(line, rules) == PULL_QUOTE:
            by_page[line.page].append(match_key(line.text))
    quote_keys = [k for keys in by_page.values() for k in keys]
    quote_keys += ["".join(keys) for keys in by_page.values() if len(keys) > 1]
    paragraphs = re.split(r"\n\s*\n", md)
    keys = [match_key(p) for p in paragraphs]
    candidates = {
        i
        for i, (para, key) in enumerate(zip(paragraphs, keys))
        if len(key) >= _MIN_PULL_QUOTE_KEY
        and not is_structural(para)
        and any(
            key in q or difflib.SequenceMatcher(None, key, q).ratio() >= 0.9
            for q in quote_keys
        )
    }
    if not candidates:
        return md
    body = "|".join(k for i, k in enumerate(keys) if i not in candidates)
    dropped = {i for i in candidates if keys[i] in body}
    logger.info("[%d] pull quote paragraphs dropped", len(dropped))
    return "\n\n".join(p for i, p in enumerate(paragraphs) if i not in dropped)


"""<=== PARAGRAPHS SPLIT ACROSS COLUMNS AND PAGES ===>"""


def _keys(text: str) -> list[str]:
    return [k for k in (match_key(w) for w in strip_markup(text).split()) if k]


def _ends_open(paragraph: str) -> bool:
    """A sentence cut off mid-way: long enough to be prose, ending on a lower-case word
    ("... organised crime, and the u") - not a title or a score bar ending "0.7 High"."""
    text = strip_markup(paragraph).rstrip()
    return len(text) >= 60 and bool(re.search(r"(?:^|\s)[a-z][\w'-]*,?$", text))


def rejoin_split_paragraphs(md: str, pdf_path: Path) -> str:
    """A paragraph that starts in lower case is the tail of a paragraph broken by a column
    or page. Its first words are found in the PDF's own text stream, which gives the words
    that really came before it; the paragraph ending with those words gets the tail back,
    wherever pymupdf4llm put it. A tail starting with a capital ("UK-based ...") is only
    rejoined to a paragraph left mid-sentence, since otherwise every pair of consecutive
    paragraphs would qualify."""
    stream = body_words(pdf_path)
    index: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for pos in range(len(stream) - _JOIN_WORDS):
        index[stream[pos : pos + _JOIN_WORDS]].append(pos)

    paragraphs = [p for p in re.split(r"\n\s*\n", md) if p.strip()]
    tails = {
        i: tuple(_keys(p)[-_JOIN_WORDS:])
        for i, p in enumerate(paragraphs)
        if not is_structural(p)
    }
    joined_into: dict[int, list[int]] = defaultdict(list)
    parent: dict[int, int] = {}

    def descends_from(i: int, j: int) -> bool:
        while i in parent:
            i = parent[i]
            if i == j:
                return True
        return False

    for j, para in enumerate(paragraphs):
        if (
            is_structural(para)
            or para.startswith("- ")
            or not re.match(r"[A-Za-z]", para)
        ):
            continue
        lower = para[0].islower()
        head = tuple(_keys(para)[:_JOIN_WORDS])
        if len(head) < _JOIN_WORDS:
            continue
        before: set[tuple[str, ...]] = set()
        for pos in index.get(head, [])[:5]:
            if pos >= _JOIN_WORDS:
                before.add(stream[pos - _JOIN_WORDS : pos])
        owners = [
            i
            for i, tail in tails.items()
            if i != j
            and tail in before
            and not descends_from(i, j)
            and not joined_into.get(i)
            and (lower or _ends_open(paragraphs[i]))
            # the two halves of a split are always close; identical text elsewhere in
            # the document (eg a table repeated in an appendix) must not attract it
            and abs(i - j) <= _JOIN_WINDOW
        ]
        if not owners and lower:
            # the PDF's text stream cannot confirm it (a table or figure frame sits
            # between the two halves), but the text can: a lower-case continuation and the
            # nearest prose paragraph before it, past any tables or captions, left mid-sentence
            previous = next(
                (
                    i
                    for i in range(j - 1, max(-1, j - 5), -1)
                    if not is_structural(paragraphs[i])
                ),
                None,
            )
            if (
                previous is not None
                and previous not in parent
                and not joined_into.get(previous)
                and _ends_open(paragraphs[previous])
            ):
                owners = [previous]
        if not owners:
            continue
        owner = min(owners, key=lambda i: (abs(i - j), i > j))
        joined_into[owner].append(j)
        parent[j] = owner
    moved = set(parent)

    if not moved:
        return md

    def gather(i: int) -> str:
        text = paragraphs[i].rstrip()
        for j in joined_into.get(i, []):
            text = f"{text} {gather(j).lstrip()}"
        return text

    out = [gather(i) for i in range(len(paragraphs)) if i not in moved]
    logger.info("[%d] split paragraphs rejoined", len(moved))
    return "\n\n".join(out)
