import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any, cast

import fitz

from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.models import CleanSection
from tests.extraction_ops.diagnostics.models import Stage
from tests.extraction_ops.diagnostics.utils import make_md_golden_test

logger = logging.getLogger(__name__)

_STAGE = "coverage"

"""<=== HOW MUCH OF THE PDF SURVIVES INTO THE SECTIONS ===>"""

# Every run of three consecutive words in the PDF's own text layer is looked for in the
# normalised sections (headers and bodies). A run that is missing is text that was dropped,
# garbled, or deliberately removed (contents pages, footnotes, chart labels, page furniture,
# text outside the trimmer, and definition sections, which go to definitions not sections).
# "Prose" counts only lines set in the document's body text size, which leaves out tables
# and charts, whose cells legitimately reorder when flattened - a missing prose run is
# almost always a real loss worth reading.

_HEADER_FOOTER_BAND = (50, 760)
_SHOW_RUNS = 25
_MIN_RUN = 4


def _key(word: str) -> str:
    return re.sub(r"[^a-z0-9]", "", word.lower())


def _pdf_words(pdf_path: Path) -> list[tuple[int, str, bool]]:
    """(page, key, is_prose) for every word in the text layer, in content order."""
    lines = []
    sizes: Counter[float] = Counter()
    with fitz.open(pdf_path) as doc:
        for page_no in range(1, doc.page_count + 1):
            page = doc.load_page(page_no - 1)
            for block in cast(dict[str, Any], page.get_text("dict"))["blocks"]:
                for line in block.get("lines", []):
                    if (
                        not _HEADER_FOOTER_BAND[0]
                        < line["bbox"][1]
                        < _HEADER_FOOTER_BAND[1]
                    ):
                        continue
                    # superscript footnote markers (flag bit 0) are not part of the text
                    spans = [
                        s
                        for s in line["spans"]
                        if s["text"].strip() and not s["flags"] & 1
                    ]
                    if not spans:
                        continue
                    text = "".join(s["text"] for s in spans)
                    size = round(max(s["size"] for s in spans), 1)
                    sizes[size] += len(text)
                    lines.append((page_no, text, size))
    body_size = sizes.most_common(1)[0][0] if sizes else 0
    words = []
    for page_no, text, size in lines:
        # body size and a little larger (intro paragraphs), never the smaller table text
        prose = body_size - 0.6 <= size <= body_size + 1.6
        for word in text.split():
            key = _key(word)
            if key:
                words.append((page_no, key, prose))
    return words


def _report(
    pdf_words: list[tuple[int, str, bool]], sections: list[CleanSection]
) -> str:
    text = "\n".join("\n".join(s.headers) + "\n" + s.body for s in sections)
    keys = [k for k in (_key(w) for w in text.split()) if k]
    grams = set(zip(keys, keys[1:], keys[2:]))

    missing = [
        i
        for i in range(len(pdf_words) - 2)
        if tuple(w[1] for w in pdf_words[i : i + 3]) not in grams
    ]
    missing_set = set(missing)
    prose_total = sum(1 for w in pdf_words if w[2])
    prose_missing = sum(1 for i in missing if pdf_words[i][2])

    runs: list[list[int]] = []
    for i in missing:
        if runs and i <= runs[-1][1] + 1:
            runs[-1][1] = i
        else:
            runs.append([i, i])
    prose_runs = [r for r in runs if pdf_words[r[0]][2] and r[1] - r[0] + 1 >= _MIN_RUN]
    prose_runs.sort(key=lambda r: r[0] - r[1])
    by_page = Counter(pdf_words[i][0] for i in missing_set)

    def pct(part: int, whole: int) -> str:
        return f"{100 * part / whole:.2f}%" if whole else "n/a"

    md = [
        "# Coverage",
        "",
        f"All text: [{len(missing)}] of [{len(pdf_words)}] three-word runs missing ({pct(len(missing), len(pdf_words))})",
        f"Prose: [{prose_missing}] of [{prose_total}] three-word runs missing ({pct(prose_missing, prose_total)})",
        "",
        "## Pages with the most missing runs",
        "",
    ]
    md.extend(f"- page {page}: {count}" for page, count in by_page.most_common(15))
    md.extend(["", f"## Longest missing prose runs (at least {_MIN_RUN} words)", ""])
    for start, end in prose_runs[:_SHOW_RUNS]:
        words = " ".join(w[1] for w in pdf_words[start : end + 3])
        md.append(f"- page {pdf_words[start][0]} ({end - start + 1} words): {words}")
    return "\n".join(md)


def _opperation(doc: str, input: list[CleanSection]) -> str:
    tools = TOOLBELT_REGISTRY[doc]
    report = _report(_pdf_words(tools.pdf_path), input)
    for line in report.splitlines()[2:4]:
        logger.info(line)
    return report


Coverage = Stage(
    suffix="md",
    consumes="norm_sections",
    operation=_opperation,
    test_golden=make_md_golden_test(_STAGE),
    to_text=None,
)
