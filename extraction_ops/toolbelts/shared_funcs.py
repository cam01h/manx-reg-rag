import logging
import re
from collections.abc import Callable
from pathlib import Path

from config import PROJECT_ROOT
from extraction_ops.models import SectionMarkers

logger = logging.getLogger(__name__)


# paths
def build_pdf_path(short_name: str) -> Path:
    return PROJECT_ROOT / f"data/raw/{short_name}.pdf"


# helpers
def replace_from_dict(text: str, replacements: dict[str, str]) -> str:
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text


def strip_patterns(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        text = re.sub(pattern, "", text)
    return text


# line -> bool
def in_line(strings: list[str]) -> Callable[[str], bool]:
    def inner(line: str) -> bool:
        return any(s in line for s in strings)

    return inner


def starts_with(strings: list[str]) -> Callable[[str], bool]:
    def inner(line: str) -> bool:
        return any(line.startswith(s) for s in strings)

    return inner


# used in testing, if changed, test_cleaners.py must be updated too
def base_text_cleaner(text: str):
    replacements = {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2013": "-",
        "\u2014": "-",
    }
    return replace_from_dict(text, replacements)


def redact_md_tables(text: str) -> str:
    return re.sub(
        r"(?:^\|.*\|[ \t]*\n?)+",
        "[table redacted from original document]\n",
        text,
        flags=re.MULTILINE,
    )


def replace_section(
    text: str, start_marker: str, end_marker: str, replacement: str = ""
) -> str:
    start = text.find(start_marker)
    if start == -1:
        logger.error(
            "in_replace_section the start marker was not found: [%s]", start_marker
        )
        raise ValueError(
            f"in_replace_section the start marker was not found: [{start_marker}]"
        )
    end = text.find(end_marker, start)
    if end == -1:
        logger.error(
            "in_replace_section the end marker was not found: [%s]", end_marker
        )
        raise ValueError(
            f"in_replace_section the end marker was not found: [{end_marker}]"
        )
    return text[:start] + replacement + text[end:]


def rejoin_page_breaks_with_marker(text: str) -> str:
    # prose lines: join on lowercase or comma
    text = re.sub(
        r"^(?!\s*[-*]|\s*\(?[a-z0-9]{1,4}\))(.*[a-z,]) *\n\s*\n *(?=[a-z])",
        r"\1[joined]",
        text,
        flags=re.MULTILINE,
    )
    # list items: join only when the line ends mid-word, never on a comma
    text = re.sub(
        r"^(\s*[-*].*[a-z]) *\n\s*\n *(?=[a-z])",
        r"\1[joined]",
        text,
        flags=re.MULTILINE,
    )
    return text


def rejoin_page_breaks(text: str) -> str:
    text = re.sub(
        r"^(?!\s*[-*]|\s*\(?[a-z0-9]{1,4}\))(.*[a-z,]) *\n\s*\n *(?=[a-z])",
        r"\1 ",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^(\s*[-*].*[a-z]) *\n\s*\n *(?=[a-z])",
        r"\1 ",
        text,
        flags=re.MULTILINE,
    )
    return text


# [1], **[1]** and _**[1]**_ styles
def strip_footnote_markers(text: str) -> str:
    text = re.sub(r"(?<=[A-Za-z.;:)])\*\*\d{1,2}\*\*", "", text)  # eg **1**
    return re.sub(r"\s*(?:_\*\* *\[\d+\] *\*\*_|\*\* *\[\d+\] *\*\*|\[\d+\])", "", text)


# strips > style footnote
def strip_footnote_bullets(text: str) -> str:
    return re.sub(r"^> *(?:\*\*)?\d+(?:\*\*)? .*$\n?", "", text, flags=re.MULTILINE)


# removes [text] but retains repealed markers
def strip_square_bracket_legislation_ids(text: str) -> str:
    # bracketed provenance citations, eg [P2000/11/15 and 22]
    text = re.sub(r" *\[(?:P\d{4}|\d{4})/[^\]]*\]", "", text)

    # unbracketed provenance citations, eg P2000/11/21ZB & 2008/13/146
    text = re.sub(
        r" *(?:P?\d{4}/\d+/\w+)(?:\s*(?:&|and)\s*P?\d{4}/\d+/\w+)*",
        "",
        text,
    )
    return text


# splitters
def split_on_bracketed_num(text: str) -> list[str]:
    return re.split(r"\n(?=[ \t]*(?:- )?\(\d+[A-Z]*\))", text)


# eg "1."
def split_on_numbered_dot(text: str) -> list[str]:
    return re.split(r"\n(?=[ \t]*(?:- )?(?:\*\*)?\d+\.\s)", text)


# eg (2A) or (3ZB)
def split_on_bracketed_amended_num(text: str) -> list[str]:
    return re.split(r"\n(?=\s*- \(\d+[A-Z]*\))", text)


def split_on_bracketed_letter(text: str) -> list[str]:
    return re.split(r"\n(?=[ \t]*(?:- )?\([a-z]+\))", text)


def split_on_paragraph(text: str) -> list[str]:
    return re.split(r"\n\s*\n", text)


def split_on_new_sentence(text: str) -> list[str]:
    return re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)


# definition line matchers
def base_def_line(line: str) -> bool:
    prefixes = ['- **"', '## **"', '**"']
    return any(line.startswith(p) for p in prefixes)


def fixed_sectors(
    sectors: tuple[str, ...],
) -> Callable[[tuple[str, ...]], tuple[str, ...]]:
    def inner(headers: tuple[str, ...]) -> tuple[str, ...]:
        return sectors

    return inner


# Building simple classes
def build_simple_markers(start: str, end: str) -> SectionMarkers:
    return SectionMarkers(start=starts_with([start]), end=starts_with([end]))


# sector matchers
def header_sectors(
    lookup: dict[str, tuple[str, ...]], fallback: tuple[str, ...]
) -> Callable[[tuple[str, ...]], tuple[str, ...]]:
    def inner(headers: tuple[str, ...]) -> tuple[str, ...]:
        sectors: set[str] = set()
        for header in headers:
            for pattern, matched in lookup.items():
                if pattern in header:
                    sectors.update(matched)
        if not sectors:
            return fallback
        return tuple(sorted(sectors))

    return inner
