import re
from config import project_root
from .specs import DocSpecs


def re_steps(text: str) -> str:
    text = re.sub(
        r"^\s*-?\s*[PJ]\d{4}/\d+/\d+(?:\(\d+\)(?:\s*(?:to|and)\s*\(\d+\))*)?(?:\s+and\s+drafting)?\s*\n?",
        "",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(r"\[\d+\]", "", text)  # inline footnote references
    text = re.sub(
        r"## \*\*(\d+[A-Z]?)\*\*\s*\n\s*## \*\*([^\n*]+)\*\*",
        r"## **\1 \2**",
        text,
    )
    text = re.sub(
        r"^>?\s*\d+\s+(?:\d{4}\s+c\.\d+|OJ\s|SI\s+\d{4}/\d+).*$\n?",
        "",
        text,
        flags=re.MULTILINE,
    )
    return text


SanctionsAct = DocSpecs(
    document="Sanctions Act 2024",
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/PRINCIPAL/2024/2024-0002/2024-0002.pdf?zoom_highlight=sanctions#search=%22sanctions%22",
    hierarchy="legislation",
    input_path=project_root / "data/raw/custom/sanctions_act.pdf",
    major_name="part",
    minor_name="paragraph",
    start_line=56,
    end_line=349,
    definitions_start=18,
    definitions_end=39,
    # TODO: dangling "in this act" left from the extraction of the defs section
    re_steps=re_steps,
    header_matchers=[
        lambda line: line.startswith("## _"),
        lambda line: (
            line.startswith("## **")
            and line[5].isdigit()
            or line.startswith("- **")
            and line[4].isdigit()
        ),
    ],
    has_definition_section=True,
    is_definition_line=lambda line: '- " **' in line,
    is_double_def_line=lambda segs: len(segs) == 5 and segs[2].strip() in ("or", "and"),
    is_false_dub_def=lambda segs: len(segs) == 5 and segs[2].strip() != "or",
    re_pack_splitter=lambda text: re.split(r"\n(?=- \(\d+\))", text),
    strip_md=lambda line: (
        line.replace("##", "").replace("**", "").replace("_", "").strip()
    ),
    # TODO: when reworking strip_md to shared_funcs.py include .replace("’", "'")
    h_strip_md=lambda line: (
        line.replace("- **", "")
        .replace("##", "")
        .replace("**", "")
        .replace("_", "")
        .replace("- ", "")
        .strip()
    ),
)
