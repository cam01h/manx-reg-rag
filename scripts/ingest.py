import pymupdf4llm
import json
import re
from pathlib import Path
from typing import cast
from globals import (
    AML_CODE_RAW_PATH,
    AML_CODE_MD_PATH,
    AML_CODE_JSONL_PATH,
    MAX_CHUNK_CHAR,
)


def re_pack_chunk(chunk: dict) -> list[dict]:
    if len(chunk["body"]) < MAX_CHUNK_CHAR:
        return [chunk]
    segments = re.split(r"\n(?=- \(\d+\))", chunk["body"])
    if len(segments) == 1:
        print(
            f"Warning: {chunk['paragraph']} is over length at {len(chunk['body'])} characters"
        )
        return [chunk]
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
def aml_code_extract(input_path: Path, output_path: Path):
    print("Extracting AML Code 2019...")
    md = cast(str, pymupdf4llm.to_markdown(input_path, header=False, footer=False))
    start_marker = "The Department of Home Affairs makes the following Code under section 157 of the Proceeds of Crime Act 2008 and section 68 of the Terrorism and Other Crime (Financial . Restrictions) Act 2014, after carrying out the consultation required by those sections[1] "
    md = md.split(start_marker, 1)[1]
    end_marker = "## **43 Revocations** "
    md = md.split(end_marker, 1)[0]
    md = re.sub(r"\[\d+\]", "", md)  # inline footnote references
    md = re.sub(r"^> \d+ .*$\n?", "", md, flags=re.MULTILINE)  # footnotes

    # output to md for human read able output / TODO: comment out later
    AML_CODE_MD_PATH.write_text(md)

    lines = md.splitlines()
    document = "The AML/CFT Code 2019"
    hierarchy = "legislation"
    part = ""
    paragraph = ""
    chunks = []
    buffer = ""
    for line in lines:
        if line.startswith("## **PART"):
            if buffer.strip() != "":
                current_chunk = {
                    "document": document,
                    "hierarchy": hierarchy,
                    "part": part,
                    "paragraph": paragraph,
                    "body": buffer.strip(),
                }
                chunks.extend(re_pack_chunk(current_chunk))
                buffer = ""
            part = line.replace("## **", "").replace("**", "")
        elif line.startswith("## **") and line[5].isdigit():
            if buffer.strip() != "":
                current_chunk = {
                    "document": document,
                    "hierarchy": hierarchy,
                    "part": part,
                    "paragraph": paragraph,
                    "body": buffer.strip(),
                }
                repacked = re_pack_chunk(current_chunk)
                chunks.extend(repacked)
                buffer = ""
            paragraph = line.replace("## **", "").replace("**", "")
        else:
            buffer += "\n" + line
    chunk = {
        "document": document,
        "hierarchy": hierarchy,
        "part": part,
        "paragraph": paragraph,
        "body": buffer.strip(),
    }
    repacked = re_pack_chunk(chunk)
    chunks.extend(repacked)

    with output_path.open("w") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print("AML Code 2019 extracted")


if __name__ == "__main__":
    aml_code_extract(AML_CODE_RAW_PATH, AML_CODE_JSONL_PATH)
