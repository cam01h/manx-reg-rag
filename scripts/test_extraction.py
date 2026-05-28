import pymupdf4llm
from typing import cast

from scripts.extraction_specs.aml_handbook import AML_HANDBOOK
from scripts.extraction_specs.config import MD_1, MD_2


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


if __name__ == "__main__":
    docs = [
        # AML_CODE,
        AML_HANDBOOK,
    ]
    for doc in docs:
        md_lines = load_clean_md(doc)
        MD_1.write_text("\n".join(md_lines))
        # definition_lines = trimmed_lines[: doc["defs_start"]] + trimmed_lines[doc["defs_end"] :]
        # MD_2.write_text("\n".join(definition_lines))
