import re
from config import project_root
from specs import DocSpecs


def re_steps(text: str) -> str:
    text = re.sub(r"^\|.*\|$\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[#]*\s*Code\s*[\d\(\),\.\s\-|]*$\n?", "", text, flags=re.MULTILINE)
    text = re.sub(
        r"^(#{0,2}\s*[\s\-#>*]*?)Code\s+.*?(?=\s\(\d|\s[A-Z])",
        r"\1",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(r"^\s*[-]?>\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r" {2,}", " ", text)
    text = text.replace("*", "").replace("#", "").replace("_", "")
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = re.sub(
        r"\n\n(\s*(?:\([a-z]{1,2}\)|\(\d{1,2}\)|\([ivxlcdm]+\)))",
        r"\n\1",
        text,
        flags=re.IGNORECASE,
    )
    # TODO: there are AML Code bloc quotes in the handbook which is a duplication of embeddings.
    return text


AmlHandbook = DocSpecs(
    document="The AML Handbook (April 2026)",
    input_path=project_root / "data/raw/custom/aml_handbook_april_2026.pdf",
    hierarchy="guidanace",
    major_name="chapter",
    minor_name="section",
    start_line=317,  # TODO: chapter 1 not included
    end_line=5933,
    definitions_start=None,
    definitions_end=None,
    re_steps=re_steps,
    is_major_header_line=lambda line: bool(re.match(r"^\s*Chapter\s*\d", line.strip())),
    is_minor_header_line=lambda line: bool(
        re.match(r"^\s*\d+(?:\.\d+){1,5}\s", line.strip())
    ),
    has_definition_section=False,
    is_definition_line=None,
    is_double_def_line=None,
    is_false_dub_def=None,
    re_pack_splitter=lambda text: text.split("\n\n"),
    strip_md=lambda line: line.replace("*", "").replace("#", "").strip(),
    h_strip_md=lambda line: (
        line.replace("- **", "")
        .replace("#", "")
        .replace("*", "")
        .replace(" — ", "")
        .strip()
    ),
)
