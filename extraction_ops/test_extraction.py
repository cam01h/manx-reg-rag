import re
import difflib
from pathlib import Path
from .models import ToolBelt
from .load_to_md import (
    apply_pdf_handlers,
    check_for_scope_start,
    clean_md_to_lines,
    get_pdf_from_url,
    load_clean_md,
    check_for_scope_end,
    pdf_to_md,
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


def ready_pdf(tools: ToolBelt) -> None:
    get_pdf_from_url(tools)
    apply_pdf_handlers(tools)


def write_clean_and_trimmed(tools: ToolBelt) -> None:
    ready_pdf(tools)
    md = pdf_to_md(tools)
    md_lines = clean_md_to_lines(tools, md)
    clean_md = "\n".join(md_lines)
    # test_regex(md)
    CLEAN_MD.write_text(clean_md)
    logger.info("[%s]: clean.md written", tools.document)
    trimmed_md_lines = trim_md(md_lines, doc)
    TRIMMED_MD.write_text("\n".join(trimmed_md_lines))
    logger.info("[%s]: trimmed.md written", tools.document)


def write_chunks_and_defs(tools: ToolBelt) -> None:
    output = load_clean_md(tools)
    CHUNKS_MD.write_text("\n".join(output.chunk_lines))
    logger.info("[%s]: chunks.md written", tools.document)
    DEFINITIONS_MD.write_text("\n".join(output.definition_lines))
    logger.info("[%s]: definitions.md written", tools.document)


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
        # write_clean_and_trimmed(doc)
        write_chunks_and_defs(doc)
