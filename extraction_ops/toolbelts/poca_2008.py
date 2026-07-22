import re
from config import project_root
from .specs import DocSpecs


def re_steps(text: str) -> str:
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r" *\[(?:P\d{4}|\d{4})/[^\]]*\]", "", text)
    return text


Poca = DocSpecs(
    document="The Proceeds of Crime Act (POCA) 2008",
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/PRINCIPAL/2008/2008-0013/2008-0013.pdf?zoom_highlight=proceeds+of+crime+act#search=%22proceeds%20of%20crime%20act%22",
    hierarchy="legislation",
    input_path=project_root / "data/raw/custom/poca.pdf",
    major_name="part",
    minor_name="paragraph",
    start_line=359,
    end_line=3853,
    has_definition_section=False,
    definitions_start=None,
    definitions_end=None,
    re_steps=re_steps,
    header_matchers=[
        lambda line: line.startswith("## **PART") or line.startswith("## **SCHEDULE"),
        lambda line: line.startswith("## CHAPTER"),
        lambda line: line.startswith("## **") and line[5].isdigit(),
    ],
    is_definition_line=lambda line: (
        '- **"' in line or '## **"' in line or line.startswith('**"')
    ),
    is_double_def_line=lambda segs: len(segs) == 5 and segs[2].strip() in ("or", "and"),
    is_false_dub_def=lambda segs: len(segs) == 5 and segs[2].strip() != "or",
    re_pack_splitter=lambda text: re.split(r"\n(?=- )", text),
    strip_md=lambda line: (
        line.replace("## **", "").replace("**", "").replace("##", "").strip()
    ),
    h_strip_md=lambda line: (
        line.replace("- **", "")
        .replace("##", "")
        .replace("**", "")
        .replace(" — ", "")
        .strip()
    ),
)
