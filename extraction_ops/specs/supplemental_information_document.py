import re
from config import project_root
from .specs import DocSpecs
from .shared_funcs import flatten_tables


def re_steps(text: str) -> str:
    text = flatten_tables(text)
    # cleans pictures
    text = re.sub(r"\*\*==>.*?<==\*\*\n?", "", text)
    text = re.sub(
        r"\*\*-+ Start of picture text -+\*\*.*?\*\*-+ End of picture text -+\*\*(?:<br>)?\n?",
        "",
        text,
        flags=re.DOTALL,
    )
    # cleans scenario titles
    text = re.sub(
        r"^## \*\*Scenario \d.*?(?=^## \*\*\d)",
        "",
        text,
        flags=re.DOTALL | re.MULTILINE,
    )
    # remove placeholder chapters
    text = text.replace(
        "There is no supplemental information associated with this chapter of the Handbook.",
        "",
    )
    text = text.replace(
        "monitoring and enhanced** \n\n## **measures**",
        "monitoring and enhanced measures**",
    )
    return text


SupplementalInformation = DocSpecs(
    document="AML/CFT Supplemental Information Document (July 2021)",
    input_url="https://www.iomfsa.im/media/2913/supplemental-information-document-july-2021-published-version.pdf",
    hierarchy="supplemental",
    input_path=project_root
    / "data/raw/custom/aml_cft_supplemental_information_document.pdf",
    major_name="chapter",
    minor_name="section",
    start_line=41,
    end_line=479,
    definitions_start=None,
    definitions_end=None,
    re_steps=re_steps,
    header_matchers=[
        lambda line: bool(re.match(r"^## \*\*\d+\.\s", line)),
        lambda line: bool(re.match(r"^## \*\*\d+\.\d", line)),
    ],
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
