import re

BULLET = "\uf0b7"


def _clean_cell(c: str) -> str:
    c = c.replace("<br>" + BULLET, "; ")  # bullet = list-item boundary
    c = c.replace(BULLET, "; ")  # bullet at cell start
    c = c.replace("<br>", " ")  # remaining <br> = line-wrap artifact
    c = c.replace("**", "")
    c = re.sub(r"\s+", " ", c).strip()
    return re.sub(r"^;\s*", "", c)  # drop leading separator


def _flatten_row(line: str) -> str:
    cells = [_clean_cell(c) for c in line.strip().strip("|").split("|")]
    method = cells[0] if cells else ""
    consid = cells[1] if len(cells) > 1 else ""
    if not method:
        return ""  # |||
    if method.lower() in ("example method", "method"):
        return ""  # header
    if set(method) <= set("-"):
        return ""  # separator
    return (f"{method} — {consid}" if consid else method).strip()


def flatten_tables(text: str) -> str:
    out = []
    for line in text.splitlines():
        if line.startswith("|"):
            row = _flatten_row(line)
            if row:
                out.append(row)
        else:
            out.append(line)
    return "\n".join(out)
