import re
from config import project_root
from extraction_ops.models import (
    ChunkSplitters,
    DefinitionTools,
    SectionMarkers,
    ToolBelt,
)
from extraction_ops.toolbelts.aml_handbook.pdf_handler import (
    handbook_redact_margin_citations,
    handbook_redact_legislation_quoted,
    handbook_remove_cover_and_dividers,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_body_cleaner,
    base_def_line,
    base_double_def_line,
    base_false_double_def,
    base_header_cleaner,
    base_text_cleaner,
    split_on_new_sentence,
    starts_with,
    strip_patterns,
)


def re_steps(text: str) -> str:
    text = base_text_cleaner(text)
    # strips chapter level contents tables
    text = re.sub(
        r"(?:^\|.*\|\n?)+",
        lambda m: "" if re.search(r"\.{5,}\s*\d+", m.group()) else m.group(),
        text,
        flags=re.MULTILINE,
    )
    # TODO: tables and visuals should be extracted to .png with fitz, path included in  chunk metadata
    text = re.sub(
        r"\*\*==> picture.*?intentionally omitted <==\*\*", "", text, flags=re.DOTALL
    )
    text = re.sub(
        r"\*\*----- Start of picture text.*?End of picture text -----\*\*",
        "",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"(?:^\|.*\|[ \t]*\n?)+",
        "[table redacted from original document]\n",
        text,
        flags=re.MULTILINE,
    )
    text = strip_patterns(text, ["\n<br>", "<br>"])
    return text


HandbookRiskDefMarker = SectionMarkers(
    start=lambda text: text.startswith('"Risk" means'),
    end=lambda text: text.startswith('"Mitigation" means implementing controls'),
)

HandbookDefs = DefinitionTools(
    section_markers=[HandbookRiskDefMarker],
    is_definition_line=base_def_line,
    is_double_def_line=base_double_def_line,
    is_false_dub_def=base_false_double_def,
)

HandbookTrimmer = SectionMarkers(
    start=lambda text: text.startswith("## **1. Introductory*"),
    end=lambda text: text.startswith("- Guidance on fictitious, anonymous"),
)

HandbookSplitters = ChunkSplitters(
    primary=lambda text: text.split("\n\n"),
    fallback=split_on_new_sentence,
)

AmlHandbook = ToolBelt(
    document="The AML Handbook (April 2026)",
    hierarchy="guidance",
    input_url="https://www.iomfsa.im/media/3590/handbook-april-2026-clean.pdf",
    pdf_path=project_root / "data/raw/custom/aml_handbook_april_2026.pdf",
    use_ocr=False,
    pdf_handlers=[
        handbook_remove_cover_and_dividers,
        handbook_redact_margin_citations,
        handbook_redact_legislation_quoted,
    ],
    definition_tools=None,
    clean_text=re_steps,
    trimmer=HandbookTrimmer,
    re_pack_splitters=HandbookSplitters,
    header_matchers=[
        lambda line: bool(re.match(r"^## \*\*\d+\.\s", line)),
        lambda line: bool(re.match(r"^## \*\*\d+\.\d+\s", line)),
        lambda line: bool(re.match(r"^(?:## )?(?:\*\*|_)\d+(?:\.\d+){2,4}\s", line)),
        lambda line: starts_with(line, ["## _", "_"]),
    ],
    clean_header=base_header_cleaner,
    clean_body=base_body_cleaner,
    min_body_len=40,
)
