import pymupdf4llm
import json
import re
from pathlib import Path
from typing import cast
from globals import AML_CODE_RAW_PATH, AML_CODE_MD_PATH, AML_CODE_JSONL_PATH


def aml_code_extract(input_path, output_path):
    print("Extracting AML Code 2019...")
    md = cast(str, pymupdf4llm.to_markdown(input_path, header=False, footer=False))
    start_marker = "The Department of Home Affairs makes the following Code under section 157 of the Proceeds of Crime Act 2008 and section 68 of the Terrorism and Other Crime (Financial . Restrictions) Act 2014, after carrying out the consultation required by those sections[1] "
    md = md.split(start_marker, 1)[1]
    end_marker = "## **43 Revocations** "
    md = md.split(end_marker, 1)[0]
    md = re.sub(r"\[\d+\]", "", md)  # inline footnote references
    md = re.sub(r"^> \d+ .*$\n?", "", md, flags=re.MULTILINE)  # footnotes

    # output to md for human read able output / TODO: comment out later
    md_outpath = Path(AML_CODE_MD_PATH)
    with md_outpath.open("w") as f:
        f.write(md)

    lines = md.splitlines()
    document = "The AML/CFT Code 2019"
    hierarchy = "legislation"
    part = ""
    paragraph = ""
    chunks = []
    buffer = ""
    for line in lines:
        if line.startswith("## **PART"):
            part = line.replace("## **", "").replace("**", "")
        elif line.startswith("## **"):
            if buffer != "":
                current_chunk = {
                    "document": document,
                    "hierarchy": hierarchy,
                    "part": part,
                    "paragraph": paragraph,
                    "body": buffer.strip(),
                }
                chunks.append(current_chunk)
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
    chunks.append(chunk)

    with output_path.open("w") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print("AML Code 2019 extracted")


if __name__ == "__main__":
    aml_code_extract(AML_CODE_RAW_PATH, AML_CODE_JSONL_PATH)
