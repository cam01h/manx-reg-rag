import re
from typing import Callable


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


# text cleaners
def base_header_cleaner(header: str) -> str:
    header = (
        header.replace("- ##", "")
        .replace("- **", "")
        .replace("#", "")
        .replace("*", "")
        .replace("_", "")
        .strip()
    )
    # lstrip added for handbook, extract to custom if it affects other docs
    return header.lstrip("- ")


def base_body_cleaner(line: str) -> str:
    line = (
        line.replace("## **", "")
        .replace("##", "")
        .replace("**", "")
        .replace("_", "")
        .strip()
    )
    return line


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


def redact_section(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1 or end <= start:
        return text
    return text[:start] + text[end:]


def rejoin_page_breaks_with_marker(text: str) -> str:
    return re.sub(
        r"^(?!\s*[-*]|\s*\(?[a-z0-9]{1,4}\))(.*[a-z,]) *\n\s*\n *(?=[a-z])",
        r"\1[joined]",
        text,
        flags=re.MULTILINE,
    )


def rejoin_page_breaks(text: str) -> str:
    return re.sub(
        r"^(?!\s*[-*]|\s*\(?[a-z0-9]{1,4}\))(.*[a-z,]) *\n\s*\n *(?=[a-z])",
        r"\1 ",
        text,
        flags=re.MULTILINE,
    )


# [1] style and **[1]** style
def strip_footnote_markers(text: str) -> str:
    return re.sub(r"\s*(?:\*\* *\[\d+\] *\*\*|\[\d+\])", "", text)


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
    return re.split(r"\n(?=- \(\d+\))", text)


def split_on_bracketed_letter(text: str) -> list[str]:
    return re.split(r"\n(?=- \([a-z]+\))", text)


def split_on_paragraph(text: str) -> list[str]:
    return re.split(r"\n\s*\n", text)


def split_on_new_sentence(text: str) -> list[str]:
    return re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)


# definition line matchers
def base_def_line(line: str) -> bool:
    prefixes = ['- **"', '## **"', '**"']
    return any(line.startswith(p) for p in prefixes)


def base_double_def_line(segs: list[str]) -> bool:
    return len(segs) == 5 and segs[2].strip() in ("or", "and")


def base_false_double_def(segs: list[str]) -> bool:
    return len(segs) == 5 and segs[2].strip() != "or"
