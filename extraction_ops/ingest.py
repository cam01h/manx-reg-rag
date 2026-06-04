from dataclasses import asdict, replace
import pymupdf4llm
import json
from typing import Callable, cast
from .chunk import Chunk
from .specs.aml_handbook import AmlHandbook
from .specs.aml_code import AmlCode
from .specs.specs import DocSpecs
from config import (
    CHUNKS_JSONL_PATH,
    DEFINITIONS_JSONL_PATH,
    DELETE_LEN,
    MAX_CHUNK_CHAR,
    MIN_CHUNK_CHAR,
    TARGET_CHUNK_CHAR,
)


def load_clean_md(specs: DocSpecs) -> list[str]:
    print(f"Loading {specs.document} to md...")
    md = cast(
        str, pymupdf4llm.to_markdown(specs.input_path, header=False, footer=False)
    )
    md_lines = md.splitlines()
    trimmed_lines = md_lines[specs.start_line : specs.end_line]
    md = "\n".join(trimmed_lines)
    md = specs.re_steps(md)
    md = md.replace("“", '"').replace("”", '"')
    trimmed_lines = md.splitlines()
    print("Extraction complete.")
    return trimmed_lines


def re_pack_oversized_chunk(chunk: Chunk, splitter: Callable) -> list[Chunk]:
    if len(chunk.body) < MAX_CHUNK_CHAR:
        return [chunk]
    # TODO: Unsplittable chunks slip through oversized, maybe add a fallback splitter
    segments = splitter(chunk.body)
    if len(segments) == 1:
        return [chunk]

    split_chunks = []
    buffer = ""

    def flush(body: str):
        split_chunks.append(replace(chunk, body=body.strip()))

    for s in segments:
        if len(s) > MAX_CHUNK_CHAR:
            print(f"Unsplittable chunk over sized at {len(s)} characters")
        if buffer != "" and len(buffer + s) > MAX_CHUNK_CHAR:
            flush(buffer)
            buffer = s
        else:
            buffer += "\n" + s
    if buffer != "":
        flush(buffer)
    return split_chunks


def extract_definitions(specs: DocSpecs, lines: list[str]) -> dict[str, str]:
    if not (
        specs.is_definition_line is not None
        and specs.is_double_def_line is not None
        and specs.is_false_dub_def is not None
    ):
        return {}

    print(f"{specs.document}: formatting defintions...")
    definitions = {}
    keys = []
    v = ""

    for line in lines:
        if not line.strip():
            continue
        if specs.is_definition_line(line):
            if v != "" and keys != []:
                for k in keys:
                    definitions[k] = v
            keys = []
            v = ""
            def_line = line.split('"')
            for i, w in enumerate(def_line):
                def_line[i] = specs.h_strip_md(w)
            if len(def_line) == 3:
                keys.append(def_line[1])
                v = def_line[2]
            if len(def_line) == 5:
                if specs.is_double_def_line(def_line):
                    keys.append(def_line[1])
                    keys.append(def_line[3])
                    v = def_line[4]
                elif specs.is_false_dub_def(def_line):
                    keys.append(def_line[1])
                    v = f'{def_line[2]} "{def_line[3]}" {def_line[4]}'
        else:
            v += "\n" + specs.strip_md(line)
    if v != "" and keys != []:
        for k in keys:
            definitions[k] = v
    print(f"{len(definitions)} definitions have been formatted.")
    return definitions


def extract_doc(specs: DocSpecs, lines: list[str]) -> list[Chunk]:
    print(f"{specs.document}: formatting chunks...")
    if specs.has_definition_section:
        lines = lines[: specs.definitions_start] + lines[specs.definitions_end :]

    def pack_chunk(major: str, minor: str, body: str) -> Chunk:
        current_chunk = Chunk(
            document=specs.document,
            hierarchy=specs.hierarchy,
            major=major,
            minor=minor,
            body=body.strip(),
        )
        return current_chunk

    buffer = ""
    chunks = []
    major = ""
    minor = ""

    for line in lines:
        if specs.is_major_header_line(line):
            if buffer.strip() != "":
                chunks.append(pack_chunk(major, minor, buffer))
                buffer = ""
            major = specs.strip_md(line)
        elif specs.is_minor_header_line(line):
            if buffer.strip() != "":
                chunks.append(pack_chunk(major, minor, buffer))
                buffer = ""
            minor = specs.strip_md(line)
        else:
            buffer += "\n" + line
    chunks.append(pack_chunk(major, minor, buffer))
    print(f"{len(chunks)} initial chunks were fromatted.")
    return chunks


def filter_chunks(chunks: list[Chunk]) -> list[Chunk]:
    filtered_chunks = []
    delted_chunks = 0
    for c in chunks:
        if len(c.body) >= DELETE_LEN:
            filtered_chunks.append(c)
        else:
            delted_chunks += 1
    print(f"{delted_chunks} chunks were filtered")
    return filtered_chunks


def attach_definitions(chunks: list[Chunk], definitions: dict) -> list[Chunk]:
    print("Attaching definitions to chunks...")
    chunks_with_terms = []
    terms_used = []
    for chunk in chunks:
        for term in definitions.keys():
            if term in chunk.body:
                terms_used.append(term)
        chunks_with_terms.append(replace(chunk, terms_used=terms_used))
        terms_used = []
    print("Definitions attached.")
    return chunks_with_terms


def re_pack_undersized_chunks(chunks: list[Chunk]) -> list[Chunk]:

    def should_merge(chunk: Chunk, previous_chunk: Chunk) -> bool:
        is_too_short = len(chunk.body) < MIN_CHUNK_CHAR
        not_at_boundary = (
            chunk.major == previous_chunk.major and chunk.minor == previous_chunk.minor
        )
        previous_chunk_not_too_big = (
            len(previous_chunk.body) + len(chunk.body) < TARGET_CHUNK_CHAR
        )
        return is_too_short and not_at_boundary and previous_chunk_not_too_big

    checked_chunks = []
    previous_chunk = None
    for chunk in chunks:
        if previous_chunk is not None:
            if should_merge(chunk, previous_chunk):
                # TODO: undersized chunks following a large chunk never merge. Accepted for now
                previous_chunk = replace(
                    previous_chunk,
                    body=f"{previous_chunk.body}\n\n{chunk.minor} - {chunk.body}",
                )
            else:
                if previous_chunk is not None:
                    checked_chunks.append(previous_chunk)
                previous_chunk = chunk
        else:
            previous_chunk = chunk
    if previous_chunk:
        checked_chunks.append(previous_chunk)
    if len(chunks) != len(checked_chunks):
        print(f"{len(chunks)} were merged into {len(checked_chunks)}")
    else:
        print("No chunks were merged")
    return checked_chunks


if __name__ == "__main__":
    docs = [
        AmlCode,
        AmlHandbook,
    ]
    all_chunks = []
    all_definitions = {}
    for doc in docs:
        md = load_clean_md(doc)
        chunks = extract_doc(doc, md)
        chunks = [
            out
            for c in chunks
            for out in re_pack_oversized_chunk(c, doc.re_pack_splitter)
        ]
        chunks = re_pack_undersized_chunks(chunks)
        chunks = filter_chunks(chunks)
        print(f"{len(chunks)} chunks after normalisation")
        if doc.has_definition_section:
            definitions = extract_definitions(doc, md)
            chunks = attach_definitions(chunks, definitions)
            all_definitions[doc.document] = definitions
        all_chunks.extend(chunks)
    with CHUNKS_JSONL_PATH.open("w") as f:
        for c in all_chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
    print(f"Across all documents, {len(all_chunks)} were extracted")
    with DEFINITIONS_JSONL_PATH.open("w") as f:
        json.dump(all_definitions, f, ensure_ascii=False, indent=2)
    defintions = 0
    for defs in all_definitions:
        defintions += len(defs)
    print(f"Across all documents, {len(all_definitions)} were formatted")
