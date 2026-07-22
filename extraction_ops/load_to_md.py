import pymupdf4llm
from typing import cast
from .models import CleanOutPut, ToolBelt
import logging


logger = logging.getLogger(__name__)


def pdf_to_clean_md(tools: ToolBelt) -> list[str]:
    logger.info("Loading [%s] to md", tools.document)
    try:
        md = cast(
            str,
            pymupdf4llm.to_markdown(
                tools.pdf_path, header=False, footer=False, use_ocr=tools.use_ocr
            ),
        )
    except Exception:
        logger.exception("failed pymupdf4llm conversion")
        raise
    if tools.pdf_handlers is not None:
        for i, hanldler in enumerate(tools.pdf_handlers):
            try:
                hanldler(tools.pdf_path)
            except:
                logger.critical("failed to complete pdf_handler idx[%d]", i)
                raise
    md = tools.clean_text(md)
    md_lines = md.splitlines()
    return md_lines


def check_for_scope_start(tools: ToolBelt, in_scope: bool, line: str) -> bool:
    if tools.trimmer.start(line):
        if in_scope:
            logger.warning(
                "trimmer.start found two matching lines in [%s]. line:[%s]",
                tools.document,
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


def check_for_scope_end(tools: ToolBelt, line: str) -> bool:
    if tools.trimmer.end(line):
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


def load_clean_md(tools: ToolBelt) -> CleanOutPut:
    md_lines = pdf_to_clean_md(tools)
    chunk_lines = []
    definition_lines = []

    in_scope = False
    in_definition_section = False
    def_idx = 0

    for line in md_lines:
        if check_for_scope_start(tools, in_scope, line):
            in_scope = True

        def_idx_buffer = def_idx
        in_definition_section, def_idx = check_if_in_definitions_section(
            tools, in_definition_section, def_idx, line
        )
        belongs_to_definitions = in_definition_section or def_idx != def_idx_buffer

        if check_for_scope_end(tools, line):
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
