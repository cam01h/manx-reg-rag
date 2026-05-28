import pymupdf4llm
import json
from typing import Callable, cast
from scripts.extraction_specs.aml_handbook import AML_HANDBOOK
from scripts.extraction_specs.config import MAX_CHUNK_CHAR
from scripts.extraction_specs.aml_code import AML_CODE


def load_clean_md(specs: dict) -> list[str]:
    print(f"Loading {specs['document']} to md...")
    md = cast(
        str, pymupdf4llm.to_markdown(specs["input_path"], header=False, footer=False)
    )
    md = specs["re_steps"](md)
    md = md.replace("“", '"').replace("”", '"')
    md_lines = md.splitlines()
    trimmed_lines = md_lines[specs["start_line"] : specs["end_line"]]
    print("Extraction complete.")
    return trimmed_lines


def re_pack_chunk(chunk: dict, splitter: Callable) -> list[dict]:
    if len(chunk["body"]) < MAX_CHUNK_CHAR:
        return [chunk.copy()]
    segments = splitter(chunk["body"])
    if len(segments) == 1:
        return [chunk.copy()]
    chunks = []
    buffer = ""
    for s in segments:
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
                chunk[specs["major"]] = major
                chunk[specs["minor"]] = minor
                chunk["body"] = buffer.strip()
                chunks.extend(re_pack_chunk(chunk.copy(), specs["re_pack_splitter"]))
                buffer = ""
            major = specs["strip_md"](line)
        elif specs["is_minor"](line):
            if buffer.strip() != "":
                chunk[specs["major"]] = major
                chunk[specs["minor"]] = minor
                chunk["body"] = buffer.strip()
                repacked = re_pack_chunk(chunk.copy(), specs["re_pack_splitter"])
                chunks.extend(repacked)
                buffer = ""
            minor = specs["strip_md"](line)
        else:
            buffer += "\n" + line
    chunk["body"] = buffer.strip()
    repacked = re_pack_chunk(chunk.copy(), specs["re_pack_splitter"])
    chunks.extend(repacked)
    # for i, c in enumerate(chunks):
    # print(f"{i + 1}. {c[specs[minor]]}: {len(c['body'])} characters in chunk")
    print(f"{len(chunks)} chunks were fromatted.")
    return chunks


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


if __name__ == "__main__":
    docs = [
        AML_CODE,
        AML_HANDBOOK,
    ]
    for doc in docs:
        md = load_clean_md(doc)
        definitions = extract_definitions(doc, md)
        chunks = extract_doc(doc, md)
        chunks = attach_definitions(chunks, definitions)
        with doc["chunk_path"].open("w") as f:
            for c in chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        with doc["def_path"].open("w") as f:
            json.dump(definitions, f, ensure_ascii=False, indent=2)
