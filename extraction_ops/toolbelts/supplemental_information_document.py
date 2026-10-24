import re

from core.sectors import ALL_SECTORS
from extraction_ops.models import ChunkSplitters, ToolBelt
from extraction_ops.toolbelts.custom_flatteners import (
    flatten_supplemental_information_tables,
)

from .shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    replace_from_dict,
    split_on_new_sentence,
    split_on_paragraph,
    strip_footnote_markers,
)

REPLACEMENT_DICT = {
    "identitycard": "identity card",
    "necessaryaspart": "necessary as part",
    ",includingelectronic": ", including electronic",
}


def _clean_text(text: str) -> str:
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


_Trimmer = build_simple_markers(
    "## **1. Introductory**", "This list is not exhaustive or limited"
)

_Splitter = ChunkSplitters(primary=split_on_paragraph, fallback=split_on_new_sentence)

SupplementalInformation = ToolBelt(
    document="AML/CFT Supplemental Information Document (July 2021)",
    hierarchy="supplemental",
    sectors=fixed_sectors(ALL_SECTORS),
    input_url="https://www.iomfsa.im/media/2913/supplemental-information-document-july-2021-published-version.pdf",
    pdf_path=build_pdf_path("supplemental"),
    clean_text=_clean_text,
    trimmer=_Trimmer,
    re_pack_splitters=_Splitter,
    header_matchers=[
        lambda line: bool(re.match(r"^## \*\*\d+\.\s", line)),
        lambda line: bool(re.match(r"^## \*\*\d+\.\d", line)),
    ],
)
