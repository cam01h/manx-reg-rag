import re

from core.sectors import ALL_SECTORS
from extraction_ops.models import (
    DefinitionTools,
    ToolBelt,
)
from extraction_ops.toolbelts.defaults import DefaultSplitter
from extraction_ops.toolbelts.shared_funcs import (
    base_def_line,
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    starts_with,
)


def _clean_text(text: str) -> str:
    text = base_text_cleaner(text)
    text = re.sub(r"\[\d+\]", "", text)  # inline footnote references
    text = re.sub(
        r"^> \d+ .*$\n?", "", text, flags=re.MULTILINE
    )  # blockquoted footnotes
    text = re.sub(
        r"^\d+ (Section|SD) .*$\n?", "", text, flags=re.MULTILINE
    )  # footnotes
    return text


_AmlCodeDefMarkers = build_simple_markers(
    '- **"acceptable applicant', "   - (c) the relevant person becomes aware"
)


_AmlCodeDefs = DefinitionTools(
    section_markers=[_AmlCodeDefMarkers],
    is_definition_line=base_def_line,
)

_Trimmer = build_simple_markers(
    "## **PART 1 - INTRODUCTORY**", "a partner in the partnership"
)


AmlCode = ToolBelt(
    document="The AML/CFT Code 2019",
    hierarchy="secondary legislation",
    sectors=fixed_sectors(ALL_SECTORS),
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/SUBORDINATE/2019/2019-0202/2019-0202_2.pdf",
    pdf_path=build_pdf_path("code"),
    trimmer=_Trimmer,
    header_matchers=[
        starts_with(["## **PART"]),
        lambda line: line.startswith("## **") and line[5].isdigit(),
    ],
    definition_tools=_AmlCodeDefs,
    clean_text=_clean_text,
    re_pack_splitters=DefaultSplitter,
)
