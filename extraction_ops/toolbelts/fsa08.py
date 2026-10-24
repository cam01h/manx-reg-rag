import re

from core.sectors import FSA08_SECTORS
from extraction_ops.models import (
    ChunkSplitters,
    DefinitionTools,
    ToolBelt,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    rejoin_page_breaks,
    replace_from_dict,
    replace_section,
    split_on_bracketed_letter,
    split_on_bracketed_num,
    starts_with,
    strip_footnote_markers,
)

# TODO: add a note to all flattened tables letting the agent know its been flattened,
# then redact from embedding text
_DECISIONS_TABLE_FLATTENED = """
The issue of a licence subject to conditions — Section 7(1)(b)
The refusal to issue a licence — Section 7(1)(c)
The imposition of conditions, or further conditions upon a licence — Section 8(1)(a)
The variation or revocation of, or refusal to vary any condition attached to a licence — Section 8(1)(b)
The suspension of a licence — Section 9(1)
The revocation of a licence — Section 9(1)
The issue or variation of, or refusal to vary or revoke a direction — Section 10
The imposition of a prohibition — Section 10A
The variation or refusal to vary a prohibition — Section 10C
The refusal to revoke a prohibition — Section 10C
The giving of a warning notice, or the terms of such a notice — Section 11
The issue or variation of, or refusal to vary or revoke, a direction — Section 14
The imposition of a penalty — Section 16
The withdrawal of an exemption — Regulations under section 44(3)(b)
The issue of a direction — Paragraph 2 of Schedule 2
"""

_REPLACEMENT_DICT = {
    # correcting line splits
    '" **permitted** " \n\n   - **persons .**': '" permitted persons ".',
    # definition minipulation
    "- (2) In this Act a person is resident": '- "resident"\nIn this Act a person is resident',
    "- (5) In determining for any purposes of": '- "public interest"\nIn determining for any purposes of',
    "- (7) A qualifying capital interest means": '- (7) A "qualifying capital interest" means',
    "- (8) Relevant shares means shares comprised": '- (8) "Relevant shares" means shares comprised',
    "- (9) A holding of 20 per cent or more": '- "qualifying capital interest"\nA holding of 20 per cent or more',
    "has the meaning given by section 7(7)": "\nIn this Act, a person who has been issued with a licence under this section is referred to as a licenceholder.",
    "has the meaning given by section 35(1);": "former and current licenceholders and classes of persons who are exempt from any provision of this Act under section 44(2) are referred to collectively as permitted persons.",
    "has the meaning given in section 2(2);": "- (a) securing an appropriate degree of protection for policyholders, members of retirement benefits schemes and the customers of persons carrying on a regulated activity; \n\n- (b) the reduction of financial crime; and \n\n\n  - (c) the maintenance of confidence in the Island's financial services, insurance and pensions industries through effective regulation, thereby supporting the Island's economy and its development as an international financial centre.",
    '- (3) In this Act " **action for': '- " **action for',
    '- (6) In this Act a " **related company': '- " **related company',
    '- (7) A "qualifying capital': '- "qualifying capital',
    '- (8) "Relevant shares" means': '- "Relevant shares" means',
    '- (10) In subsection (8), "equity share capital"': '- "equity share capital"',
}
# NOTE: "Qualifying Capital Interest" is actually defined twice in the act.
# Including bothe definitions mean both definitions will be called by the tool


def _join_schedule_subtitles(text: str) -> str:
    return re.sub(
        r"^## \*\*(SCHEDULE \d+[A-Z]?)\*\* *\n\s*\n## (?:\*\*|_)(?!SCHEDULE \d)(.+?)(?:\*\*|_) *$",
        r"## **\1 - \2**",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )


def _remove_enactment_citations(text: str) -> str:
    return re.sub(
        r"^(?:## )?\[?Sections? \d+[A-Z]*(?:\(\d+[A-Za-z]*\))*"
        r"(?: *(?:&|and|,) *(?:\d+[A-Z]*)?(?:\(\d+[A-Za-z]*\))*)*\]? *$\n?",
        "",
        text,
        flags=re.MULTILINE,
    )


def _clean_text(text: str) -> str:
    text = base_text_cleaner(text)
    # must replace must go above strip footnotes otherwise section [50] is caught
    text = text.replace("section [50] and Schedule 7", "section 50 and Schedule 7")
    text = strip_footnote_markers(text)
    # Schedule 6 and 7 removed as they are ammendments and enactments
    text = replace_section(text, "## **SCHEDULE 6", "## **SCHEDULE 8")
    text = _remove_enactment_citations(text)
    text = _join_schedule_subtitles(text)
    text = rejoin_page_breaks(text)
    text = replace_section(
        text,
        "|Decision|Provision|",
        "\n- (4) On the determination",
        _DECISIONS_TABLE_FLATTENED,
    )
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    return text


_Fsa08p48DefMarkers = build_simple_markers(
    '- " **advertisement** " includes every form of advertising',
    '- "equity share capital"',
)  # this line is edited in the dict on line 61


_Fsa08S02DefMarkers = build_simple_markers(
    '   - " **functions** " means functions conferred', "within the meaning of the"
)

_Fsa08Defs = DefinitionTools(
    section_markers=[_Fsa08p48DefMarkers, _Fsa08S02DefMarkers],
    is_definition_line=starts_with(['- " **', '- "', '   - " **']),
)

_Fsa08Trimmer = build_simple_markers(
    "## **PART 1 - THE REGULATOR AND",
    "(3) This paragraph is without prejudice to the generality",
)

_Fsa08Splitters = ChunkSplitters(
    primary=split_on_bracketed_num,
    fallback=split_on_bracketed_letter,
)

Fsa08 = ToolBelt(
    document="Financial Services Act 2008",
    hierarchy="primary legislation",
    sectors=fixed_sectors(FSA08_SECTORS),
    input_url="https://www.iomfsa.im/media/2376/financialservicesact2008.pdf",
    pdf_path=build_pdf_path("fsa"),
    trimmer=_Fsa08Trimmer,
    header_matchers=[
        starts_with(["## **PART", "## **Schedule", "## **SCHEDULE"]),
        starts_with(["## CHAPTER"]),
        starts_with(["## _"]),
        lambda line: line.startswith("## **") and line[5].isdigit(),
    ],
    definition_tools=_Fsa08Defs,
    clean_text=_clean_text,
    re_pack_splitters=_Fsa08Splitters,
)
