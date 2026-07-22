import re
from config import project_root
from .specs import DocSpecs


def re_steps(text: str) -> str:
    text = re.sub(r"\[[^\]]*\]", "", text)
    text = re.sub(
        r"In this Act the expressions listed below are defined by the provisions specified\..*?(?=\n## )",
        "",
        text,
        flags=re.DOTALL,
    )
    # TODO: flatten table for designated ports
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
    has_definition_section=True,
    definitions_start=3474,
    definitions_end=3587,
    re_steps=re_steps,
    header_matchers=[
        lambda line: line.startswith("## **PART") or line.startswith("## **SCHEDULE"),
        lambda line: bool(re.match(r"^##\s+_[^_]+_", line)),
        lambda line: (
            line.startswith("## **") and line[5].isdigit() or line.startswith("- **")
        ),
    ],
    # ## _Charging orders_ _****_
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
        .replace(" — ", "")
        .replace("_", "")
        .replace("- ", "")
        .strip()
    ),
)
