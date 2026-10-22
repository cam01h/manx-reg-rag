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
# a title that wraps in the PDF continues in further whole-bold fragments:
#   "**Deposit taking returns - non-Isle of Man**<br>**incorporated**<br>(1)..."
_TITLE_WRAP = re.compile(r"^\s*\*\*([^*]+)\*\*\d*\s*(?:<br>|$)")
# rules whose title wraps onto the next page. Listed explicitly because a body that opens
# with a bold sub-heading looks identical in the markdown (9.24 "**Trustees**")
_TITLE_CONTINUES_ON_NEXT_PAGE = {"3.4", "6.62"}
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


def _absorb_title_wrap(title: str, rest: str) -> tuple[str, str]:
    # 24 rules have two-line titles (2.10, 2.23, 5.12, 7.3, 8.42 ...); without this the
    # second line becomes the first line of the body
    match = _TITLE_WRAP.match(rest)
    while match is not None:
        title = f"{title} {match.group(1).strip()}"
        rest = rest[match.end() :]
        match = _TITLE_WRAP.match(rest)
    return title, rest


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
                title, rest = _absorb_title_wrap(
                    match.group(2), cells[0][match.end() :]
                )
                rule = _Rule(number=match.group(1), title=title)
                _add_row(rule, cells, rest)
            elif (
                rule is not None
                and not rule.fragments
                and rule.number in _TITLE_CONTINUES_ON_NEXT_PAGE
            ):
                # the rule starts at the foot of a page with only the first line of its title;
                # the second line opens the next page's row (3.4 "...or trust" / "money")
                title, rest = _absorb_title_wrap(rule.title, cells[0])
                if title == rule.title:
                    logger.error("rule [%s] title continuation not found", rule.number)
                    raise ValueError(f"rule {rule.number} title continuation not found")
                rule.title = title
                _add_row(rule, cells, rest)
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


# <=== APPENDIX 1: DEFINITIONS TABLE ===>
# Rows are |term|definition|. Rewritten as the usual definition line so the shared
# definition matchers pick them up:  - **"term"** means ...
# Run after flatten_rule_book_tables (which leaves appendix rows untouched).
_DEFINITIONS_START = "**Appendix 1"
_DEFINITIONS_END = "**Appendix 2"
# a definition that runs over a page break continues in a new table whose header
# pymupdf4llm fills with a "Col1" placeholder
_CONTINUATION_CELL = "Col1"
# list items inside a definition: "(a) text" / "(iv) text", or a lone "(a)" / "•" fragment
_ENUM_WITH_TEXT = re.compile(r"^\([a-z0-9]{1,4}\)\s+\S")
_ENUM_OR_BULLET_ONLY = re.compile(r"^(?:\([a-z0-9]{1,4}\)|•)$")


def _clean_term(cell: str) -> str:
    # '**"annual financial**<br>**return"**' -> '"annual financial return"'
    term = cell.replace("<br>", " ").replace("**", "")
    return re.sub(r"\s+", " ", term).strip()


def _definition_lines(cell: str) -> list[str]:
    # <br> fragments are line wraps; list items start a new "- " line
    lines: list[str] = []
    prefix: str | None = None
    for fragment in (f.strip() for f in cell.split("<br>")):
        if not fragment:
            continue
        if _ENUM_OR_BULLET_ONLY.match(fragment):
            prefix = "- " if fragment == "•" else f"- {fragment} "
        elif prefix is not None:
            lines.append(prefix + fragment)
            prefix = None
        elif _ENUM_WITH_TEXT.match(fragment):
            lines.append(f"- {fragment}")
        elif lines:
            lines[-1] = f"{lines[-1]} {fragment}"
        else:
            lines.append(fragment)
    return lines


def flatten_definitions_table(text: str) -> str:
    out: list[str] = []
    in_definitions = False
    # index in `out` of the last line of the current definition. Running heads from a
    # page break sit between a definition and its "Col1" continuation, so continuations
    # are joined here rather than onto out[-1].
    last_line = -1
    for line in text.splitlines():
        if line.startswith(_DEFINITIONS_START):
            in_definitions = True
            out.append(line)
        elif line.startswith(_DEFINITIONS_END):
            in_definitions = False
            out.append(line)
        elif not in_definitions or not line.startswith("|"):
            out.append(line)
        else:
            cells = _split_cells(line)
            body = _definition_lines(cells[1]) if len(cells) > 1 else []
            if cells[0] == _CONTINUATION_CELL and last_line >= 0:
                if body and not body[0].startswith("- "):
                    out[last_line] = f"{out[last_line]} {body[0]}"
                    body = body[1:]
                out[last_line + 1 : last_line + 1] = body
                last_line += len(body)
            elif body:
                out.append(f"- **{_clean_term(cells[0])}** {body[0]}")
                out.extend(body[1:])
                last_line = len(out) - 1
            else:
                out.append(line)  # unexpected shape - leave it visible
    return "\n".join(out)


# <=== APPENDIX 2: MINIMUM SHARE CAPITAL TABLE ===>
# One 6-column table split into sector groups. Each row becomes one line that keeps the
# column numbers, because rule 2.30 refers to "columns 1 and 2", "column 4", "column 5"
# and "column 6" of Appendix 2. Run after flatten_rule_book_tables.
_APPENDIX_2_START = "**Appendix 2"
_APPENDIX_2_END = "**Appendix 3"
# repeated on every page: "|Column 1|...", "|---|...", "|**Description of activity**|...", "|**Class**|..."
_APPENDIX_2_HEADER_ROW = re.compile(
    r"^\|(?:Column 1|---|\*\*Description of activity|\*\*Class)\b"
)
# turnover bands in the Class 8 row: "a) up to and including £1 million;"
_BAND = re.compile(r"(?:^|\s)([a-e])\)\s+")


def _cell_text(cell: str) -> str:
    # a word hyphenated across a line keeps its hyphen but loses the gap: "sub-<br>underwriter"
    text = re.sub(r"(?<=\w)-<br>(?=\w)", "-", cell)
    text = text.replace("<br>", " ").replace("**", "")
    return re.sub(r"\s+", " ", text).strip()


def _split_bands(text: str) -> tuple[str, list[str]]:
    # "intro a) x b) y" -> ("intro", ["x", "y"]); no bands -> (text, [])
    parts = _BAND.split(text)
    intro = parts[0].strip()
    bands = [parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)]
    return intro, bands


def _capital_row_lines(cells: list[str]) -> list[str]:
    cls, paragraphs, description, qualification, share_capital, net_assets = (
        _cell_text(c) for c in cells
    )
    lead = f"- Class {cls}, paragraph(s) {paragraphs} - {description}"
    if qualification:
        lead = f"{lead}. Qualification or exception (column 4): {qualification}"
    intro, bands = _split_bands(description)
    _, capital_bands = _split_bands(share_capital)
    _, asset_bands = _split_bands(net_assets)
    if bands and len(bands) == len(capital_bands) == len(asset_bands):
        # Class 8: one line per turnover band, pairing the a)-e) values in columns 5 and 6
        lines = [f"- Class {cls}, paragraph(s) {paragraphs} - {intro}"]
        for letter, band, capital, assets in zip(
            "abcde", bands, capital_bands, asset_bands
        ):
            lines.append(
                f"- {letter}) {band.rstrip(';.')}: minimum share capital requirement "
                f"(column 5) {capital}; minimum net tangible asset requirement (column 6) {assets}."
            )
        return lines
    return [
        f"{lead}. Minimum share capital requirement (column 5): {share_capital}. "
        f"Minimum net tangible asset requirement (column 6): {net_assets}."
    ]


def flatten_appendix_2_table(text: str) -> str:
    out: list[str] = []
    in_appendix = False
    # index in `out` of the previous row's line - page headers sit between a row and its
    # page-break continuation, so the continuation is joined there, not onto out[-1]
    last_row = -1
    for line in text.splitlines():
        if line.startswith(_APPENDIX_2_START):
            in_appendix = True
            out.append(line)
        elif line.startswith(_APPENDIX_2_END):
            in_appendix = False
            out.append(line)
        elif not in_appendix or not line.startswith("|"):
            out.append(line)
        elif _APPENDIX_2_HEADER_ROW.match(line):
            continue
        else:
            cells = _split_cells(line)
            if len(cells) != 6:
                out.append(line)  # unexpected shape - leave it visible
            elif len(set(cells)) == 1:
                out.append(
                    f"## **{_cell_text(cells[0])}**"
                )  # sector group, e.g. "Trust services"
            elif not any(cells[:3]) and last_row >= 0:
                # page-break continuation of the previous row's column 4 text
                qualification = _cell_text(cells[3])
                out[last_row] = out[last_row].replace(
                    ". Minimum share capital requirement (column 5)",
                    f" {qualification}. Minimum share capital requirement (column 5)",
                    1,
                )
            else:
                out.extend(_capital_row_lines(cells))
                last_row = len(out) - 1
    return "\n".join(out)


# <=== APPENDIX PAGE HEADERS ===>
# Appendix pages carry the appendix title as a running head, wrapped over up to 3 lines
# with blank lines between, e.g.
#   "Appendix 2 - Minimum" / "Share Capital Requirement" / "etc. (Rule 2.30)"
# The block always ends on the line with the closing bracket (sometimes followed by
# "Financial Services Rule Book 2016"). Plain text only - the real headings are bold
# ("**Appendix 2 - ...") and are left alone.
_APPENDIX_PAGE_HEAD = re.compile(r"^Appendix \d+ - ")
_PAGE_HEAD_END = re.compile(r"\)(?: Financial Services Rule Book 2016)?\s*$")
_PAGE_HEAD_MAX_LINES = 3


def _page_head_end(lines: list[str], start: int) -> int | None:
    # index of the block's closing line, or None if it is not found within the limit
    seen = 0
    for i in range(start, len(lines)):
        line = lines[i].strip()
        if not line:
            continue
        if _PAGE_HEAD_END.search(line):
            return i
        seen += 1
        if seen >= _PAGE_HEAD_MAX_LINES:
            return None
    return None


def strip_appendix_page_heads(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        end = _page_head_end(lines, i) if _APPENDIX_PAGE_HEAD.match(lines[i]) else None
        if end is not None:
            i = end + 1  # drop the whole block
        else:
            out.append(lines[i])
            i += 1
    return "\n".join(out)


# <=== APPENDIX 3: FINANCIAL RESOURCES STATEMENT ===>
# Parts A-E are calculation templates ("X" placeholders) plus Notes 1-19. Output:
#   ## **Net Tangible Assets Calculation**          one heading per calculation table
#   - Less: Goodwill and other intangible assets (see Note 2)
#   ## **Note 5 - Debtors > 90 days**                one heading per note
#   Debtors which are more than 90 days overdue ...
# Notes 4 and 5 arrive as plain text, not table rows: in layout-off mode pymupdf4llm drops
# one-row tables, so the unbox_single_row_note_tables pdf_handler removes their borders.
# Run after flatten_rule_book_tables, before strip_appendix_page_heads.
_APPENDIX_3_START = "**Appendix 3"
_APPENDIX_3_END = "**Appendix 4"
_APPENDIX_3_NOTES = list(range(1, 20))  # Notes 1-19, in this order
# the Part C heading wraps: "**APPENDIX 3 - PART C - ... ANNUAL AUDITED**" / "**EXPENDITURE**"
_PART_HEADING_WRAP = re.compile(
    r"(\*\*APPENDIX 3 - PART [A-E] - [^*\n]+)\*\*\n+\*\*([A-Z ]+)\*\*"
)
_TABLE_ROW_NOTE = re.compile(r"^Note (\d+)(?:<br>)?$")
_PLAIN_NOTE = re.compile(r"^Note (\d+) (.*)$")
_CONTINUATION_CELLS = {"Col1", "Col2"}
_PERCENT = re.compile(r"^\d+%$")
_WHOLE_BOLD = re.compile(r"^\*\*[^*]+\*\*\.?$")


def _note_lines(fragments: list[str]) -> list[str]:
    # like _definition_lines, but a whole-bold fragment (a sub-heading inside a note,
    # e.g. "**Work in progress > 90 days**") starts a new line; consecutive whole-bold
    # fragments are one heading that wrapped, so they are joined
    lines: list[str] = []
    prefix: str | None = None
    previous_bold = False
    for fragment in (f.strip() for f in fragments):
        if not fragment:
            continue
        is_bold = _WHOLE_BOLD.match(fragment) is not None
        if _ENUM_OR_BULLET_ONLY.match(fragment):
            prefix = "- " if fragment == "•" else f"- {fragment} "
        elif prefix is not None:
            lines.append(prefix + fragment)
            prefix = None
        elif fragment.startswith(("• ", "- ")):
            lines.append(f"- {fragment[2:].strip()}")
        elif _ENUM_WITH_TEXT.match(fragment):
            lines.append(f"- {fragment}")
        elif is_bold and previous_bold:
            lines[-1] = f"{lines[-1]} {fragment}"
        elif is_bold:
            lines.append(fragment)
        elif lines:
            lines[-1] = f"{lines[-1]} {fragment}"
        else:
            lines.append(fragment)
        previous_bold = is_bold
    return lines


def _note_title(text: str) -> str:
    # the note's opening bold run(s) - a long bold title wraps into several runs (Note 3) -
    # else a short first sentence ("Capital and Reserves."), else nothing
    bold = re.match(r"^((?:\*\*[^*]+\*\*\s*)+)", text)
    title = bold.group(1).replace("**", "") if bold else text.split(". ")[0]
    title = re.sub(r"\s+", " ", title).strip().rstrip(".")
    title = title.split(". ")[0]  # "Goodwill and other intangible assets. Disallowed."
    return title if len(title) <= 200 else ""


def _check_notes(found: list[int]) -> None:
    # every note must be present and in order, or a page-break continuation gets attached
    # to the wrong note (without Notes 4 and 5, Note 5's second half lands in Note 3)
    if found != _APPENDIX_3_NOTES:
        missing = [n for n in _APPENDIX_3_NOTES if n not in found]
        logger.error("Appendix 3 notes found %s, missing %s", found, missing)
        raise ValueError(
            f"Appendix 3 notes missing {missing} - was the "
            "rule_book_unbox_single_row_note_tables pdf_handler applied?"
        )


def _note_heading(number: str, title: str) -> str:
    return f"## **Note {number} - {title}**" if title else f"## **Note {number}**"


def _calculation_line(cells: list[str], mode: str) -> tuple[str | None, str]:
    # returns (line or None, new Less/Add mode)
    label = _cell_text(cells[0])
    others = [_cell_text(c) for c in cells[1:]]
    if not label:
        return None, mode  # subtotal row with only an "X"
    if label in ("Less:", "Add:"):
        return None, label
    if cells[0].startswith("**"):
        return f"- {label}", ""  # bold total row ends the Less/Add run
    percent = next((c for c in others if _PERCENT.match(c)), None)
    line = f"- {mode} {label}" if mode else f"- {label}"
    if percent:
        line = f"{line} - market value adjustment {percent}"
    return line, mode


def _is_table_title(cells: list[str]) -> bool:
    # a calculation table's title row: its other cells hold only column markers, e.g.
    # "|Net Tangible Assets Calculation|£|£|" or "|Liquid Capital Requirement|Col2|Col3|".
    # Data rows always hold an "X"; "|Adjustments to Expenditure|||" has no marker, so it
    # stays an item. (The "|---|" separators are already gone - flatten_rule_book_tables drops them.)
    if cells[0].startswith("Table I"):
        return True
    if not cells[0] or cells[0].startswith("**"):
        return False
    others = [_cell_text(c) for c in cells[1:]]
    has_marker = any(c in ("£", "Col2", "Col3") for c in others)
    return has_marker and all(c in ("", "£", "Col2", "Col3") for c in others)


def _plain_note_end(line: str) -> bool:
    # a plain-text note (4 or 5) runs until the page footer, a table or a heading
    return line.startswith(("## ", "|", "**APPENDIX", "**Appendix"))


def flatten_appendix_3(text: str) -> str:
    text = _PART_HEADING_WRAP.sub(r"\1 \2**", text)
    lines = text.splitlines()
    out: list[str] = []
    in_appendix = False
    last_note = -1  # index in `out` of the current note's last line
    mode = ""  # "Less:" / "Add:" while inside that part of a calculation
    found: list[int] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if line.startswith(_APPENDIX_3_START):
            in_appendix = True
            out.append(line)
        elif line.startswith(_APPENDIX_3_END):
            in_appendix = False
            out.append(line)
        elif not in_appendix:
            out.append(line)
        elif _PLAIN_NOTE.match(line):
            note = _PLAIN_NOTE.match(line)
            fragments = [note.group(2)]
            while i < len(lines) and not _plain_note_end(lines[i]):
                fragments.append(lines[i])
                i += 1
            out.append(_note_heading(note.group(1), _note_title(note.group(2))))
            found.append(int(note.group(1)))
            out.extend(_note_lines(fragments))
            last_note = len(out) - 1
        elif not line.startswith("|"):
            out.append(
                line
            )  # part headings, page headers (stripped later), blank lines
        elif line.startswith("|---"):
            continue
        else:
            cells = _split_cells(line)
            first = cells[0].replace("<br>", "").strip()
            note = _TABLE_ROW_NOTE.match(cells[0].strip())
            if note and len(cells) == 3:
                # |Note N|title|text|  (Notes 11-19)
                out.append(_note_heading(note.group(1), _cell_text(cells[1])))
                found.append(int(note.group(1)))
                out.extend(_note_lines(cells[2].split("<br>")))
                last_note = len(out) - 1
            elif note:
                # |Note N|text|  (Notes 1-10) - the title is the text's opening
                out.append(
                    _note_heading(
                        note.group(1), _note_title(cells[1].replace("<br>", " "))
                    )
                )
                found.append(int(note.group(1)))
                out.extend(_note_lines(cells[1].split("<br>")))
                last_note = len(out) - 1
            elif first in _CONTINUATION_CELLS and last_note >= 0:
                # page-break continuation of the previous note: |Col1|text| or |Col1|Col2|text|
                more = _note_lines(cells[-1].split("<br>"))
                if (
                    more
                    and not more[0].startswith("- ")
                    and not _WHOLE_BOLD.match(more[0])
                ):
                    out[last_note] = (
                        f"{out[last_note]} {more[0]}"  # sentence carried over the page
                    )
                    more = more[1:]
                out[last_note + 1 : last_note + 1] = more
                last_note += len(more)
            elif _is_table_title(cells):
                out.append(f"## **{_cell_text(cells[0])}**")
                mode = ""
            else:
                calculation, mode = _calculation_line(cells, mode)
                if calculation is not None:
                    out.append(calculation)
    _check_notes(found)
    return "\n".join(out)


# <=== APPENDIX 4: TABLE B (FREE DELIVERIES OF SECURITIES) ===>
# Rows are |no.|nature of counterparty|0-3|4-15|over 15| with the business-day bands in a
# header row of their own. Each row becomes one line:
#   - 2A. A counterparty to whom securities ... Business days since delivery 0-3: 15% of
#     contract or market value; 4-15: ...; over 15: ...
# Merged cells (row 2's 15% spans 0-3 and 4-15) already arrive repeated in each column.
_TABLE_B_HEADING = "**TABLE B (OF APPENDIX 4)**"
_TABLE_B_ROWS = ["1", "2", "2A", "3"]


def _table_b_line(cells: list[str], bands: list[str]) -> str:
    number = _cell_text(cells[0])
    counterparty = _cell_text(cells[1]).rstrip(".")
    values = [
        f"{band}: {_cell_text(value).rstrip('.')}"
        for band, value in zip(bands, cells[2:])
    ]
    return (
        f"- {number}. {counterparty}. Business days since delivery {'; '.join(values)}."
    )


def flatten_appendix_4_table_b(text: str) -> str:
    out: list[str] = []
    in_table = False
    bands: list[str] = []
    rows: list[str] = []
    for line in text.splitlines():
        if line.startswith(_TABLE_B_HEADING):
            in_table = True
            out.append(line)
        elif not in_table or not line.startswith("|"):
            if in_table and rows and line.strip():
                in_table = False  # first text after the table rows
            out.append(line)
        else:
            cells = _split_cells(line)
            if len(cells) != 5:
                out.append(line)  # unexpected shape - leave it visible
            elif "Col2" in cells:
                continue  # "|Nature of counterparty ...|Col2|Business days since delivery|Col4|Col5|"
            elif not cells[0] and not cells[1]:
                bands = [
                    _cell_text(c) for c in cells[2:]
                ]  # "|||**0-3**|**4-15**|**over 15**|"
            else:
                rows.append(_cell_text(cells[0]))
                out.append(_table_b_line(cells, bands))
    if not bands or rows != _TABLE_B_ROWS:
        logger.error("Table B bands %s, rows %s", bands, rows)
        raise ValueError(
            f"Table B expected rows {_TABLE_B_ROWS} with day bands, found {rows}, bands {bands}"
        )
    return "\n".join(out)
