from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class DocSpecs:
    document: str
    input_path: Path
    md_path: Path
    definition_path: Path
    hierarchy: str
    major: str  # TODO: needst to replaced before write to JSONL
    major_name: str
    minor: str
    minor_name: str
    start_line: int
    end_line: int
    definitions_start: int
    definitions_end: int
    re_steps: Callable
    is_major_header_line: Callable
    is_minor_header_line: Callable
    has_definition_section: bool
    is_definition_line: bool
    is_double_def_line: (
        bool  # useed for 'the terms "x" and "Y" should be taken to mean...'
    )
    is_f_dub_def: bool  # looks like a double definition line but is not
    re_pack_splitter: Callable
    strip_md: Callable
    h_strip_md: Callable
