import re
from config import PROJECT_ROOT
import logging
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
    base_double_def_line,
    base_false_double_def,
    base_header_cleaner,
    base_text_cleaner,
    in_line,
    redact_md_tables,
    replace_from_dict,
    split_on_new_sentence,
    starts_with,
    strip_patterns,
)

logger = logging.getLogger(__name__)

REPLACEMENTS = {
    # reshaping definition lines in 3.2
    '_Customer due diligence ("CDD")_': '\n- "Customer due diligence" or "CDD" ',
    '_Identification and Verification ("ID&V")_': '- "Identification and Verification" or "ID&V"',
    "_Reasonable measures_": '- "Reasonable measures"',
    '_Enhanced customer due diligence ("ECDD")_': '- "Enhanced customer due diligence" or "ECDD"',
    "_Ongoing monitoring_": '- "Ongoing monitoring"',
    "_Enhanced Ongoing Monitoring_": '- "Enhanced Ongoing Monitoring"',
    # ungluing headers from bodies
    "provided** The FATF": "provided**\n\nThe FATF",
    "signatories/directors** Considerations": "signatories/directors**\n\nConsiderations",
    "party's account** Where funds": "party's account**\n\nWhere funds",
    "source of funds** However a": "source of funds**\n\nHowever a",
    '("PEPs") risk** Much international': '("PEPs") risk**\n\nMuch international',
    "introducer concession** Conditions for": "introducer concession**\n\nConditions for",
    "introducer procedures** Ensuring appropriate": "introducer procedures**\n\nEnsuring appropriate",
    "miscellaneous concessions** As with all": "miscellaneous concessions**\n\nAs with all",
    "other related parties** Relevant persons": "other related parties**\n\nRelevant persons",
    "and address** In order to": "and address**\n\nIn order to",
    "and Arrangements_ Additional requirements": "and Arrangements_\n\nAdditional requirements",
    "CDD requirements_ Certain CDD": "CDD requirements_\n\nCertain CDD",
}


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
    text = redact_md_tables(text)
    text = strip_patterns(text, ["\n<br>", "<br>"])
    text = replace_from_dict(text, REPLACEMENTS)
    return text


HandbookRiskDefMarker221 = SectionMarkers(
    start=in_line(['"Risk" means:']),
    end=in_line(['"Mitigation" means implementing controls']),
)

HandbookRiskDefMarker32 = SectionMarkers(
    start=in_line(['- "Customer due diligence"']),
    end=in_line(["Enhanced ongoing monitoring falls"]),
)

HandbookRiskDefMarker431 = SectionMarkers(
    start=in_line(['- "receiving regulated person" -']),
    end=in_line(['- "underlying client" - the allowed']),
)

HandbookDefs = DefinitionTools(
    section_markers=[
        HandbookRiskDefMarker221,
        HandbookRiskDefMarker32,
        HandbookRiskDefMarker431,
    ],
    is_definition_line=starts_with(['"', '## - "', '- "']),
    is_double_def_line=base_double_def_line,
    is_false_dub_def=base_false_double_def,
)

HandbookTrimmer = SectionMarkers(
    start=lambda text: text.startswith("## **1. Introductory*"),
    end=lambda text: text.startswith("Guidance on fictitious, anonymous and"),
)

HandbookSplitters = ChunkSplitters(
    primary=lambda text: text.split("\n\n"),
    fallback=split_on_new_sentence,
)

AmlHandbook = ToolBelt(
    document="The AML Handbook (April 2026)",
    hierarchy="guidance",
    input_url="https://www.iomfsa.im/media/3590/handbook-april-2026-clean.pdf",
    pdf_path=PROJECT_ROOT / "data/raw/custom/aml_handbook_april_2026.pdf",
    use_ocr=False,
    pdf_handlers=[
        handbook_remove_cover_and_dividers,
        handbook_redact_margin_citations,
        handbook_redact_legislation_quoted,
    ],
    definition_tools=HandbookDefs,
    clean_text=re_steps,
    trimmer=HandbookTrimmer,
    re_pack_splitters=HandbookSplitters,
    header_matchers=[
        lambda line: bool(re.match(r"^## \*\*\d+\.\s", line)),
        lambda line: bool(re.match(r"^(?:## |- )\*\*\d+\.\d+\s", line)),
        lambda line: bool(re.match(r"^(?:## )?(?:\*\*|_)\d+(?:\.\d+){2,4}\s", line)),
        starts_with(["## _", "_"]),
    ],
    clean_header=base_header_cleaner,
    clean_body=base_body_cleaner,
    min_body_len=40,
)
