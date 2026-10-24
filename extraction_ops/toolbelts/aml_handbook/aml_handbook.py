import logging
import re

from core.sectors import ALL_SECTORS
from extraction_ops.models import (
    ChunkSplitters,
    DefinitionTools,
    SectionMarkers,
    ToolBelt,
)
from extraction_ops.toolbelts.aml_handbook.pdf_handler import (
    handbook_redact_legislation_quoted,
    handbook_redact_margin_citations,
    handbook_remove_cover_and_dividers,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    fixed_sectors,
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
    '## _3.2.1.1 Customer due diligence ("CDD")_': '\n- "Customer due diligence" or "CDD" ',
    '## _3.2.1.2 Identification and Verification ("ID&V")_ ': '- "Identification and Verification" or "ID&V"',
    "## _3.2.1.3 Reasonable measures_ ": '- "Reasonable measures"',
    '## _3.2.1.4 Enhanced customer due diligence ("ECDD")_ ': '- "Enhanced customer due diligence" or "ECDD"',
    "## _3.2.1.5 Ongoing monitoring_ ": '- "Ongoing monitoring"',
    "## _3.2.1.6 Enhanced Ongoing Monitoring_ ": '- "Enhanced Ongoing Monitoring"',
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
    "monitoring and enhanced** \n\n## **measures**": "monitoring and enhanced measures**",
    "enhanced measures** The purpose of CDD": "enhanced measures**\n\nThe purpose of CDD",
    "methodology** Risk assessments": "methodology**\n\nRisk assessments",
    "and/or wealth** When researching": "and/or wealth**\n\nWhen researching",
    "the concession** If the conditions": "the concession**\n\nIf the conditions",
    # removing heading markers from bullets
    "## a. Understanding Source": "- a. Understanding Source",
    "## c. Independent Verification": "- c. Independent Verification",
    "## d. Face to Face": "- d. Face to Face",
    "## e. Ongoing Monitoring": "- e. Ongoing Monitoring",
    "## 2. assessing those": "      2. assessing those",
}


def _clean_text(text: str) -> str:
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


_HandbookRiskDefMarker221 = SectionMarkers(
    start=in_line(['"Risk" means:']),
    end=in_line(['"Mitigation" means implementing controls']),
)

_HandbookRiskDefMarker32 = SectionMarkers(
    start=in_line(['- "Customer due diligence"']),
    end=in_line(["Guidance on enhanced ongoing monitoring is at section 3.4.7"]),
)

_HandbookRiskDefMarker431 = SectionMarkers(
    start=in_line(['- "receiving regulated person" -']),
    end=in_line(['- "underlying client" - the allowed']),
)

_DefTools = DefinitionTools(
    section_markers=[
        _HandbookRiskDefMarker221,
        _HandbookRiskDefMarker32,
        _HandbookRiskDefMarker431,
    ],
    is_definition_line=starts_with(['"', '## - "', '- "']),
)

_Trimmer = SectionMarkers(
    start=lambda text: text.startswith("## **1. Introductory*"),
    end=lambda text: text.startswith("Guidance on fictitious, anonymous and"),
)

_Splitters = ChunkSplitters(
    primary=lambda text: text.split("\n\n"),
    fallback=split_on_new_sentence,
)

AmlHandbook = ToolBelt(
    document="The AML Handbook (August 2026)",
    hierarchy="guidance",
    sectors=fixed_sectors(ALL_SECTORS),
    input_url="https://www.iomfsa.im/media/3650/handbook-august-2026-clean.pdf",
    pdf_path=build_pdf_path("handbook"),
    use_ocr=False,
    pdf_handlers=[
        handbook_remove_cover_and_dividers,
        handbook_redact_margin_citations,
        handbook_redact_legislation_quoted,
    ],
    definition_tools=_DefTools,
    clean_text=_clean_text,
    trimmer=_Trimmer,
    re_pack_splitters=_Splitters,
    header_matchers=[
        lambda line: bool(re.match(r"^## \*\*\d+\.\s", line)),
        lambda line: bool(re.match(r"^(?:## |- )?\*\*\d+\.\d+\s", line)),
        lambda line: bool(re.match(r"^(?:## |- )?(?:\*\*|_)\d+(?:\.\d+){2}\s", line)),
        lambda line: bool(re.match(r"^(?:## |- )?(?:\*\*|_)\d+(?:\.\d+){3,}\s", line)),
        starts_with(["## _", "_"]),
    ],
)
