import re

# the whole document is one two-column table per Part: | rule | guidance |
# each row becomes "## **<rule>**" followed by its guidance as plain paragraphs

# running head and foot on every page
_PAGE_FURNITURE = re.compile(
    r"^(?:Last updated: \w+ \d{4} Page \d+ of \d+|Isle of Man Financial Services Authority)[ \t]*$\n?",
    re.MULTILINE,
)
# "<br> <br>" (or more) is a blank line inside the cell = a real paragraph break.
# a single "<br>" is just the PDF wrapping the line
_PARAGRAPH_BREAK = re.compile(r"<br>\s*(?:<br>\s*)+")
# list bullets come through as "\uf0b7" (Symbol font) or "•", wrapped in <br>s:
#   "links below:<br>\uf0b7 <br>IOM branches ..." / "such as<br>• <br>Regulators;"
_BULLET = re.compile(r"(?:<br>\s*)*[\uf0b7\u2022]\s*(?:<br>)?\s*")


def strip_page_furniture(text: str) -> str:
    return _PAGE_FURNITURE.sub("", text)


def _split_cells(line: str) -> list[str]:
    # strip only the outer pipes so an empty first cell ("||...") is kept
    return [c.strip() for c in line.strip()[1:-1].split("|")]


def _clean_rule_cell(cell: str) -> str:
    # "_2.10 Annual financial statements of parent and_<br>_holding companies_"
    # "<br>_8.9 Conflicts of interest policy_" / "_6.25_ _Distribution of ..._"
    cell = cell.replace("<br>", " ").replace("_", "").replace("**", "")
    return re.sub(r"\s+", " ", cell).strip()


def _paragraphs(cell: str) -> list[str]:
    paragraphs = []
    cell = _BULLET.sub("<br><br>- ", cell)
    for chunk in _PARAGRAPH_BREAK.split(cell):
        chunk = re.sub(r"\s+", " ", chunk.replace("<br>", " ")).strip()
        if chunk:
            paragraphs.append(chunk)
    return paragraphs


def _is_continuation(cells: list[str]) -> bool:
    # a row that runs over a page break restarts on the next page with an empty rule cell,
    # which pymupdf4llm sometimes labels "Col1"
    return cells[0] in ("", "Col1")


def _is_header_row(cells: list[str]) -> bool:
    # "|Introductory|Guidance|" and the "|---|---|" separator that follows it
    return cells[0] == "---" or cells[1] == "Guidance"


# rows unboxed by the pdf handler come through as plain text, the rule cell in italics:
#   "_2.30 Financial resources requirements_"
#   "_3.12 Reconciliation_ This rule details the requirement ..."
_UNBOXED_RULE = re.compile(r"^_(\d\.\d{1,2}[A-Z]? [^_]+)_(.*)$")
_LIST_ITEM = re.compile(r"^\d+\. ")
_SENTENCE_END = (".", ":", ";")


def _starts_paragraph(previous: str, line: str) -> bool:
    # plain text keeps the PDF's line wraps. A line only starts a new paragraph if it is a
    # list item or the line before it finished a sentence
    if not previous.strip() or previous.startswith("## "):
        return True
    return bool(_LIST_ITEM.match(line)) or previous.endswith(_SENTENCE_END)


def promote_unboxed_rules(text: str) -> str:
    out: list[str] = []
    in_unboxed = False
    for line in text.splitlines():
        match = _UNBOXED_RULE.match(line)
        if match is not None:
            in_unboxed = True
            out.extend(["", f"## **{match.group(1).strip()}**"])
            line = match.group(2)
        elif line.startswith(("|", "## ")):
            in_unboxed = False
        if not in_unboxed:
            out.append(line)
            continue
        line = line.strip()
        if not line:
            # blank lines here are list-item spacing, not paragraph breaks
            continue
        if _starts_paragraph(out[-1], line):
            out.extend(["", line])
        else:
            out[-1] = f"{out[-1]} {line}"
    return "\n".join(out)


def flatten_guidance_tables(text: str) -> str:
    out: list[str] = []
    for line in text.splitlines():
        if not line.startswith("|") or line.count("|") != 3:
            out.append(line)
            continue
        cells = _split_cells(line)
        if _is_header_row(cells):
            continue
        paragraphs = _paragraphs(cells[1])
        if not paragraphs:
            continue
        if _is_continuation(cells):
            # drop the blank lines left behind by the page furniture
            while out and not out[-1].strip():
                out.pop()
            # mid-sentence page break (starts lowercase) rejoins the last paragraph
            if paragraphs[0][0].islower() and out:
                out[-1] = f"{out[-1]} {paragraphs.pop(0)}"
        else:
            out.extend(["", f"## **{_clean_rule_cell(cells[0])}**"])
        for paragraph in paragraphs:
            out.extend(["", paragraph])
    return "\n".join(out)
