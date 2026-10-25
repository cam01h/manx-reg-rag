from core.sectors import LICENCE_CLASSES
from extraction_ops.models import (
    ChunkSplitters,
    ToolBelt,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    replace_from_dict,
    split_on_numbered_dot,
    split_on_paragraph,
    starts_with,
)

_REPLACEMENT_DICT = {
    "## **APPENDIX 1** \n\n## **Suggested contents": "## **APPENDIX 1 - Suggested contents",
    "## **APPENDIX 2** \n\n## **Illustration - client": "## **APPENDIX 2 - Illustration - client",
    "## 1. Background": "1. Background",
    "## 3. Application": "3. Application",
    "client\n\ncompany": "client company",
}


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    return text


_Trimmer = build_simple_markers(
    "## **Introduction", "8. If necessary, withdrawing from one"
)

_Splitters = ChunkSplitters(primary=split_on_numbered_dot, fallback=split_on_paragraph)

Conflicts = ToolBelt(
    document="Conflicts of Interest Policy - Guidance Note - Rule 8.9",
    hierarchy="guidance",
    sectors=fixed_sectors(LICENCE_CLASSES),
    input_url="https://www.iomfsa.im/media/1720/rule87conflictsofinterestjuly.pdf",
    pdf_path=build_pdf_path("conflicts"),
    trimmer=_Trimmer,
    header_matchers=[
        starts_with(["## **", "## **APPENDIX"]),
        lambda line: line.startswith("##") and line[3].isdigit(),
    ],
    definition_tools=None,
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
