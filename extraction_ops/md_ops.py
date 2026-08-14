import logging
from pathlib import Path
from typing import Callable, cast

import pymupdf4llm

from extraction_ops.models import CleanOutPut, ToolBelt


logger = logging.getLogger(__name__)


def pdf_to_md(pdf_path: Path, doc: str, use_ocr: bool) -> str:
    logger.info("Loading [%s] to md", doc)
    try:
        md = cast(
            str,
            pymupdf4llm.to_markdown(
                pdf_path, header=False, footer=False, use_ocr=use_ocr
            ),
        )
    except Exception:
        logger.exception("failed pymupdf4llm conversion")
        raise
    return md


def clean_md_to_lines(cleaner: Callable[[str], str], md: str) -> list[str]:
    md = cleaner(md)
    return md.splitlines()


def check_for_scope_start(
    doc: str, start_marker: Callable[[str], bool], in_scope: bool, line: str
) -> bool:
    if start_marker(line):
        if in_scope:
            logger.warning(
                "trimmer.start found two matching lines in [%s]. line:[%s]",
                doc,
                line,
            )
            raise ValueError("two line match trimmer.start")
        return True
    return False


def check_if_in_definitions_section(
    tools: ToolBelt, in_definition_section: bool, def_idx: int, line: str
) -> tuple[bool, int]:
    if tools.definition_tools is None:
        return False, def_idx
    markers_list = tools.definition_tools.section_markers
    if def_idx >= len(markers_list):
        if def_idx > len(markers_list):
            logger.critical("index of definition section exceeded range")
            raise ValueError("index of definition section excceded range")
        return False, def_idx
    marker = tools.definition_tools.section_markers[def_idx]
    if not in_definition_section:
        if marker.start(line):
            logger.debug(
                "line recognised as start of definition section [%d]: [%s]",
                def_idx,
                line,
            )
            return True, def_idx
        return False, def_idx
    else:
        if marker.end(line):
            logger.debug(
                "line recognised as end of definition section [%d]: [%s]", def_idx, line
            )
            return False, def_idx + 1
        return True, def_idx


def check_for_scope_end(end_marker: Callable[[str], bool], line: str) -> bool:
    if end_marker(line):
        logger.debug("detected final line: [%s]", line)
        return True
    return False


def normalise_serial_new_lines(lines: list[str]) -> list[str]:
    previous_line = ""
    kept_lines = []
    for i, line in enumerate(lines):
        if i == 0:
            previous_line = line
            kept_lines.append(line)
        else:
            if not previous_line.strip() and not line.strip():
                continue
            kept_lines.append(line)
            previous_line = line
    return kept_lines


def build_output(chunk_lines: list[str], definition_lines: list[str]) -> CleanOutPut:
    output = CleanOutPut(chunk_lines=chunk_lines, definition_lines=definition_lines)
    return output


def process_lines(md_lines: list[str], tools: ToolBelt) -> CleanOutPut:
    chunk_lines = []
    definition_lines = []

    in_scope = False
    in_definition_section = False
    def_idx = 0

    for line in md_lines:
        if check_for_scope_start(tools.document, tools.trimmer.start, in_scope, line):
            in_scope = True

        def_idx_buffer = def_idx
        in_definition_section, def_idx = check_if_in_definitions_section(
            tools, in_definition_section, def_idx, line
        )
        belongs_to_definitions = in_definition_section or def_idx != def_idx_buffer

        if check_for_scope_end(tools.trimmer.end, line):
            (definition_lines if belongs_to_definitions else chunk_lines).append(line)
            break
        if in_scope:
            (definition_lines if belongs_to_definitions else chunk_lines).append(line)
    else:
        logger.warning("no end line detected")

    if not in_scope:
        logger.critical("no start line detected")
        raise ValueError(f"no start line detected in {tools.document}")
    if in_definition_section:
        logger.warning("scope ended while in definition section [%d]", def_idx)

    elif tools.definition_tools is not None and def_idx != len(
        tools.definition_tools.section_markers
    ):
        logger.warning(
            "[%d] definitions found when [%d] expected",
            def_idx,
            len(tools.definition_tools.section_markers),
        )

    chunk_lines = normalise_serial_new_lines(chunk_lines)
    definition_lines = normalise_serial_new_lines(definition_lines)
    logger.info("[%d] definition lines found", len(definition_lines))
    logger.info("[%d] chunk lines found", len(chunk_lines))
    output = build_output(chunk_lines, definition_lines)

    logger.info("[%s] Extracted to md.", tools.document)

    return output


def pdf_to_output(tools: ToolBelt) -> CleanOutPut:
    md = pdf_to_md(tools.pdf_path, tools.document, tools.use_ocr)
    clean_md_lines = clean_md_to_lines(tools.clean_text, md)
    return process_lines(clean_md_lines, tools)
