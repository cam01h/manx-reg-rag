import re
from scripts.extraction_specs.config import project_root


def re_steps(text: str) -> str:
    text = re.sub(r"^\|.*\|$\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text


AML_HANDBOOK = {
    "document": "The AML Handbook (April 2026)",
    "input_path": project_root / "data/raw/custom/aml_handbook_april_2026.pdf",
    "md_path": project_root / "data/processed/raw_handbook.md",
    "chunk_path": project_root / "data/processed/handbook_chunks.jsonl",
    "def_path": project_root / "data/processed/handbook_defs.json",
    "hierarchy": "guidnace",
    "major": "chapter",
    "minor": "paragraph",
    "start_line": 173,
    "end_line": 5933,
    "defs_start": 0,
    "defs_end": None,
    "re_steps": re_steps,
    "is_major": None,  # lambda line: line.startswith("## **PART"),
    "is_minor": None,  # lambda line: line.startswith("## **") and line[5].isdigit(),
    "is_def_line": None,  # lambda line: ('- **"' in line or '## **"' in line or line.startswith('**"')),
    "is_dub_def_line": None,  # lambda segs: len(segs) == 5 and segs[2].strip() in ("or", "and"),
    "is_f_dub_def": None,  # lambda segs: len(segs) == 5 and segs[2].strip() != "or",
    "re_pack_splitter": None,  # lambda text: re.split(r"\n(?=- \(\d+\))", text),
    "strip_md": lambda line: line.replace("## **", "").replace("**", "").strip(),
    "h_strip_md": lambda line: (
        line.replace("- **", "")
        .replace("##", "")
        .replace("**", "")
        .replace(" — ", "")
        .strip()
    ),
}
