import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# first cell of a rule's opening row, either:
#   "**2.1**<br>**Annual reporting date**<br>..."   (number and title in separate bold runs)
#   "**2.24A Deposit data**5 <br>..."               (one bold run; trailing 5 is a footnote)
# a stray leading <br> appears on some rows (7.12)
_RULE_START = re.compile(
    r"^(?:<br>)*\*\*(\d{1,2}\.\d{1,3}[A-Z]?)(?:\*\*<br>\*\*| )(.+?)\*\*\d*\s*(?:<br>|$)"
)
# the "|Rule|Application|" header row and the "|---|---|" separator repeat on every page
_HEADER_ROW = re.compile(r"^\|(Rule|---|\*\*Rule)")
# lines that close the rule currently being built
_PART_START = "#### **PART"
_APPENDIX_START = "**Appendix"
# the application column is italic; "**_7_**" inside it is a footnote marker
_ITALIC = re.compile(r"_([^_]+)_")
_FOOTNOTE = re.compile(r"\*\*_\d+_\*\*")
# a <br> fragment that is only an enumerator: "(1)", "(2A)" / "(a)", "(iv)"
_NUM_ONLY = re.compile(r"^\(\d+[A-Z]*\)$")
_LETTER_ONLY = re.compile(r"^\([a-z]{1,4}\)$")


@dataclass
class _Rule:
    number: str
    title: str
    applications: list[str] = field(default_factory=list)
    fragments: list[str] = field(default_factory=list)


def _split_cells(line: str) -> list[str]:
    # strip only the outer pipes so an empty last cell ("...||") is kept
    return [c.strip() for c in line.strip()[1:-1].split("|")]


def _application_text(cell: str) -> str:
    cell = _FOOTNOTE.sub("", cell)
    text = " ".join(_ITALIC.findall(cell))
    text = text.replace("<br>", " ").replace("**", "")
    return re.sub(r"\s+", " ", text).strip()


def _add_row(rule: _Rule, cells: list[str], first_cell: str) -> None:
    # rows are [body] or [body, application]
    if len(cells) == 2:
        rule.applications.append(_application_text(cells[1]))
    for fragment in first_cell.split("<br>"):
        if fragment.strip():
            rule.fragments.append(fragment.strip())


def _rebuild_paragraphs(fragments: list[str]) -> list[str]:
    # <br> fragments are visual line wraps from the PDF. Re-join them into one line per
    # paragraph, written as "- (1) ..." / "   - (a) ..." so the shared bracket splitters match.
    lines: list[str] = []
    prefix: str | None = None
    for fragment in fragments:
        if _NUM_ONLY.match(fragment):
            prefix = f"- {fragment} "
        elif _LETTER_ONLY.match(fragment):
            prefix = f"   - {fragment} "
        elif prefix is not None:
            lines.append(prefix + fragment)
            prefix = None
        elif lines:
            lines[-1] = f"{lines[-1]} {fragment}"
        else:
            lines.append(fragment)
    if prefix is not None:
        lines.append(prefix.rstrip())
    return lines


def _render_rule(rule: _Rule) -> list[str]:
    # continuation rows repeat the application (or leave it blank) - keep each distinct text once
    unique: list[str] = []
    for app in rule.applications:
        if app and app not in unique:
            unique.append(app)
    return [
        f"## **{rule.number} {rule.title}**",
        f"Application: {' '.join(unique)}",
        *_rebuild_paragraphs(rule.fragments),
    ]


def flatten_rule_book_tables(text: str) -> str:
    out: list[str] = []
    rule: _Rule | None = None

    for line in text.splitlines():
        if line.startswith((_PART_START, _APPENDIX_START)):
            if rule is not None:
                out.extend(_render_rule(rule))
                rule = None
            out.append(line)
        elif not line.startswith("|"):
            # running heads / page numbers between continuation rows; stripped later in clean_text
            out.append(line)
        elif _HEADER_ROW.match(line):
            continue
        elif rule is not None and line.count("|") > 3:
            # 3+ cells inside a rule = a nested table (3.24, 8.57). pymupdf4llm emits it twice:
            # flattened into the rule's own cell, then again as these rows. The rule cell
            # already holds all of it, so drop the duplicate.
            continue
        else:
            cells = _split_cells(line)
            match = _RULE_START.match(cells[0])
            if match is not None:
                if rule is not None:
                    out.extend(_render_rule(rule))
                rule = _Rule(number=match.group(1), title=match.group(2))
                _add_row(rule, cells, cells[0][match.end() :])
            elif rule is not None:
                _add_row(rule, cells, cells[0])
            else:
                out.append(
                    line
                )  # table row outside the rules (e.g. appendices) - untouched

    if rule is not None:
        out.extend(_render_rule(rule))
    return "\n".join(out)


# <=== RULE 3.24: TABLE CONTINUATION OUT OF ORDER ===>
# The 3.24(1) table runs over a page break. pymupdf4llm puts the page-53 half at the END of
# that page's cell (after (6)(c)) when it sits at the TOP of the page in the PDF. It splits
# (6)(c) mid-sentence: "...client money arising" | table | "from reconciliation discrepancies".
# Run after flatten_rule_book_tables. Markers are exact so a changed edition raises instead
# of silently mis-moving text.
_RULE_3_24_TABLE_START = (
    "\n   - (c) in respect of principal deals, paid for by the client"
)
_RULE_3_24_TABLE_END = "(A+B+C1+C2+D+E1+E2)-F-G X"
_RULE_3_24_INSERT_BEFORE = (
    "\n- (2) A licenceholder should calculate the individual client balance"
)


def fix_rule_3_24_table_order(text: str) -> str:
    insert_at = text.find(_RULE_3_24_INSERT_BEFORE)
    start = text.find(_RULE_3_24_TABLE_START)
    end = text.find(_RULE_3_24_TABLE_END, start)
    if insert_at == -1 or start == -1 or end == -1 or insert_at > start:
        logger.error("rule 3.24 table markers not found in expected order")
        raise ValueError("rule 3.24 table markers not found in expected order")
    end += len(_RULE_3_24_TABLE_END)
    table_tail = text[start:end]
    # cutting the block rejoins "...client money arising" with " from reconciliation..."
    text = text[:start] + text[end:]
    # insert_at is before start, so the cut has not moved it
    return text[:insert_at] + table_tail + text[insert_at:]
