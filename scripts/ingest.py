import pymupdf4llm
import json
import re
from typing import cast
from scripts.extraction_specs.config import MAX_CHUNK_CHAR
from scripts.extraction_specs.aml_code import AML_CODE


def extract_definitions(defs_lines: list) -> dict[str, str]:
    for line in defs_lines:
        line = line.replace("“", '"').replace("”", '"')
    definitions = {}
    k = ""
    v = ""
    for line in defs_lines:
        if not line.strip():
            continue
        if '- **"' in line or '## **"' in line or line.startswith('**"'):
            if k != "" and v != "":
                definitions[k] = v
                k = ""
                v = ""
            def_line = line.split('"')
            for i, w in enumerate(def_line):
                def_line[i] = (
                    w.replace("- **", "")
                    .replace("##", "")
                    .replace("**", "")
                    .replace(" — ", "")
                    .strip()
                )
            if len(def_line) == 3:
                k = def_line[1]
                v = def_line[2]
            if len(def_line) == 5:
                if def_line[2].strip() == "or":
                    k = f'"{def_line[1]}" {def_line[2]} "{def_line[3]}"'
                    v = def_line[4]
                else:
                    k = def_line[1]
                    v = f'{def_line[2]} "{def_line[3]}" {def_line[4]}'
        else:
            v += "\n" + line.replace("**", "").strip()
    return definitions


def re_pack_chunk(chunk: dict) -> list[dict]:
    if len(chunk["body"]) < MAX_CHUNK_CHAR:
        return [chunk.copy()]
    segments = re.split(r"\n(?=- \(\d+\))", chunk["body"])
    if len(segments) == 1:
        print(
            f"Warning: {chunk['paragraph']} is over length at {len(chunk['body'])} characters"
        )
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

    for i, c in enumerate(chunks):
        if len(c["body"]) > MAX_CHUNK_CHAR:
            print(
                f"Warning: {c['paragraph']} chunk number {i + 1} is over length at {len(c['body'])} characters"
            )

    return chunks


# TODO: extract logic to function calls
def extract_doc(specs: dict):
    print(f"Extracting {specs['document']}...")
    md = cast(
        str, pymupdf4llm.to_markdown(specs["input_path"], header=False, footer=False)
    )
    md_lines = md.splitlines()
    md_lines = md_lines[specs["start_line"] : specs["end_line"]]
    md = "\n".join(md_lines)
    md = specs["re_steps"](md)

    # output to md for human read able output / TODO: comment out later
    specs["md_path"].write_text(md)

    lines = md.splitlines()
    defs_lines = lines[specs["defs_start"] : specs["defs_end"]]
    chunk_lines = lines[: specs["defs_start"]] + lines[specs["defs_end"] :]

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
    current_chunk = chunk.copy()

    for line in chunk_lines:
        if specs["is_major"](line):
            if (
                buffer.strip() != ""
            ):  # flushes chunk on part lines as long as buffer not empty
                current_chunk[specs["major"]] = major
                current_chunk[specs["minor"]] = minor
                current_chunk["body"] = buffer.strip()
                chunks.extend(re_pack_chunk(current_chunk))
                buffer = ""
            major = specs["strip_md"](line)
        elif specs["is_minor"](
            line
        ):  # flushes chunk on para lines as long as buffer not empty
            if buffer.strip() != "":
                current_chunk[specs["major"]] = major
                current_chunk[specs["minor"]] = minor
                current_chunk["body"] = buffer.strip()
                repacked = re_pack_chunk(current_chunk)
                chunks.extend(repacked)
                buffer = ""
            minor = specs["strip_md"](line)
        else:
            buffer += "\n" + line
    current_chunk["body"] = buffer.strip()
    repacked = re_pack_chunk(current_chunk)
    chunks.extend(repacked)

    definition_dict = extract_definitions(defs_lines)
    with specs["def_path"].open("w") as f:
        json.dump(definition_dict, f, ensure_ascii=False, indent=2)

    with specs["chunk_path"].open("w") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"{specs['document']} extracted")


if __name__ == "__main__":
    extract_doc(AML_CODE)
