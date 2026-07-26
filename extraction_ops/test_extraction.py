import pymupdf4llm
import re
import difflib
import httpx
from typing import cast
from pathlib import Path
from .models import ToolBelt
from .load_to_md import (
    apply_pdf_handlers,
    check_for_scope_start,
    load_clean_md,
    check_for_scope_end,
    pdf_to_clean_md,
)

# from .toolbelts.aml_code import AmlCode
from .toolbelts.aml_handbook.aml_handbook import AmlHandbook
from config import CLEAN_MD, CHUNKS_MD, DEFINITIONS_MD, TRIMMED_MD, setup_logging
import logging

logger = logging.getLogger(__name__)


def write_diff(before: Path, after: Path, write_path: Path) -> None:
    text_before = before.read_text()  # whatever you had previously
    text_after = after.read_text()  # after the new regex

    diff = difflib.unified_diff(
        text_before.splitlines(),
        text_after.splitlines(),
        lineterm="",
        n=2,  # context lines (lines of unchanged content around each change)
    )

    write_path.write_text("\n---\n".join(diff))


def get_pdf_from_url(tools: ToolBelt) -> None:
    print(f"downloading pdf: [{tools.document}]")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
        }
        response = httpx.get(
            url=tools.input_url, timeout=20, follow_redirects=True, headers=headers
        )
        response.raise_for_status()
    except httpx.HTTPError:
        print("download fail")
        raise
    if not response.content.startswith(b"%PDF"):
        print("empty file downloaded")
        raise ValueError(f"{tools.document} did not return a pdf")
    try:
        with open(tools.pdf_path, "wb") as f:
            f.write(response.content)
        print("pdf downloaded")
    except Exception:
        raise


def load_md(tools: ToolBelt) -> str:
    if tools.pdf_handlers is not None:
        for hanldler in tools.pdf_handlers:
            try:
                hanldler(tools.pdf_path)
            except:
                print("failed to complete pdf_handler")
                raise
    md = cast(
        str,
        pymupdf4llm.to_markdown(
            tools.pdf_path, header=False, footer=False, use_ocr=tools.use_ocr
        ),
    )
    return md


def test_regex(md: str):
    lines = md.splitlines()
    affected_lines = [
        line
        for line in lines
        if re.match(r"\n(?=\d+[A-Z]?\.\s*\(\d+\)|\(\d+\)\s)", line)
    ]
    for line in affected_lines:
        print(line)


def trim_md(md_lines: list[str], tools: ToolBelt) -> list[str]:
    kept_lines = []
    in_scope = False
    for line in md_lines:
        if check_for_scope_start(tools, in_scope, line) and not in_scope:
            in_scope = True
        if in_scope:
            if check_for_scope_end(tools, line):
                kept_lines.append(line)
                break
            kept_lines.append(line)
    return kept_lines


if __name__ == "__main__":
    setup_logging("test_extraction")
    # comment out all but one for testing
    docs = [
        # AmlCode,
        AmlHandbook,
        # SupplementalInformation,
        # Poca,
        # TerrorismAndCrime,
        # FiuAct,
        # RegulatedActivitiesOrder
        # Dbroa,
        # FinancialRestrictionsAct,
        # SanctionsAct
    ]
    for doc in docs:
        get_pdf_from_url(doc)
        apply_pdf_handlers(doc)
        md_lines = pdf_to_clean_md(doc)
        clean_md = "\n".join(md_lines)
        # test_regex(md)
        CLEAN_MD.write_text(clean_md)
        trimmed_md_lines = trim_md(md_lines, doc)
        TRIMMED_MD.write_text("\n".join(trimmed_md_lines))
        output = load_clean_md(doc)
        CHUNKS_MD.write_text("\n".join(output.chunk_lines))
        DEFINITIONS_MD.write_text("\n".join(output.definition_lines))
