import functools
import itertools
import logging
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import fitz

from extraction_ops.models import ChunkSplitters
from extraction_ops.toolbelts.fiu.fiu_shared import (
    close_punctuation_gaps,
    drop_empty_bullets,
    drop_picture_markers,
    strip_footnote_numbers,
)
from extraction_ops.toolbelts.nra.nra_base import split_on_paragraph_item_or_sentence
from extraction_ops.toolbelts.nra.nra_styles import match_key, styled_lines
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    rejoin_page_breaks,
    replace_from_dict,
    split_on_paragraph_not_list,
)

logger = logging.getLogger(__name__)

"""<=== SHARED SET-UP FOR THE FIU TYPOLOGY REPORTS ===>"""

# The four typology reports share one Publisher template:
#   - section titles are white 28-36pt text set over a photo banner. pymupdf4llm classes
#     the banner as a picture, so the title arrives as "picture text" (or now and then as
#     a "## " heading)
#   - each typology is white text in a shaded box - also picture text - followed by a
#     "Red Flags" list
#   - diagrams are pictures whose text is labels only
# The md stays the source of the text. fitz is consulted for the section titles (so a
# picture is only made a heading when its text really is a banner) and for the few boxes
# and the glossary that pymupdf4llm loses or mangles.

_BANNER_MIN_SIZE = 27
_WHITE = "ffffff"

_PICTURE = re.compile(
    r"\*\*----- Start of picture text -----\*\*(?:<br>)?(.*?)\*\*----- End of picture text -----\*\*(?:<br>)?",
    re.DOTALL,
)
_TYPOLOGY = re.compile(r"^Typology\s*(\d+)\s*[:\-–—]?\s*(.*)$")
# a title wrapped onto a second line is short; the first line of the case is not
_TITLE_WRAP_CHARS = 45
_MIN_PROSE_WORDS = 40
_MIN_STATEMENT_WORDS = 15


@functools.cache
def _title_keys(pdf_path: Path) -> frozenset[str]:
    """Match keys of every banner title, and of each pair of consecutive banner lines (a
    title set over two lines in two sizes, eg "Typologies:" / "Multiple Occupancy")."""
    banners = [
        line
        for line in styled_lines(pdf_path)
        # "Typologies:" is set in black over a white panel, every other title in white
        if line.size >= _BANNER_MIN_SIZE and line.page > 1
    ]
    keys = {match_key(line.text) for line in banners}
    keys.update(
        match_key(a.text) + match_key(b.text)
        for a, b in itertools.pairwise(banners)
        if a.page == b.page
    )
    keys.discard("")
    return frozenset(keys)


@functools.cache
def banner_keys(pdf_path: Path) -> frozenset[str]:
    # "Typologies: Labour Exploitation" can arrive as the heading "Labour Exploitation"
    keys = _title_keys(pdf_path)
    return keys | {k.removeprefix("typologies") for k in keys} - {""}


def banner_heading(title: str, pdf_path: Path) -> str:
    """ "# title", with the "Typologies: " the md dropped put back and the trailing colon of
    "High Risk Countries:" taken off"""
    key = match_key(title)
    titles = _title_keys(pdf_path)
    if key not in titles and "typologies" + key in titles:
        title = f"Typologies: {title}"
    return f"# {title.rstrip(' :')}"


def _picture_lines(body: str) -> list[str]:
    lines = [line.strip() for line in body.replace(" ", " ").split("<br>")]
    # stray dashes the template sets beside a title
    lines = [line for line in lines if line and not re.fullmatch(r"[-–—]+", line)]
    if "'" in lines:
        # "The Isle of Man's" with its apostrophe set as a line of its own
        lines = [line for line in lines if line != "'"]
        lines = [re.sub(r"(?<=\w) s\b", "'s", line, count=1) for line in lines]
    return lines


def _flow(lines: list[str]) -> str:
    """Picture text keeps the box's line wraps. Lines are joined into paragraphs, with a
    break after a line ending a sentence and a list item for each bullet."""
    paragraphs: list[str] = []
    for line in lines:
        bullet = line.startswith(("•", ""))
        if bullet:
            line = "- " + line.lstrip("• ").strip()
        if not paragraphs or bullet or re.search(r"[.:;!?\"')]$", paragraphs[-1]):
            paragraphs.append(line)
        elif paragraphs[-1].endswith("-"):
            # "the same Isle of Man-" / "licensed poker platform"
            paragraphs[-1] = f"{paragraphs[-1]}{line}"
        else:
            paragraphs[-1] = f"{paragraphs[-1]} {line}"
    return "\n\n".join(paragraphs)


def typology_heading(number: str, title: str) -> str:
    title = re.sub(r"\s+", " ", title).strip(" -–—:")
    return f"## Typology {number} - {title}" if title else f"## Typology {number}"


def _typology(lines: list[str]) -> str:
    match = cast(re.Match, _TYPOLOGY.match(lines[0]))
    title = [match.group(2)]
    rest = lines[1:]
    while rest and len(rest[0]) < _TITLE_WRAP_CHARS and not rest[0].endswith("."):
        title.append(rest.pop(0))
    return f"{typology_heading(match.group(1), ' '.join(title))}\n\n{_flow(rest)}"


def pictures_to_text(text: str, pdf_path: Path) -> str:
    """Banner titles become "# " headings, typology boxes "## Typology N - title" headings
    with their case as the body, and other boxes of prose (eg "Sanctions evasion commonly
    involves:") paragraphs. Chart and diagram labels, and the pull quote, are dropped."""
    banners = banner_keys(pdf_path)

    def repl(match: re.Match) -> str:
        lines = _picture_lines(match.group(1))
        if not lines:
            return ""
        joined = re.sub(r"\s+", " ", " ".join(lines))
        if match_key(joined) in banners:
            return f"\n\n{banner_heading(joined, pdf_path)}\n\n"
        if _TYPOLOGY.match(lines[0]):
            return f"\n\n{_typology(lines)}\n\n"
        words = len(joined.split())
        # a box of prose, or a short statement in a box ("Immediate outcome 11 dictates
        # ..."); the pull quote has no full stop and is dropped
        if words >= _MIN_PROSE_WORDS or (
            words >= _MIN_STATEMENT_WORDS and joined.endswith(".")
        ):
            return f"\n\n{_flow(lines)}\n\n"
        return ""

    return _PICTURE.sub(repl, text)


"""<=== BOXES PYMUPDF4LLM LOSES ===>"""


def _block_text(block: dict) -> str:
    lines = [
        "".join(s["text"] for s in line["spans"]).strip()
        for line in block.get("lines", [])
    ]
    return " ".join(line for line in lines if line).replace(" ", " ")


def _is_white(block: dict) -> bool:
    spans = [
        s for line in block.get("lines", []) for s in line["spans"] if s["text"].strip()
    ]
    return bool(spans) and all(f"{s['color']:06x}" == _WHITE for s in spans)


def restore_lost_boxes(text: str, pdf_path: Path) -> str:
    """Now and then a typology box is dropped whole, leaving only its last line behind as a
    bold paragraph. The box is rebuilt from the PDF's own text blocks (one per paragraph)
    in place of that line."""
    md_keys = " ".join(match_key(w) for w in text.replace("<br>", " ").split())
    with fitz.open(pdf_path) as doc:
        for page in doc:
            blocks = [
                b
                for b in cast(dict[str, Any], page.get_text("dict"))["blocks"]
                if _is_white(b)
            ]
            for i, block in enumerate(blocks):
                title = _block_text(block)
                match = _TYPOLOGY.match(title)
                if not match:
                    continue
                paragraphs = []
                for following in blocks[i + 1 :]:
                    if _TYPOLOGY.match(_block_text(following)):
                        break
                    paragraphs.append(_block_text(following))
                probe = " ".join(match_key(w) for w in " ".join(paragraphs).split()[:8])
                if not paragraphs or probe in md_keys:
                    continue
                tail = cast(list, cast(dict, blocks[i + len(paragraphs)])["lines"])[-1]
                tail_text = "".join(s["text"] for s in tail["spans"]).strip()
                tail_text = base_text_cleaner(tail_text).replace("‑", "-")
                orphan = f"**{tail_text}**"
                if orphan not in text:
                    logger.error("lost box [%s] has no orphan line to replace", title)
                    raise ValueError(
                        f"lost box [{title}] has no orphan line to replace"
                    )
                box = typology_heading(match.group(1), match.group(2))
                body = "\n\n".join(
                    base_text_cleaner(p).replace("‑", "-") for p in paragraphs
                )
                text = text.replace(orphan, f"{box}\n\n{body}", 1)
                logger.info("restored lost box [%s] from the PDF", title)
    return text


"""<=== HEADINGS ===>"""

_MD_HEADING = re.compile(r"^#{2,6} (?:\*\*)?(.*?)(?:\*\*)?[ \t]*$", re.MULTILINE)


def relevel_headings(text: str, pdf_path: Path) -> str:
    """md headings: banner titles "# ", "Red Flags" a bold label inside its typology, links
    and other text mistaken for a heading plain text, everything else "## "."""
    banners = banner_keys(pdf_path)

    def repl(match: re.Match) -> str:
        heading = match.group(1).strip().lstrip("- ").strip()
        if heading.startswith("Typology"):
            return match.group()
        if not heading or re.search(r"https?://|www\.", heading):
            return heading
        if re.match(r"Red Flags", heading):
            return "**Red Flags:**"
        if match_key(heading) in banners:
            return banner_heading(heading, pdf_path)
        return f"## {heading}"

    return _MD_HEADING.sub(repl, text)


def drop_repeated_headings(text: str) -> str:
    """A section title is often repeated straight after as the first sub-heading
    ("Enforced Criminality" twice), and a section running over several pages repeats its
    banner on each one."""
    paragraphs = re.split(r"\n\s*\n", text)
    out: list[str] = []
    section = ""
    for para in paragraphs:
        if not para.strip():
            continue
        key = match_key(para.lstrip("#"))
        if para.startswith("# "):
            if key == section:
                continue
            section = key
        # "# Typologies: Sexual Exploitation" then "## Sexual Exploitation"
        if (
            para.startswith("#")
            and out
            and out[-1].startswith("#")
            and match_key(out[-1].lstrip("#")).endswith(key)
        ):
            continue
        out.append(para)
    return "\n\n".join(out)


"""<=== FOOTNOTES AND LISTS ===>"""


def drop_footnotes(text: str) -> str:
    # "**1.** htps://...", "> **4.** RUSI - Guide to ...", "**6.** https://... **7.** https://..."
    text = re.sub(r"^(?:> )?\*\*\d{1,2}\.\s?\*\*.*$\n?", "", text, flags=re.MULTILINE)
    # the wrapped tail of a footnote link: "> -the-symbols/"
    text = re.sub(r"^> \S*/[ \t]*$\n?", "", text, flags=re.MULTILINE)
    # "> ***** The Isle of Man NRA uses ..." - asterisk footnotes carry substance
    text = re.sub(r"^> \*{4,}\s*", "Note: ", text, flags=re.MULTILINE)
    return strip_footnote_numbers(text)


def tidy_lists(text: str) -> str:
    # red flag bullets that came through as the Wingdings arrow, sometimes two to a line
    text = re.sub(r"[ \t]*[ \t]*", "\n\n- ", text)
    text = re.sub(r"^\n\n- ", "- ", text)

    # items wrapped onto a second item: "- **... closed social**" / "- **media groups ...**",
    # "- **... no arm's-**" / "- **length terms ...**"
    def join(match: re.Match) -> str:
        item = match.group(1)
        return item if item.endswith("-") else f"{item} "

    previous = None
    while previous != text:
        previous = text
        text = re.sub(
            r"^(- \*\*[^\n]*?[^.;:!?\n])\*\*[ \t]*\n\s*\n- \*\*(?=[a-z])",
            join,
            text,
            flags=re.MULTILINE,
        )
    return text


"""<=== GLOSSARY ===>"""


def _glossary_rows(pdf_path: Path) -> list[tuple[str, str]]:
    """The glossary page's term and meaning, read from fitz: a term and its meaning are
    either one line with a wide gap or two lines at the same height."""
    rows: list[tuple[str, str]] = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            lines = []
            for block in cast(dict[str, Any], page.get_text("dict"))["blocks"]:
                for line in block.get("lines", []):
                    text = "".join(s["text"] for s in line["spans"])
                    size = max(s["size"] for s in line["spans"])
                    lines.append((round(line["bbox"][1]), line["bbox"][0], text, size))
            if not any(
                t.strip() == "Glossary" and s >= _BANNER_MIN_SIZE
                for _, _, t, s in lines
            ):
                continue
            by_y: dict[int, list[tuple[float, str]]] = {}
            for y, x, t, s in lines:
                if t.strip() and 11 <= s <= 17:
                    key = next((k for k in by_y if abs(k - y) <= 3), y)
                    by_y.setdefault(key, []).append((x, t))
            for y in sorted(by_y):
                joined = "     ".join(t for _, t in sorted(by_y[y])).strip()
                parts = re.split(r"\s{3,}|\s+[–-]\s+", joined, maxsplit=1)
                if len(parts) == 2 and parts[1].strip():
                    row = (parts[0].strip(), parts[1].strip())
                    # the TF glossary lists "SDN" twice
                    if row not in rows:
                        rows.append(row)
                elif rows and joined[:1].isupper() and " " in joined:
                    # a meaning wrapped onto a second line ("... Trafficking in Persons, /
                    # Especially Women and Children")
                    rows[-1] = (rows[-1][0], f"{rows[-1][1]} {joined}")
                else:
                    logger.warning("glossary term with no meaning: [%s]", joined)
    return rows


def glossary_to_definitions(text: str, pdf_path: Path) -> str:
    """The glossary section's md (a mangled run of terms) is replaced by definition lines in
    the shape the definitions parser expects: "TERM" meaning"""
    rows = _glossary_rows(pdf_path)
    if not rows:
        return text
    lines = "\n".join(
        f'"{base_text_cleaner(term)}" {base_text_cleaner(meaning).replace(chr(34), chr(39))}'
        for term, meaning in rows
    )
    return re.sub(
        r"(^# Glossary[ \t]*\n).*?(?=^# |\Z)",
        lambda m: f"{m.group(1)}\n{lines}\n\n",
        text,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )


def definitions_to_lines(text: str, title: str = "Definitions") -> str:
    """A section of "## Term" headings, each with a paragraph explaining it, becomes
    definition lines: "Term" explanation. The section's own title is dropped so the lines
    run straight on from the glossary before it."""

    def section(match: re.Match) -> str:
        body = re.sub(
            r"^## (.+?)[ \t]*\n\s*\n(?!#)(.+)$",
            lambda m: f'"{m.group(1)}" {m.group(2).replace(chr(34), chr(39))}',
            match.group(2),
            flags=re.MULTILINE,
        )
        return body

    return re.sub(
        rf"(^# {title}[ \t]*\n)(.*?)(?=^# |\Z)",
        section,
        text,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )


"""<=== CLEANER AND TOOLBELT FACTORY ===>"""


def tidy_blank_lines(text: str) -> str:
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def build_typology_cleaner(
    pdf_path: Path,
    replacements: dict[str, str] | None = None,
    extra: Callable[[str], str] | None = None,
) -> Callable[[str], str]:
    def clean(text: str) -> str:
        text = base_text_cleaner(text)
        # non-breaking hyphen and narrow space
        text = text.replace("‑", "-").replace(" ", " ")
        if replacements:
            text = replace_from_dict(text, replacements)
        # chart legends: "**█ A Little █ Not at All █ Quite Well**"
        text = re.sub(r"^.*\u2588.*$\n?", "", text, flags=re.MULTILINE)
        text = restore_lost_boxes(text, pdf_path)
        text = pictures_to_text(text, pdf_path)
        text = drop_picture_markers(text)
        text = relevel_headings(text, pdf_path)
        text = drop_repeated_headings(text)
        text = drop_footnotes(text)
        text = tidy_lists(text)
        text = drop_empty_bullets(text)
        text = close_punctuation_gaps(text)
        # "... to support the / regulated sector" broken by a column or page
        text = rejoin_page_breaks(text)
        text = glossary_to_definitions(text, pdf_path)
        if extra is not None:
            text = extra(text)
        return tidy_blank_lines(text)

    return clean


def is_introduction(line: str) -> bool:
    # the first section of every report - "# Introduction to Project Anton" comes later
    return line.strip() == "# Introduction"


TYPOLOGY_SPLITTERS = ChunkSplitters(
    primary=split_on_paragraph_not_list,
    fallback=split_on_paragraph_item_or_sentence,
)
