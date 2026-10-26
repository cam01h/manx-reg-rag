from core.sectors import IA08_FIRMS
from extraction_ops.models import ChunkSplitters, DefinitionTools, ToolBelt
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    replace_from_dict,
    replace_section,
    split_on_bracketed_num,
    split_on_paragraph_or_list_item,
    starts_with,
    strip_footnote_bullets,
    strip_footnote_markers,
)

# the Schedule table, rewritten by hand. The Schedule headings and the table heading are
# folded into one header. The (a), (b) items have no "- " so a split can only fall between
# Level 1 and Level 2
_SCHEDULE_FLAT = """## **SCHEDULE - Discretionary civil penalties (regulation 5)**

[Editors note: the below is a flattened table]

Discretionary civil penalty - percentage of relevant income:

- Level 1 - up to 5% of relevant income: A penalty may be imposed at this level in cases where there has been a serious regulatory failing where any of the following factors are present but none of the factors in Level 2 are present -
   (a) the serious regulatory failing has resulted in a risk of significant loss to any of the regulated entity's customers;
   (b) the serious regulatory failing has resulted in a significant risk of financial crime; or
   (c) the serious regulatory failing is attributable to serious negligence by any of the regulated entity's directors, controllers, principal control officers, managers or the chief executive.
- Level 2 - up to 8% of relevant income: A penalty may be imposed at this level in cases where there has been a serious regulatory failing where the following factors are present -
   (a) the serious regulatory failing has resulted in a significant loss to any of the regulated entity's customers;
   (b) the serious regulatory failing has resulted in financial crime;
   (c) the serious regulatory failing was incurred deliberately by any of the regulated entity's directors, controllers, principal control officers, managers or the chief executive in order to obtain a benefit or mitigate a loss;
   (d) any of the regulated entity's directors, controllers, principal control officers, managers or the chief executive have attempted to conceal the serious regulatory failing from the Authority; or
   (e) the serious regulatory failing is attributable to serious deficiencies in any of -
      (i) the regulated entity's corporate governance;
      (ii) the regulated entity's systems and internal controls; or
      (iii) the fitness and propriety of any of the regulated entity's directors, controllers, principal control officers, managers or the chief executive.

"""

_REPLACEMENT_DICT = {
    # regulation number and title on separate headings
    "## **3** \n\n## **Interpretation**": "## **3 Interpretation**",
    # two terms on one line, split so each is picked up as a definition
    '**"the Act"** means the Insurance Act 2008 and " **section** " means a section of the Act;': '- " **the Act** " means the Insurance Act 2008;\n\n- " **section** " means a section of the Act;',
    # definitions without a bullet or with the quotes outside the bold
    '**"business day"** means': '- " **business day** " means',
    '- **"commission"** means': '- " **commission** " means',
    '- **"customers"** includes': '- " **customers** " includes',
    # (iii) lost its bullet
    "\n\n(iii) where the decision of the Authority is varied": "\n\n      - (iii) where the decision of the Authority is varied",
}


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_section(text, "## **MADE", "## **ENDNOTES**", _SCHEDULE_FLAT)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    text = strip_footnote_bullets(text)
    text = strip_footnote_markers(text)
    return text


_Trimmer = build_simple_markers(
    "## **3 Interpretation", "      (iii) the fitness and propriety of any of the"
)

# "relevant income" is the last term and its (a) to (c) and the two paragraphs after it
# belong to it, so the definitions end on the last of those paragraphs
_DefMarkers = build_simple_markers(
    '- " **the Act', "In order for commission to be netted from relevant income"
)

_DefTools = DefinitionTools(
    section_markers=[_DefMarkers],
    is_definition_line=starts_with(['- " **']),
)

_Splitters = ChunkSplitters(
    primary=split_on_bracketed_num, fallback=split_on_paragraph_or_list_item
)


def _is_section(line: str) -> bool:
    return (line.startswith("## **") and line[5].isdigit()) or line.startswith(
        "## **SCHEDULE"
    )


# current and former authorised insurers, registered insurance managers and registered
# insurance intermediaries
InsuranceCivPenRegs = ToolBelt(
    document="Insurance (Civil Penalties) Regulations 2023",
    hierarchy="secondary legislation",
    sectors=fixed_sectors(IA08_FIRMS),
    input_url="https://www.iomfsa.im/media/3194/insurancecivilpenaltiesregulations2023.pdf",
    pdf_path=build_pdf_path("insurance_civ_pen_regs"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[_is_section],
    definition_tools=_DefTools,
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
