import re

from core.sectors import INSURANCE_MANAGER, INSURERS, NON_LIFE_CO
from extraction_ops.models import ChunkSplitters, DefinitionTools, ToolBelt
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    rejoin_page_breaks,
    replace_from_dict,
    replace_section,
    split_on_bracketed_letter,
    split_on_bracketed_num,
    starts_with,
    strip_footnote_markers,
)

# the class table in regulation 3(3), rewritten by hand: one line per class
_CLASS_TABLE_FLAT = """[Editors note: the below is a flattened table]

- Class 1 (long-term business): Linked long-term
- Class 2 (long-term business): Long-term but excluding contracts within class 1
- Class 3 (general business): Marine, aviation and transport
- Class 4 (general business): Property, but excluding contracts within classes 3 or 5
- Class 5 (general business): Motor
- Class 6 (general business): Pecuniary loss
- Class 7 (general business): Liability, other than contracts within classes 3 or 5
- Class 8 (general business): Credit and suretyship
- Class 9 (general business): Personal miscellaneous, including accident, health and disability
- Class 10 (reinsurance): Reinsurance of contracts within classes 1 and 2
- Class 11 (reinsurance): Reinsurance of contracts within classes 3 to 9
- Class 12 (captive): Contracts within classes 1 to 11 which comply with the requirements set out in Schedule 1
- Class 13 (insurance special purpose vehicle): This class is supplemental to any of classes 1 to 12 and means that the insurer is subject to the requirements of Schedule 2 (class 13 in itself does not enable an insurer to carry on any insurance business)

"""

_REPLACEMENT_DICT = {
    "## **MADE** \n\n": "",
    ". These Regulations come into operation on 30 June 2025[1]": "These Regulations come into operation on 30 June 2025.",
    # list in regulation 25 run together
    "(a) the Insurance Regulations 2021[9] \n\n- (b) the Insurance (Special Purpose Vehicles) Regulations 2015[10] ; and (c) the Insurance (Miscellaneous Amendments) Regulations 2015[11] .": "- (a) the Insurance Regulations 2021;\n\n- (b) the Insurance (Special Purpose Vehicles) Regulations 2015; and\n\n- (c) the Insurance (Miscellaneous Amendments) Regulations 2015.",
    # definitions without a bullet
    '\n**"the Act"** means': '\n- **"the Act"** means',
    '\n**"sandbox"** has': '\n- **"sandbox"** has',
    '\n**"approved bank"** means': '\n- **"approved bank"** means',
    '\n**"balance sheet"** also': '\n- **"balance sheet"** also',
    '\n**"authorised"** , includes': '\n- **"authorised"** , includes',
    # bold that caught a closing quote or semicolon
    'exposure **"** and': 'exposure" and',
    'partnership" **;**': 'partnership";',
}

# page footnotes are plain lines here ("2 SD 2021/0276"), some quoted ("> 7 Insurance ...")
_FOOTNOTE_LINE = re.compile(
    r"^>? *\d{1,2} (?:SD|O\.J\.|G\.C\.|Under section 50\(4\)|Insurance Regulations 2018)\b.*$\n?",
    re.MULTILINE,
)
# "## **SCHEDULE 1** / [Regulations 3(3) and 4(2)] / ## **CLASS 12: CAPTIVE INSURERS**"
_SCHEDULE_TITLE = re.compile(
    r"^## \*\*(SCHEDULE \d+)\*\* *\n\s*\n(\[[^\]\n]*\] *\n\s*\n)?## \*\*(.+?)\*\* *$",
    re.MULTILINE,
)
# "## **2** / ## **Requirement to be subject to a sandbox**"
_NUMBER_ONLY_HEADING = re.compile(r"^## \*\*(\d+)\*\* *\n\s*\n## \*\*", re.MULTILINE)


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    text = _FOOTNOTE_LINE.sub("", text)
    text = strip_footnote_markers(text)
    text = _SCHEDULE_TITLE.sub(r"## **\1 - \3**\n\n\2", text)
    text = _NUMBER_ONLY_HEADING.sub(r"## **\1 ", text)
    text = replace_section(
        text,
        "**Category Class number Description**",
        "- (4) In paragraph (3)",
        _CLASS_TABLE_FLAT,
    )
    # paragraphs that run over a page break, with a footnote in between
    text = rejoin_page_breaks(text)
    return text


_Trimmer = build_simple_markers("## **1 Title", "- (h) its registration number.")

# regulation 3(1) and the interpretation paragraphs of Schedules 1, 2, 5, 6 and 7
_DefMarkers = [
    build_simple_markers('- **"the Act"** means', '- **"written",**'),
    build_simple_markers(
        '- " **beneficial ownership**', '- **"reinsurance"** includes'
    ),
    build_simple_markers('- **"approved bank"**', '- **"tier"**'),
    build_simple_markers(
        '- **"cell"** , in relation to a PCC', '- **"supporting core"**'
    ),
    build_simple_markers(
        '- **"authorised"** , includes', '- **"provisional authorisation"**'
    ),
    build_simple_markers('- **"general partner"**', '- **"partner"** has the meaning'),
]

_DefTools = DefinitionTools(
    section_markers=_DefMarkers,
    is_definition_line=starts_with(['- **"', '- a **"', '- an **"', '- " **']),
)

_Splitters = ChunkSplitters(
    primary=split_on_bracketed_num, fallback=split_on_bracketed_letter
)


def _is_section(line: str) -> bool:
    # "## **4 Application of these Regulations" / "## **1 Interpretation" in a schedule
    return line.startswith("## **") and line[5:6].isdigit()


# the most specific heading wins: a schedule paragraph takes its schedule's sectors
_SECTOR_MATCHERS = {
    "23 Cancellation of registration of insurance manager": (INSURANCE_MANAGER,),
    "PART 3 (REGISTER OF INSURANCE MANAGERS)": (INSURANCE_MANAGER,),
    # captives and ISPVs sit with non-life (see core/sectors.py)
    "CLASS 12: CAPTIVE INSURERS": (NON_LIFE_CO,),
    "CLASS 13: INSURANCE SPECIAL PURPOSE VEHICLES": (NON_LIFE_CO,),
    "FAST-TRACK AUTHORISATION": INSURERS,
    "REGULATORY SANDBOXING": INSURERS,
    "PROTECTED CELL COMPANIES": INSURERS,
    "INCORPORATED CELL COMPANIES": INSURERS,
    "LIMITED PARTNERSHIPS": INSURERS,
}


def _sectors(headers: tuple[str, ...]) -> tuple[str, ...]:
    for header in reversed(headers):
        for pattern, sectors in _SECTOR_MATCHERS.items():
            if pattern in header:
                return sectors
    # authorised insurers, permit holders and registered insurance managers (regulation 4)
    return INSURERS + (INSURANCE_MANAGER,)


InsuranceRegs = ToolBelt(
    document="Insurance Regulations 2025",
    hierarchy="secondary legislation",
    sectors=_sectors,
    input_url="https://www.iomfsa.im/media/3478/insurance-regulations-2025.pdf",
    pdf_path=build_pdf_path("insurance_regs"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[
        starts_with(["## **SCHEDULE"]),
        _is_section,
        starts_with(["## **PART", "## **« PART"]),
    ],
    definition_tools=_DefTools,
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
