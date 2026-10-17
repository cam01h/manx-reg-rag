import argparse
import logging
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from config import setup_logging
from extraction_ops import TOOLBELT_REGISTRY

from .clean_md import CleanMd
from .definitions import Definitions
from .handled_pdf import HandledPdf
from .normalise_sections import NormSections
from .process_lines import ChunkLines, DefLines
from .raw_md import RawMd
from .raw_pdf import RawPdf
from .seg_by_head import Headers, Sections
from .segment_by_definitions import DefSegs
from .term_variants import Variants
from .trimmed import Trimmed
from .utils import build_path, read_md, write_json, write_md

logger = logging.getLogger(__name__)


_STAGES = {
    "raw_pdf": RawPdf,
    "handled_pdf": HandledPdf,
    "raw_md": RawMd,
    "clean": CleanMd,
    "trimmed": Trimmed,
    "chunk_lines": ChunkLines,
    "def_lines": DefLines,
    "raw_sections": Sections,
    "headers": Headers,
    "norm_sections": NormSections,
    "def_segs": DefSegs,
    "definitions": Definitions,
    "variants": Variants,
}

_STAGES_NOT_CHAINED = [
    "raw_pdf",
    "handled_pdf",
    "raw_md",
]  # fill in as added


def loader(doc: str, consumes: str) -> str | Path | list[Any]:
    stage_consumed = _STAGES[consumes]
    if stage_consumed.model is not None:
        path = build_path(consumes, doc, suffix="json")
        return TypeAdapter(list[stage_consumed.model]).validate_json(read_md(path))
    path = build_path(consumes, doc, suffix=stage_consumed.suffix)
    if stage_consumed.suffix == "md":
        return read_md(path)
    elif stage_consumed.suffix == "pdf":
        return path
    else:
        logger.error("[%s] is not a valid file type", stage_consumed.suffix)
        raise TypeError(f"[{stage_consumed.suffix}] is not a valid file type")


def chain(current_stage: str) -> list[str]:
    if current_stage in _STAGES_NOT_CHAINED:
        logger.error("cannot chain in pdf stages")
        raise ValueError("cannot chain in pdf stages")
    keys = [current_stage]
    consumes = _STAGES[current_stage].consumes
    while consumes is not None and consumes not in _STAGES_NOT_CHAINED:
        keys.append(consumes)
        consumes = _STAGES[consumes].consumes
    return list(reversed(keys))


def runner(doc: str, current_stage: str):
    keys = chain(current_stage)
    seed_from = _STAGES[keys[0]].consumes
    output = loader(doc, seed_from) if seed_from else None
    for key in keys[:-1]:
        output = _STAGES[key].operation(doc, output)
    return output


def get_input(doc: str, current_stage: str, source: str):
    consumes = _STAGES[current_stage].consumes
    if consumes is None:
        return None
    if source == "from_golden":
        return loader(doc, consumes)
    return runner(doc, current_stage)


def write_file(doc: str, stage: str, mode: str, output) -> None:
    stage_object = _STAGES[stage]
    path = build_path(stage, doc, mode, stage_object.suffix)
    if stage_object.suffix == "pdf":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(output)
    elif stage_object.suffix == "md":
        if stage_object.to_text:
            json_path = build_path(stage, doc, mode, "json")
            write_json(json_path, output)
            text = stage_object.to_text(output)
            write_md(path, text)
        else:
            write_md(path, output)
    else:
        logger.error("[%s] is not a valid file type", stage_object.suffix)
        raise TypeError(f"[{stage_object.suffix}] is not a valid file type")


def build_cli():
    parser = argparse.ArgumentParser(
        description="Diagnostics CLI to isolate each step of the ingestion pipeline when adding or refreshing new imports"
    )
    parser.add_argument(
        "stage", choices=_STAGES.keys(), help="The diagnostic stage you want to run"
    )
    parser.add_argument(
        "doc", choices=TOOLBELT_REGISTRY.keys(), help="the name of the document"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "-c",
        dest="source",
        action="store_const",
        const="chain",
        help="Chain-Mode runs from the first .md file extracted from the PDF",
    )
    source.add_argument(
        "-f",
        dest="source",
        action="store_const",
        const="from_golden",
        help="Runs this tage based on the colden file output from the previous stage",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "-r",
        dest="mode",
        action="store_const",
        const="test",
        help="writes a test file for inspection",
    )
    mode.add_argument(
        "-g",
        dest="mode",
        action="store_const",
        const="golden",
        help="Writes a golden file",
    )
    mode.add_argument(
        "-t",
        dest="mode",
        action="store_const",
        const="test_golden",
        help="runs a stage according to mode and tests against existing golden file",
    )
    return parser.parse_args()


def main():
    args = build_cli()
    stage = _STAGES[args.stage]
    input = get_input(args.doc, args.stage, args.source)
    output = stage.operation(args.doc, input)
    if args.mode == "test_golden":
        stage.test_golden(args.doc, output)
    else:
        write_file(args.doc, args.stage, args.mode, output)


if __name__ == "__main__":
    setup_logging("diagnostics")
    main()
