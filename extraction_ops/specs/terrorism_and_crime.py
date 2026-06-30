import re
from config import project_root
from .specs import DocSpecs


def re_steps(text: str) -> str:
    text = re.sub(r"\[[^\]]*\]", "", text)
    return text


TerrorismAndCrime = DocSpecs(
    document="The Terrorism and Crime act 2008",
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/PRINCIPAL/2003/2003-0006/2003-0006_11.pdf?zoom_highlight=terrorism#search=%22terrorism%22",
    hierarchy="legislation",
    input_path=project_root / "data/raw/custom/terrorism_and_crime.pdf",
    major_name="part",
    minor_name="paragraph",
    start_line=296,
    end_line=7658,
    has_definition_section=False,
    definitions_start=None,
    definitions_end=None,
    re_steps=re_steps,
    header_matchers=[
        lambda line: line.startswith("## **PART") or line.startswith("## **SCHEDULE"),
        lambda line: bool(re.match(r"^##\s+_[^_]+_\s*$", line)),
        lambda line: line.startswith("## **") and line[5].isdigit(),
    ],
    is_definition_line=lambda line: (
        '- **"' in line or '## **"' in line or line.startswith('**"')
    ),
    is_double_def_line=lambda segs: len(segs) == 5 and segs[2].strip() in ("or", "and"),
    is_false_dub_def=lambda segs: len(segs) == 5 and segs[2].strip() != "or",
    re_pack_splitter=lambda text: re.split(r"\n(?=- )", text),
    strip_md=lambda line: (
        line.replace("## **", "")
        .replace("**", "")
        .replace("##", "")
        .replace("_", "")
        .strip()
    ),
    h_strip_md=lambda line: (
        line.replace("- **", "")
        .replace("##", "")
        .replace("**", "")
        .replace(" — ", "")
        .replace("_", "")
        .strip()
    ),
)
