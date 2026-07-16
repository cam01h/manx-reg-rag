from dataclasses import dataclass
from pathlib import Path
from typing import Callable


# used on individual chunks removed from the text
@dataclass(frozen=True)
class Chunk:
    chunk_id: str  # chunk id created her and not in embeddings.py, TODO: body will need to be hashed in normalise_chunks
    document: str
    hierarchy: str
    usage_note_ids: list[str]
    headers: list[str]
    body: str
    terms_used: list[str] | None = None


# used on individual defintions as extracted
@dataclass(frozen=True)
class Definition:
    document: str
    scope: str
    term: str
    definition: str
    # TODO: add nested definied terms


# TODO: replace slicing by index with a for loop that walk the doc using an in_range and in_definition bool/toggles to dictate where the line is disguarded, appended to chunk_line or definition_lines
# used for marking the trim at the start/end of the doc and start/end of the defintion sections
@dataclass(frozen=True)
class SectionMarkers:
    start: Callable[[str], bool]
    end: Callable[[str], bool]


# tools used for defintion extraction
@dataclass(frozen=True)
class DefinitionTools:
    # split list of trimmed lines using regex pattern, this is less brittle and likely to survive update better
    section_markers: list[SectionMarkers]
    definition_scope: str
    is_definition_line: Callable[[str], bool]
    # used for 'the terms "x" and "Y" should be taken to mean...'
    is_double_def_line: Callable[[list[str]], bool]
    # looks like a double definition line but is not
    is_false_dub_def: Callable[[list[str]], bool]


# primary can just split chunk.body but fallback can carry intro to second chunk for lists that require the intro eg. "(3) the following are exempt:"
@dataclass(frozen=True)
class ChunkSplitters:
    primary: Callable[[str], list[str]]
    fallback: Callable[[str], list[str]]


# tools and variables used for ingestion pipeline
@dataclass(frozen=True)
class ToolBelt:
    document: str
    hierarchy: str
    # check if header list is in keys of manual dict, if true then append the usage note_id. this allows for section level usage notes
    # input is None as it will used variables defined in the same file
    usage_notes: dict[str, str] | None
    input_url: str
    pdf_path: Path
    # split list of all lines using regex pattern, this is less brittle than hardcoded index and likely to survive update better
    trimmer: SectionMarkers
    header_matchers: list[Callable[[str], bool]]
    definition_tools: DefinitionTools | None
    clean_text: Callable[
        [str], str
    ]  # include md = md.replace("“", '"').replace("”", '"')
    re_pack_splitters: ChunkSplitters
    clean_body: Callable[[str], str]
    clean_header: Callable[[str], str]


@dataclass(frozen=True)
class CleanOutPut:
    chunk_lines: list[str]
    definition_lines: list[str]
