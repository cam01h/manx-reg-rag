import pymupdf4llm
import json
from typing import Callable, cast
from scripts.extraction_specs.aml_handbook import AML_HANDBOOK
from config import (
    DELETE_LEN,
    MAX_CHUNK_CHAR,
    MIN_CHUNK_CHAR,
    TARGET_CHUNK_CHAR,
)
from scripts.extraction_specs.aml_code import AML_CODE


def load_clean_md(specs: dict) -> list[str]:
    print(f"Loading {specs['document']} to md...")
    md = cast(
        str, pymupdf4llm.to_markdown(specs["input_path"], header=False, footer=False)
    )
    md_lines = md.splitlines()
    trimmed_lines = md_lines[specs["start_line"] : specs["end_line"]]
    md = "\n".join(trimmed_lines)
    md = specs["re_steps"](md)
    md = md.replace("“", '"').replace("”", '"')
    trimmed_lines = md.splitlines()
    print("Extraction complete.")
    return trimmed_lines


def re_pack_oversized_chunk(chunk: dict, splitter: Callable) -> list[dict]:
    if len(chunk["body"]) < MAX_CHUNK_CHAR:
        return [chunk.copy()]
    segments = splitter(
        chunk["body"]
    )  # TODO: Unsplittable chunks slip through oversized, maybe add a fallback splitter
    if len(segments) == 1:
        return [chunk.copy()]
    chunks = []
    buffer = ""
    for s in segments:
        if len(s) > MAX_CHUNK_CHAR:
            print(f"Unsplittable chunk over sized at {len(s)} characters")
        if buffer != "" and len(buffer + s) > MAX_CHUNK_CHAR:
            chunk_copy = chunk.copy()
            chunk_copy["body"] = buffer.strip()
            chunks.append(chunk_copy)
            buffer = s
        else:
            buffer += "\n" + s
    if buffer != "":
        chunk_copy = chunk.copy()
        chunk_copy["body"] = buffer.strip()
        chunks.append(chunk_copy)
    return chunks


def extract_definitions(specs: dict, lines: list[str]) -> dict[str, str]:
    print(f"{specs['document']}: formatting defintions...")
    definitions = {}
    keys = []
    v = ""
    for line in lines:
        if not line.strip():
            continue
        if specs["is_def_line"](line):
            if v != "" and keys != []:
                for k in keys:
                    definitions[k] = v
            keys = []
            v = ""
            def_line = line.split('"')
            for i, w in enumerate(def_line):
                def_line[i] = specs["h_strip_md"](w)
            if len(def_line) == 3:
                keys.append(def_line[1])
                v = def_line[2]
            if len(def_line) == 5:
                if specs["is_dub_def_line"](def_line):
                    keys.append(def_line[1])
                    keys.append(def_line[3])
                    v = def_line[4]
                elif specs["is_f_dub_def"](def_line):
                    keys.append(def_line[1])
                    v = f'{def_line[2]} "{def_line[3]}" {def_line[4]}'
        else:
            v += "\n" + specs["strip_md"](line)
    if v != "" and keys != []:
        for k in keys:
            definitions[k] = v
    print(f"{len(definitions)} definitions have been formatted.")
    return definitions


def extract_doc(specs: dict, lines: list[str]) -> list[dict]:
    print(f"{specs['document']}: formatting chunks...")
    if specs["has_def_section"]:
        lines = lines[: specs["defs_start"]] + lines[specs["defs_end"] :]

    buffer = ""
    chunks = []
    major = ""
    minor = ""
    chunk = {
        "document": specs["document"],
        "hierarchy": specs["hierarchy"],
        specs["major"]: "",
        specs["minor"]: "",
        "body": "",
    }

    for line in lines:
        if specs["is_major"](line):
            if buffer.strip() != "":
                chunk[specs["major"]] = major  # TODO: repeated 3 times: extract to func
                chunk[specs["minor"]] = minor
                chunk["body"] = buffer.strip()
                chunks.extend(
                    re_pack_oversized_chunk(chunk.copy(), specs["re_pack_splitter"])
                )
                buffer = ""
            major = specs["strip_md"](line)
        elif specs["is_minor"](line):
            if buffer.strip() != "":
                chunk[specs["major"]] = major
                chunk[specs["minor"]] = minor
                chunk["body"] = buffer.strip()
                repacked = re_pack_oversized_chunk(
                    chunk.copy(), specs["re_pack_splitter"]
                )
                chunks.extend(repacked)
                buffer = ""
            minor = specs["strip_md"](line)
        else:
            buffer += "\n" + line
    chunk[specs["major"]] = major
    chunk[specs["minor"]] = minor
    chunk["body"] = buffer.strip()
    repacked = re_pack_oversized_chunk(chunk.copy(), specs["re_pack_splitter"])
    chunks.extend(repacked)
    filtered_chunks = []
    delted_chunks = 0
    for (
        c
    ) in chunks:  # TODO: this is aggressive and runs before merge: needs further work
        if len(c["body"]) >= DELETE_LEN:
            filtered_chunks.append(c)
        else:
            delted_chunks += 1
    print(f"{delted_chunks} were filtered")
    print(f"{len(filtered_chunks)} chunks were fromatted.")
    return filtered_chunks


def attach_definitions(chunks: list[dict], definitions: dict) -> list[dict]:
    print("Attaching definitions to chunks...")
    terms_used = []
    for chunk in chunks:
        for term in definitions.keys():
            if term in chunk["body"]:
                terms_used.append(term)
        chunk["terms_used"] = terms_used
        terms_used = []
    print("Definitions attached.")
    return chunks


def re_pack_undersized_chunks(specs: dict, chunks: list[dict]) -> list[dict]:

    def should_merge(chunk: dict[str, str], previous_chunk: dict) -> bool:
        if previous_chunk != {}:
            is_too_short = len(chunk["body"]) < MIN_CHUNK_CHAR
            not_at_boundary = (
                chunk[specs["major"]] == previous_chunk[specs["major"]]
                and chunk[specs["minor"]] == previous_chunk[specs["minor"]]
            )
            previous_chunk_not_too_big = (
                len(previous_chunk["body"]) + len(chunk["body"]) < TARGET_CHUNK_CHAR
            )
            return is_too_short and not_at_boundary and previous_chunk_not_too_big
        return False

    checked_chunks = []
    previous_chunk = {}
    for chunk in chunks:
        if should_merge(
            chunk, previous_chunk
        ):  # TODO: undersized chunks following a large chunk never merge. Accepted for now
            previous_chunk["body"] = (
                f"{previous_chunk['body']}\n\n{chunk[specs['minor']]} - {chunk['body']}"
            )
        else:
            if previous_chunk:
                checked_chunks.append(previous_chunk.copy())
            previous_chunk = chunk.copy()
    if previous_chunk:
        checked_chunks.append(previous_chunk.copy())
    print(f"{len(chunks)} were repacked into {len(checked_chunks)}")
    return checked_chunks


if __name__ == "__main__":
    # TODO: change from dict to class
    docs = [
        AML_CODE,
        AML_HANDBOOK,
    ]
    for doc in docs:
        md = load_clean_md(doc)
        chunks = extract_doc(doc, md)
        chunks = re_pack_undersized_chunks(
            doc, chunks
        )  # TODO: pull all chunk sizing funcs together in order
        if doc["has_def_section"]:
            definitions = extract_definitions(doc, md)
            chunks = attach_definitions(chunks, definitions)
            with doc["def_path"].open("w") as f:
                json.dump(definitions, f, ensure_ascii=False, indent=2)
        with doc["chunk_path"].open("w") as f:
            for c in chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
