from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class DocSpecs:
    document: str
    hierarchy: str
    input_url: str
    input_path: Path
    major_name: str  # TODO: needst to replaced before write to JSONL
    minor_name: str
    start_line: int
    end_line: int
    definitions_start: int | None
    definitions_end: int | None
    re_steps: Callable[[str], str]
    header_matchers: list[Callable[[str], bool]]
    has_definition_section: bool
    is_definition_line: Callable[[str], bool] | None
    is_double_def_line: (
        Callable[[list[str]], bool]
        | None  # useed for 'the terms "x" and "Y" should be taken to mean...'
    )
    is_false_dub_def: (
        Callable[[list[str]], bool] | None
    )  # looks like a double definition line but is not
    re_pack_splitter: Callable[[str], list[str]]
    strip_md: Callable[[str], str]
    h_strip_md: Callable[[str], str]
