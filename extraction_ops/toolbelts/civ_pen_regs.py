from core.sectors import RAO_CLASSES
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

# both tables in the Schedule, rewritten by hand. The two Schedule headings and the table
# headings are folded into one header per table. The (a), (b) items have no "- " so a split
# can only fall between Level 1 and Level 2
_SCHEDULE_FLAT = """## **SCHEDULE - Table 1 - Discretionary civil penalties (regulation 5)**

[Editors note: the below is a flattened table]

Discretionary civil penalty - percentage of the licenceholder's relevant income:

- Level 1 - up to 5% of relevant income: A penalty may be imposed at this level in cases where there has been a serious regulatory failing where any of the following factors are present but none of the factors in Level 2 are present -
   (a) the serious regulatory failing has resulted in a risk of significant loss to any of the licenceholder's customers;
   (b) the serious regulatory failing has resulted in a significant risk of financial crime; or
   (c) the serious regulatory failing is attributable to serious negligence by any of the licenceholder's directors, controllers or key persons.
- Level 2 - up to 8% of relevant income: A penalty may be imposed at this level in cases where there has been a serious regulatory failing where any of the following factors are present -
   (a) the serious regulatory failing has resulted in a significant loss to any of the licenceholder's customers;
   (b) the serious regulatory failing has resulted in financial crime;
   (c) the serious regulatory failing was incurred deliberately by any of the licenceholder's directors, controllers or key persons in order to obtain a benefit or mitigate a loss;
   (d) any of the licenceholder's directors, controllers or key persons have attempted to conceal the serious regulatory failing from the Authority; or
   (e) the serious regulatory failing is attributable to serious deficiencies in any of -
      (i) the licenceholder's corporate governance (if applicable);
      (ii) the licenceholder's systems and internal controls; or
      (iii) the fitness and propriety of any of the licenceholder's directors, controllers or key persons.

## **SCHEDULE - Table 2 - Administrative civil penalties (regulation 6)**

[Editors note: the below is a flattened table]

Administrative civil penalty - penalty for all classes of licenceholders except Class 1; penalty for Class 1(1) and 1(2) licenceholders:

- Return submitted/provided from 1 to 4 business days after end of specified period - all classes except Class 1: £100; Class 1(1) and 1(2): £100
- Return submitted/provided from 5 to 20 business days after end of specified period - all classes except Class 1: £500; Class 1(1) and 1(2): £1,000
- Return submitted/provided more than 20 business days after end of specified period - all classes except Class 1: £2,000; Class 1(1) and 1(2): £5,000

"""

_REPLACEMENT_DICT = {
    # two terms on one line, split so each is picked up as a definition
    '- " **the Act** " means the Financial Services Act 2008 and " **section** " means a section of the Act;': '- " **the Act** " means the Financial Services Act 2008;\n\n- " **section** " means a section of the Act;',
    # revoked definition with no body
    '## " **Commission** " [Revoked] **[3]** \n\n': "",
    # definition that lost its bullet and became a heading
    '## " **relevant income** " means': '- " **relevant income** " means',
    # statute footnote left in the middle of the "return" definition
    "4 SD 0884/2011 as amended by SD 0373/2013 \n\n": "",
    # back to back endnote markers, strip_footnote_markers leaves the "****"
    " **[14][15]**": "",
    " **[17][18]**": "",
    # footnote markers before punctuation would leave a space behind
    "_Bank Holidays Act 1989_[2] ;": "_Bank Holidays Act 1989_;",
    "(Isle of Man) Act 1973_[3] ,": "(Isle of Man) Act 1973_,",
    "Regulated Activities Order 2011[4] ;": "Regulated Activities Order 2011;",
}


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_section(text, "## **SCHEDULE**", "## **ENDNOTES**", _SCHEDULE_FLAT)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    text = strip_footnote_bullets(text)
    text = strip_footnote_markers(text)
    return text


_Trimmer = build_simple_markers(
    "## **3 Interpretation", "- Return submitted/provided more than 20"
)

_DefMarkers = build_simple_markers('- " **the Act', '- " **specified period')

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


# all current and former licenceholders (regulation 6 does not apply to Class 1(3) or 6)
CivPenRegs = ToolBelt(
    document="Financial Services (Civil Penalties) Regulations 2015",
    hierarchy="secondary legislation",
    sectors=fixed_sectors(RAO_CLASSES),
    input_url="https://www.iomfsa.im/media/1431/financialservicespenalties2015.pdf",
    pdf_path=build_pdf_path("civ_pen_regs"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[_is_section],
    definition_tools=_DefTools,
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
