import logging
import re

from config import MAX_CHUNK_CHAR

logger = logging.getLogger(__name__)

"""<=== MARKDOWN TABLES ===>"""

# The NRAs carry much of their substance in tables (risk ratings, scores, country exposure).
# A md table is one long block with no blank lines, so the chunker can only cut it mid-row
# and the rows lose their column headings. Each row is rewritten as a self-describing line
# ("- Sector: Banking; 2020: Medium; 2026: Medium High") and long tables are cut into blocks
# that each repeat the table's caption.

_TABLE_BLOCK = re.compile(r"(?:^\|.*\|[ \t]*(?:\n|$))+", re.MULTILINE)
_SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")
_CAPTION = re.compile(
    r"^\*\*(?:Fig(?:ure)?|Key for|Case Stud|Typology)\b.*\*\*$", re.IGNORECASE
)
_PAGE_NUMBER = re.compile(r"^\d{1,3}$")
_GLOSSARY_HEADER = re.compile(r"(?:term|acronym|abbreviation)", re.IGNORECASE)
# cut tables a little under the chunk ceiling so a caption and a row or two can follow
_BLOCK_CHARS = MAX_CHUNK_CHAR - 300


def _cell(text: str) -> str:
    text = text.replace("<br>", " ").replace("**", "")
    return re.sub(r"\s+", " ", text).strip()


def parse_table(block: str) -> tuple[list[str] | None, list[list[str]]]:
    lines = [line.strip() for line in block.strip().split("\n") if line.strip()]
    rows = [[_cell(c) for c in line.strip("|").split("|")] for line in lines]
    header = None
    if len(rows) > 1 and all(_SEPARATOR_CELL.match(c) or not c for c in rows[1]):
        header = rows[0]
        rows = rows[2:]
    rows = [r for r in rows if not all(_SEPARATOR_CELL.match(c) or not c for c in r)]
    width = max((len(r) for r in rows), default=0)
    if header is not None and len(header) < width:
        # the label column usually has no heading of its own: "|2020|2021|" over "|Retail|18.5|20.5|"
        header = [""] * (width - len(header)) + header
    return header, rows


def split_group_header(
    header: list[str] | None, rows: list[list[str]]
) -> tuple[str | None, list[str] | None, list[list[str]]]:
    """A header row that repeats one label across every column is a group title spanning
    the table ("Retail & Private Banking"); the real column headings are the next row."""
    labels = {c for c in (header or []) if c}
    if len(labels) == 1 and len([c for c in header or [] if c]) > 1 and rows:
        return labels.pop(), rows[0], rows[1:]
    return None, header, rows


def is_contents_table(header: list[str] | None, rows: list[list[str]]) -> bool:
    cells = (header or []) + [r[0] for r in rows if r]
    if any(c.lower() == "contents" for c in cells):
        return True
    numbered = [r for r in rows if r and _PAGE_NUMBER.match(r[-1])]
    return len(rows) >= 4 and len(numbered) / len(rows) >= 0.6


def render_row(header: list[str] | None, row: list[str]) -> str:
    cells = [c for c in row if c]
    if not cells:
        return ""
    if len(cells) == 1:
        # a row that only labels the rows below it, eg "Financial Institutions"
        return f"{cells[0]}:"
    if header and any(header):
        pairs = [(h, v) for h, v in zip(header, row) if v]
        first_h, first_v = pairs[0]
        if not first_h:
            rest = "; ".join(f"{h}: {v}" if h else v for h, v in pairs[1:])
            return f"- {first_v}: {rest}"
        return "- " + "; ".join(f"{h}: {v}" if h else v for h, v in pairs)
    return f"- {cells[0]}: {'; '.join(cells[1:])}"


def _blocks(lines: list[str], caption: str | None) -> str:
    blocks: list[str] = []
    current: list[str] = []
    size = 0
    for line in lines:
        if current and size + len(line) > _BLOCK_CHARS:
            blocks.append("\n".join(current))
            current, size = [], 0
        if not current and caption:
            heading = caption if not blocks else f"{caption[:-2]} (continued)**"
            current.append(heading)
            size += len(heading)
        current.append(line)
        size += len(line) + 1
    if current:
        blocks.append("\n".join(current))
    return "\n\n".join(blocks)


def flatten_tables(md: str) -> str:
    paragraphs = re.split(r"\n\s*\n", md)
    out: list[str] = []
    for para in paragraphs:
        if not para.lstrip().startswith("|"):
            out.append(para)
            continue
        # a paragraph can hold text lines above the table (eg its caption)
        pieces = _TABLE_BLOCK.split(para)
        tables = _TABLE_BLOCK.findall(para)
        lead = pieces[0].strip()
        for k, table in enumerate(tables):
            header, rows = parse_table(table)
            group, header, rows = split_group_header(header, rows)
            caption = None
            if lead and _CAPTION.match(lead.split("\n")[-1]):
                caption = lead.split("\n")[-1]
                lead = "\n".join(lead.split("\n")[:-1]).strip()
            elif not lead and out and _CAPTION.match(out[-1].strip()):
                caption = out.pop().strip()
            if lead:
                out.append(lead)
            if group:
                caption = (
                    f"**{caption.strip('*')} - {group}**" if caption else f"**{group}**"
                )
            if is_contents_table(header, rows):
                logger.debug("contents table dropped")
            else:
                lines = [line for line in (render_row(header, r) for r in rows) if line]
                if lines:
                    out.append(_blocks(lines, caption))
                elif caption:
                    out.append(caption)
            lead = pieces[k + 1].strip() if k + 1 < len(pieces) else ""
        if lead:
            out.append(lead)
    return "\n\n".join(out)


"""<=== GLOSSARY ===>"""

# Every NRA ends with a two column glossary ("Key Agency/Term/Acronym | Meaning"). Its rows
# become definition lines in the shape the definitions parser expects: "TERM" meaning


def _unquote(text: str, replacement: str) -> str:
    # quotes inside a glossary row would be read as further terms by the definitions parser
    return re.sub(r'["\u201c\u201d]', replacement, text)


def glossary_to_definitions(md: str) -> str:
    out: list[str] = []
    last_end = 0
    in_glossary = False
    for match in _TABLE_BLOCK.finditer(md):
        between = md[last_end : match.start()]
        out.append(between)
        header, rows = parse_table(match.group())
        starts = bool(
            header and len(header) == 2 and _GLOSSARY_HEADER.search(header[0])
        )
        # a glossary carried onto the next page arrives as a new table without the
        # "Term | Meaning" header - its first row is a term
        continues = (
            in_glossary
            and not between.strip()
            and len((header or rows[0]) if rows or header else []) == 2
        )
        if starts or continues:
            if continues and header and not starts:
                rows = [header] + rows
            out.append(
                "\n".join(
                    f'"{_unquote(term, "")}" {_unquote(meaning, chr(39))}'
                    for term, meaning in (r[:2] for r in rows if len(r) >= 2)
                    if term and meaning
                )
                + "\n"
            )
            in_glossary = True
        else:
            out.append(match.group())
            in_glossary = False
        last_end = match.end()
    out.append(md[last_end:])
    return "".join(out)
