import re
from config import project_root
from extraction_ops.models import (
    DefinitionTools,
    ToolBelt,
    ChunkSplitters,
    SectionMarkers,
)
from extraction_ops.specs.shared_funcs import (
    base_body_cleaner,
    base_header_cleaner,
    split_on_bracketed_letter,
    split_on_bracketed_num,
    base_def_line,
    base_double_def_line,
    base_false_double_def,
)


def clean_text(text: str) -> str:
    text = re.sub(r"\[\d+\]", "", text)  # inline footnote references
    text = re.sub(
        r"^> \d+ .*$\n?", "", text, flags=re.MULTILINE
    )  # blockquoted footnotes
    text = re.sub(
        r"^\d+ (Section|SD) .*$\n?", "", text, flags=re.MULTILINE
    )  # footnotes
    return text


AmlCodeDefMarkers = SectionMarkers(
    start=lambda line: line.startswith("- **“acceptable applicant"),
    end=lambda line: line.startswith("   - (c) the relevant person becomes aware"),
)


AmlCodeDefs = DefinitionTools(
    section_markers=[AmlCodeDefMarkers],
    definition_scope="in this act...",
    is_definition_line=base_def_line,
    is_double_def_line=base_double_def_line,
    is_false_dub_def=base_false_double_def,
)

AmlCodeTrimmer = SectionMarkers(
    start=lambda text: text.startswith("## **PART 1 - INTRODUCTORY**"),
    end=lambda text: text.startswith("a partner in the partnership"),
)

AmlCodeSplitters = ChunkSplitters(
    primary=split_on_bracketed_num,
    fallback=split_on_bracketed_letter,
)

AmlCode = ToolBelt(
    document="The AML Code 2019",
    hierarchy="secondary legislation",
    usage_notes=None,
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/SUBORDINATE/2019/2019-0202/2019-0202_2.pdf",
    pdf_path=project_root / "data/raw/custom/the_aml_code_2019.pdf",
    trimmer=AmlCodeTrimmer,
    header_matchers=[
        lambda line: line.startswith("## **PART"),
        lambda line: line.startswith("## **") and line[5].isdigit(),
    ],
    definition_tools=AmlCodeDefs,
    clean_text=clean_text,
    re_pack_splitters=AmlCodeSplitters,
    clean_body=base_body_cleaner,
    clean_header=base_header_cleaner,
)
