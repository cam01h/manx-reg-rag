import re
from scripts.extraction_specs.config import project_root


def re_steps(text: str) -> str:
    text = re.sub(r"\[\d+\]", "", text)  # inline footnote references
    text = re.sub(
        r"^> \d+ .*$\n?", "", text, flags=re.MULTILINE
    )  # blockquoted footnotes
    text = re.sub(
        r"^\d+ (Section|SD) .*$\n?", "", text, flags=re.MULTILINE
    )  # footnotes
    return text


AML_CODE = {
    "document": "The AML Code 2019",
    "input_path": project_root / "data/raw/custom/the_aml_code_2019.pdf",
    "md_path": project_root / "data/processed/raw_code.md",
    "chunk_path": project_root / "data/processed/raw_code.jsonl",
    "def_path": project_root / "data/processed/code_defs.json",
    "hierarchy": "legislation",
    "major": "part",
    "minor": "paragraph",
    "start_line": 87,
    "end_line": 1867,
    "defs_start": 11,
    "defs_end": 379,
    "re_steps": re_steps,
    "is_major": lambda line: line.startswith("## **PART"),
    "is_minor": lambda line: line.startswith("## **") and line[5].isdigit(),
    "is_def_line": lambda line: (
        '- **"' in line or '## **"' in line or line.startswith('**"')
    ),
    "is_dub_def_line": lambda lines: len(lines) == 5 and lines[2].strip() == "or",
    "is_f_dub_def": lambda lines: len(lines) == 5 and lines[2].strip() != "or",
    "strip_md": lambda line: line.replace("## **", "").replace("**", "").strip(),
    "h_strip_md": lambda line: (
        line.replace("- **", "")
        .replace("##", "")
        .replace("**", "")
        .replace(" — ", "")
        .strip()
    ),
}
