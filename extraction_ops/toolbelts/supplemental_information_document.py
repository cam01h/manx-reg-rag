import re
from config import PROJECT_ROOT
from extraction_ops.models import ChunkSplitters, SectionMarkers, ToolBelt
from extraction_ops.toolbelts.custom_flatteners import (
    flatten_supplemental_information_tables,
)
from .shared_funcs import (
    base_body_cleaner,
    base_header_cleaner,
    base_text_cleaner,
    replace_from_dict,
    split_on_new_sentence,
    split_on_paragraph,
    starts_with,
    strip_footnote_markers,
)

REPLACEMENT_DICT = {
    "identitycard": "identity card",
    "necessaryaspart": "necessary as part",
    ",includingelectronic": ", including electronic",
}


def re_steps(text: str) -> str:
    text = base_text_cleaner(text)
    text = flatten_supplemental_information_tables(text)
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
    # fix header 3
    text = text.replace(
        "monitoring and enhanced** \n\n## **measures**",
        "monitoring and enhanced measures**",
    )
    text = strip_footnote_markers(text)
    text = replace_from_dict(text, REPLACEMENT_DICT)
    return text


SupplementalTrimmer = SectionMarkers(
    start=starts_with(["## **1. Introductory**"]),
    end=starts_with(["This list is not exhaustive or limited"]),
)

SupplementalSplitter = ChunkSplitters(
    primary=split_on_paragraph, fallback=split_on_new_sentence
)

SupplementalInformation = ToolBelt(
    document="AML/CFT Supplemental Information Document (July 2021)",
    hierarchy="supplemental",
    input_url="https://www.iomfsa.im/media/2913/supplemental-information-document-july-2021-published-version.pdf",
    pdf_path=PROJECT_ROOT
    / "data/raw/custom/aml_cft_supplemental_information_document.pdf",
    use_ocr=True,
    pdf_handlers=None,
    definition_tools=None,
    clean_text=re_steps,
    trimmer=SupplementalTrimmer,
    re_pack_splitters=SupplementalSplitter,
    header_matchers=[
        lambda line: bool(re.match(r"^## \*\*\d+\.\s", line)),
        lambda line: bool(re.match(r"^## \*\*\d+\.\d", line)),
    ],
    clean_header=base_header_cleaner,
    clean_body=base_body_cleaner,
    min_body_len=40,
)
