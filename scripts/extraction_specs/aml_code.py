import re
from config import project_root
from specs import DocSpecs


def re_steps(text: str) -> str:
    text = re.sub(r"\[\d+\]", "", text)  # inline footnote references
    text = re.sub(
        r"^> \d+ .*$\n?", "", text, flags=re.MULTILINE
    )  # blockquoted footnotes
    text = re.sub(
        r"^\d+ (Section|SD) .*$\n?", "", text, flags=re.MULTILINE
    )  # footnotes
    return text


AmlCode = DocSpecs(
    document="The AML Code 2019",
    input_path=project_root / "data/raw/custom/the_aml_code_2019.pdf",
    chunk_path=project_root / "data/processed/raw_code.jsonl",
    definition_path=project_root / "data/processed/code_defs.json",
    hierarchy="legislation",
    major_name="part",
    minor_name="paragraph",
    start_line=87,
    end_line=1859,
    definitions_start=11,
    definitions_end=346,
    re_steps=re_steps,
    is_major_header_line=lambda line: line.startswith("## **PART"),
    is_minor_header_line=lambda line: line.startswith("## **") and line[5].isdigit(),
    has_definition_section=True,
    is_definition_line=lambda line: (
        '- **"' in line or '## **"' in line or line.startswith('**"')
    ),
    is_double_def_line=lambda segs: len(segs) == 5 and segs[2].strip() in ("or", "and"),
    is_false_dub_def=lambda segs: len(segs) == 5 and segs[2].strip() != "or",
    re_pack_splitter=lambda text: re.split(r"\n(?=- \(\d+\))", text),
    strip_md=lambda line: line.replace("## **", "").replace("**", "").strip(),
    h_strip_md=lambda line: (
        line.replace("- **", "")
        .replace("##", "")
        .replace("**", "")
        .replace(" — ", "")
        .strip()
    ),
)
