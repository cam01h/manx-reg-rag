import re
from config import project_root
from .specs import DocSpecs


def re_steps(text: str) -> str:
    text = re.sub(r" *\[(?:P\d{4}|\d{4})/[^\]]*\]", "", text)
    text = re.sub(
        r"## \*\*(\d+[A-Z]?)\*\*\s*\n\s*## \*\*([^\n*]+)\*\*",
        r"## **\1 \2**",
        text,
    )
    text = re.sub(r"\**\[\d+\]\**", "", text)
    text = re.sub(
        r"^[#\-\s]*P\d{4}/\d+/\d+(?:\(\d+\))?\s*$\n?",
        "",
        text,
        flags=re.MULTILINE,
    )
    return text


FiuAct = DocSpecs(
    document="The Financial Intellegence Unit Act 2016",
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/PRINCIPAL/2016/2016-0005/2016-0005_3.pdf?zoom_highlight=FIU+Act#search=%22FIU%20Act%22",
    hierarchy="primary legislation",
    input_path=project_root / "data/raw/custom/fiu_act.pdf",
    major_name="part",
    minor_name="paragraph",
    start_line=87,
    end_line=1114,
    has_definition_section=True,
    definitions_start=16,
    definitions_end=40,
    re_steps=re_steps,
    header_matchers=[
        lambda line: line.startswith("## **SCHEDULE"),
        lambda line: line.startswith("## **PART"),
        lambda line: (
            line.startswith("## **") and line[5].isdigit() or line.startswith("- **")
        ),
    ],
    is_definition_line=lambda line: bool('- " **' in line),
    is_double_def_line=lambda segs: len(segs) == 5 and segs[2].strip() in ("or", "and"),
    is_false_dub_def=lambda segs: len(segs) == 5 and segs[2].strip() != "or",
    re_pack_splitter=lambda text: re.split(
        r"\n(?=- \(\d+\)|\d+[A-Z]?\.\s*\(\d+\)|\(\d+\)\s|\d+[A-Z]?\.\s)", text
    ),
    strip_md=lambda line: (
        line.replace("## **", "")
        .replace("**", "")
        .replace("##", "")
        .replace("_", "")
        .replace("\n\n", "\n")
        .strip()
    ),
    h_strip_md=lambda line: (
        line.replace("- **", "")
        .replace("##", "")
        .replace("**", "")
        .replace("_", "")
        .replace("- ", "")
        .strip()
    ),
)
