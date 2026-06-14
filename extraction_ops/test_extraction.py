import pymupdf4llm
import difflib
import httpx
from .specs.specs import DocSpecs
from typing import cast
from pathlib import Path
from extraction_ops.specs.aml_handbook import AmlHandbook
from extraction_ops.specs.aml_code import AmlCode
from extraction_ops.specs.supplemental_information_document import (
    SupplementalInformation,
)
from config import CLEAN_MD, CHUNKS_MD, DEFINITIONS_MD, TRIMMED_MD


def write_diff(before: Path, after: Path, write_path: Path) -> None:
    text_before = before.read_text()  # whatever you had previously
    text_after = after.read_text()  # after the new regex

    diff = difflib.unified_diff(
        text_before.splitlines(),
        text_after.splitlines(),
        lineterm="",
        n=2,  # context lines (lines of unchanged content around each change)
    )

    write_path.write_text("\n---\n".join(diff))


def get_pdf_from_url(specs: DocSpecs) -> None:
    print("downloading pdf...")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
        }
        response = httpx.get(
            url=specs.input_url, timeout=20, follow_redirects=True, headers=headers
        )
        response.raise_for_status()
    except httpx.HTTPError:
        print("download fail")
        raise
    if not response.content.startswith(b"%PDF"):
        print("empty file downloaded")
        raise ValueError(f"{specs.document} did not return a pdf")
    try:
        with open(specs.input_path, "wb") as f:
            f.write(response.content)
        print("pdf downloaded")
    except Exception:
        raise


def load_clean_md(specs: DocSpecs) -> list[str]:
    md = cast(
        str, pymupdf4llm.to_markdown(specs.input_path, header=False, footer=False)
    )
    md = specs.re_steps(md)
    md = md.replace("“", '"').replace("”", '"')
    md_lines = md.splitlines()
    return md_lines


def load_clean_trimmed_md(specs: DocSpecs) -> list[str]:
    try:
        md = cast(
            str, pymupdf4llm.to_markdown(specs.input_path, header=False, footer=False)
        )
    except Exception:
        raise
    md = specs.re_steps(md)
    md = md.replace("“", '"').replace("”", '"')
    md_lines = md.splitlines()
    trimmed_lines = md_lines[specs.start_line : specs.end_line]
    return trimmed_lines


if __name__ == "__main__":
    # comment out all but one for testing
    docs = [
        # AmlCode,
        # AmlHandbook,
        SupplementalInformation
    ]
    for doc in docs:
        get_pdf_from_url(doc)
        clean_md_lines = load_clean_md(doc)
        CLEAN_MD.write_text("\n".join(clean_md_lines))
        trimmed_md_lines = load_clean_trimmed_md(doc)
        TRIMMED_MD.write_text("\n".join(trimmed_md_lines))
        chunk_lines = (
            trimmed_md_lines[: doc.definitions_start]
            + trimmed_md_lines[doc.definitions_end :]
        )
        CHUNKS_MD.write_text("\n".join(chunk_lines))
        definition_lines = trimmed_md_lines[doc.definitions_start : doc.definitions_end]
        DEFINITIONS_MD.write_text("\n".join(definition_lines))
