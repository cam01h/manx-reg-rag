from dataclasses import dataclass
from pathlib import Path
from typing import Callable


# used on individual chunks removed from the text
@dataclass(frozen=True)
class Chunk:
    chunk_id: str  # chunk id created her and not in embeddings.py, TODO: body will need to be rehashed in split_chunk and merge
    document: str
    hierarchy: str
    usage_note_ids: list[str]
    headers: list[str]
    body: str
    terms_used: list[str] | None = None


# used on individual defintions as extracted
@dataclass(frozen=True)
class Defintion:
    term: str
    scope: str
    defintion: str


# tools used for defintion extraction
@dataclass(frozen=True)
class DefinitionTools:
    # split list of trimmed lines using regex pattern, this is less brittle and likely to survive update better
    definitions_start: list[Callable[[list[str]], list[str]]]
    definitions_end: list[Callable[[list[str]], list[str]]]
    scope: str
    has_definition_section: bool
    is_definition_line: Callable[[str], bool] | None
    is_double_def_line: (
        Callable[[list[str]], bool]
        | None  # used for 'the terms "x" and "Y" should be taken to mean...'
    )
    is_false_dub_def: (
        Callable[[list[str]], bool] | None
    )  # looks like a double definition line but is not


# tools and variables used for ingestion pipeline
@dataclass(frozen=True)
class ToolBelt:
    document: str
    hierarchy: str
    usage_note_id: str
    usage_note_prompt: str
    usage_note_finder: Callable[
        [list[str], dict[list[str], dict[str, str]]], str | None
    ]  # check if header list is in keys of manual dict, if true then append the usage note_id. this allows for section level usage notes
    input_url: str
    pdf_path: Path
    # split list of all lines using regex pattern, this is less brittle and likely to survive update better
    start_line: Callable[[list[str]], list[str]]
    end_line: Callable[[list[str]], list[str]]
    definition_tools: DefinitionTools | None
    re_steps: Callable[[str], str]
    header_matchers: list[Callable[[str], bool]]
    re_pack_splitter: Callable[[str], list[str]]
    strip_md: Callable[[str], str]
    header_strip_md: Callable[[str], str]
