import argparse
import logging
from pathlib import Path

from utils import build_path, read_md

from extraction_ops import TOOLBELT_REGISTRY

logger = logging.getLogger(__name__)

_STAGES_NOT_CHAINED = []  # fill in as added

_STAGES = {}  # fill in as i add stages


def loader(doc: str, consumes: str) -> str | Path:
    suffix_consumed = _STAGES[consumes].suffix
    path = build_path(consumes, doc, "golden", suffix_consumed)
    if suffix_consumed == "md":
        return read_md(path)
    elif suffix_consumed == "pdf":
        return path
    else:
        logger.error("[%s] is not a valid file type", suffix_consumed)
        raise TypeError(f"[{suffix_consumed}] is not a valid file type")


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
        output = _STAGES[key].opperation(doc, output)
    return output


def get_input(doc: str, current_stage: str, source: str):
    consumes = _STAGES[current_stage].consumes
    if consumes is None:
        return None
    if source == "from_golden":
        return loader(doc, consumes)
    return runner(doc, current_stage)


def write_file(doc: str, stage: str, mode: str, output) -> None:
    path = build_path(stage, doc, mode, _STAGES[stage].suffix)
    text = _STAGES[stage].to_text(output)
    path.write_text(text)


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
    output = stage.opperation(args.doc, input)
    if args.mode == "test_golden":
        stage.test_golden(args.doc, output)
    else:
        write_file(args.doc, args.stage, args.mode, output)
