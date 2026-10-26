import re
from collections.abc import Callable

from extraction_ops.toolbelts.rule_book.rule_book_sectors import (
    RB_ALL,
    RULE_BOOK_SECTORS,
)

# shared by the four Rule Book summary tables (record keeping, consent and notification,
# registers, policies). In layout mode each one comes through as one markdown table per
# page with the header row repeated. Each row becomes its own "### **<rule> - <title>**"
# section, so a chunk is one rule and its sectors can be looked up from the rule number.
#
# rows are handled in three ways:
#   - group row: bold first cell, every other cell empty ("**PART 2 - ...**") -> "## **" heading
#   - page continuation: the rule cell is empty -> cells appended to the previous row
#   - same title, new rule: the title cell is empty -> title taken from the previous row

# repeated on every page: "_**Summary only.  It is each licenceholder's responsibility ..."
_BANNER = re.compile(r"^(?:## )?_\*\*Summary only\..*$\n?", re.MULTILINE)
# a <br> after a full stop / semicolon / colon, or before "(a)" / "(ii)", is a real line
# break inside the cell. Any other <br> is the PDF wrapping the line
_LINE_BREAK = re.compile(r"(?<=[.;:])<br>|<br>(?=\((?:[a-z]|[ivx]+)\))")
_RULE_NO = re.compile(r"\b\d\.\d{1,2}[A-Z]?\b")


def strip_summary_banner(text: str) -> str:
    return _BANNER.sub("", text)


def _split_cells(line: str) -> list[str]:
    # strip only the outer pipes so an empty first cell ("||4.7(8)|...") is kept
    return [cell.strip() for cell in line.strip()[1:-1].split("|")]


def clean_cell(cell: str) -> str:
    cell = cell.replace("**", "")
    # a hyphen at a line wrap stays joined: "safe-<br>custody", "(Non-<br>IOM"
    cell = re.sub(r"(?<=\w)-<br>", "-", cell)
    cell = _LINE_BREAK.sub("\n", cell)
    cell = cell.replace("<br>", " ")
    return re.sub(r"[ \t]+", " ", cell).strip()


def _is_separator(cells: list[str]) -> bool:
    return all(cell and set(cell) <= {"-", ":"} for cell in cells)


def _join(previous: str, extra: str) -> str:
    if not previous:
        return extra
    if not extra:
        return previous
    return f"{previous}\n{extra}" if previous.endswith(".") else f"{previous} {extra}"


def _last_row(items: list[str | list[str]]) -> list[str] | None:
    for item in reversed(items):
        if isinstance(item, list):
            return item
    return None


def flatten_summary_tables(
    text: str,
    header: tuple[str, ...],
    rule_col: int,
    render: Callable[[list[str]], tuple[str, list[str]]],
) -> str:
    # pass 1: rows are collected first so a page continuation can still reach back to the
    # row it belongs to, across the page furniture in between
    items: list[str | list[str]] = []
    for line in text.splitlines():
        if not line.startswith("|"):
            items.append(line)
            continue
        raw = _split_cells(line)
        cells = [clean_cell(cell) for cell in raw]
        if not any(cells) or _is_separator(cells) or tuple(cells) == header:
            continue
        if raw[0].startswith("**") and not any(cells[1:]):
            items.extend(["", f"## **{cells[0]}**", ""])
            continue
        last = _last_row(items)
        if last is not None and not cells[rule_col]:
            for i, cell in enumerate(cells):
                last[i] = _join(last[i], cell)
            continue
        if last is not None and not cells[0]:
            cells[0] = last[0]
        items.append(cells)

    # pass 2: each row becomes a heading and its body lines
    out: list[str] = []
    for item in items:
        if isinstance(item, str):
            out.append(item)
            continue
        heading, body = render(item)
        out.extend(["", f"### **{heading}**", "", *body, ""])
    return "\n".join(out)


def rule_sectors(headers: tuple[str, ...]) -> tuple[str, ...]:
    # the row heading wins; a row with no rule number ("Note 4") falls back to its group
    # heading ("APPENDIX 3 - Financial Resources Statement (Rule 2.30)")
    for header in reversed(headers):
        rules = _RULE_NO.findall(header)
        if rules:
            sectors: set[str] = set()
            for rule in rules:
                sectors.update(RULE_BOOK_SECTORS.get(rule, RB_ALL))
            return tuple(sorted(sectors))
    return RB_ALL
