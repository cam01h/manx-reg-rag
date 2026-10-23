import re
from collections.abc import Callable

from config import MAX_CHUNK_CHAR, PROJECT_ROOT
from core.sectors import ALL_SECTORS
from extraction_ops.models import (
    ChunkSplitters,
    DefinitionTools,
    SectionMarkers,
    ToolBelt,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_body_cleaner,
    base_double_def_line,
    base_false_double_def,
    base_header_cleaner,
    base_text_cleaner,
    fixed_sectors,
    replace_from_dict,
    split_on_bracketed_amended_num,
    split_on_bracketed_letter,
    split_on_paragraph,
    starts_with,
    strip_footnote_markers,
)

from .rule_book_flattener import (
    APPENDIX6_START,
    APPENDIX6_START_FIXED,
    PII_ONE_LINE,
    PII_TABLE_FLAT,
    fix_rule_3_24_table_order,
    flatten_appendix_2_table,
    flatten_appendix_3,
    flatten_appendix_4_table_b,
    flatten_definitions_table,
    flatten_rule_book_tables,
    strip_appendix_page_heads,
)
from .rule_book_handler import (
    rule_book_unbox_single_row_note_tables,
)

_RUNNING_HEAD = re.compile(
    r"^(?:"
    r"## (?:c SD No\.2016/0264 Page \d+|Page \d+ SD No\.2016/0264 c)"
    r"|(?:SCHEDULE|Index) Financial Services Rule Book 2016"
    r"|Financial Services Rule Book 2016(?: SCHEDULE| Index)?"
    r"|\(Rule [\d.]+\)(?: Financial Services Rule Book 2016)?"
    r"|\d{1,2} (?:SD \d+/\d+|AT \d+ of \d{4}|\d{4} c\.\d+)"
    r")[ \t]*$\n?",
    re.MULTILINE,
)

_TRIPPLE_DEF = '"**option**", "**future**" and "**contract for differences**" mean investments falling within paragraphs (g), (h) and (i) respectively of the definition of "**investment**" in Schedule 2 to the Order; a client\'s "**required contribution**" is the greater of -'
_TRIPPLE_DEF_FIXED = '\n"**future**" and "**contract for differences**" mean investments falling within paragraphs (g), (h) and (i) respectively of the definition of "**investment**" in Schedule 2 to the Order;\n "**option**" mean investments falling within paragraphs (g), (h) and (i) respectively of the definition of "**investment**" in Schedule 2 to the Order;\n "**required contribution**" a client\'s required contribution is the greater of -'


_REPLACEMENT_DICT = {
    "thatperson": "that person",
    "theperson": "the person",
    "offexchange": "off-exchange",
    "subparagraph": "sub-paragraph",
    # splitting definitions
    'of the licenceholder; "**client bank account**",': 'of the licenceholder;\n"**client bank account**",',
    'client bank account; "**client free': 'client bank account;\n"**client free',
    "owed by the licenceholder; \"**'client company'": 'owed by the licenceholder;\n"**client company',
    'detailed in rule 3.9; "**client money**" means': 'detailed in rule 3.9;\n"**client money**" means',
    'bank account; "**client settlement': 'bank account;\n"**client settlement',
    'detailed in rule 3.9; "**general client': 'detailed in rule 3.9;\n"**general client',
    'in rule 3.9; "**money**" means': 'in rule 3.9;\n"**money**" means',
    'electronic form; "**nominee bank': 'electronic form;\n"**nominee bank',
    'is client money; "**recognised': 'is client money;\n"**recognised',
    'recognised bank; "**relevant': 'recognised bank;\n"**relevant',
    'in rule 3.9; "**subscription and/or redemption account**" means': 'in rule 3.9;\n "**subscription account" or "redemption account**" means',
    'in rule 3.9; "**trust bank': 'in rule 3.9;\n"**trust bank',
    'money of that trust; "**trust money': 'money of that trust;\n"**trust money',
    # 3.22
    'corresponding meaning; "**margined client': 'corresponding meaning;\n"**margined client',
    _TRIPPLE_DEF: _TRIPPLE_DEF_FIXED,
    "payment transaction; and in rules": "payment transaction;\nand in rules",
    'country; "**investment': 'country;\n"**investment',
    'investment scheme; "**registrable': 'investment scheme;\n"**registrable',
    'in a register; "**safe-custody': 'in a register;\n"**safe-custody',
    'relationship); "**title document': 'relationship);\n"**title document',
    PII_ONE_LINE: PII_TABLE_FLAT,
    APPENDIX6_START: APPENDIX6_START_FIXED,
}


def fix_italics_spacing(text: str) -> str:
    return re.sub(r"([A-Za-z])_(?=[A-Z])", r"\1 _", text)


def typo_fix_on_icaap(text: str) -> str:
    return text.replace(
        '"internal capital adequacy assessment" process"',
        '"internal capital adequacy assessment process"',
    )


def _clean_text(text: str) -> str:
    text = base_text_cleaner(text)
    text = fix_italics_spacing(text)
    text = flatten_rule_book_tables(text)
    text = fix_rule_3_24_table_order(text)
    text = flatten_definitions_table(text)
    text = flatten_appendix_2_table(text)
    text = flatten_appendix_3(text)
    text = flatten_appendix_4_table_b(text)
    text = strip_appendix_page_heads(text)
    text = typo_fix_on_icaap(text)  # typo in orgional
    text = _RUNNING_HEAD.sub("", text)
    text = strip_footnote_markers(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    return text


RuleBookS4Defs = SectionMarkers(
    start=starts_with(['" **the Act** " means the']),
    end=starts_with(['" **the Order** " means the Regulated']),
)

RuleBookR3p2 = SectionMarkers(
    start=starts_with(['In this Part - "**client']),
    end=starts_with(['"**trust money**" means money']),
)

RuleBookR3p22 = SectionMarkers(
    start=starts_with(["- (10) In this rule - a client's \"**equity"]),
    end=starts_with(["   - (b) the aggregate of the client"]),
)

RuleBookR3p35 = SectionMarkers(
    start=starts_with(['In this Rule Book, "**relevant']),
    end=starts_with(['and in rules 3.35 to 3.42 - "**recognised']),
)


RuleBookR4p2 = SectionMarkers(
    start=starts_with(['- (1) In this Part - "**eligible custodian']),
    end=starts_with(["   - (b) acts only in accordance with the"]),
)


RuleBookR5p1 = SectionMarkers(
    start=starts_with(['In this Rule Book, "**auditor']),
    end=starts_with(["   - (b) has been excepted"]),
)

RuleBookR8p1 = SectionMarkers(
    start=starts_with(
        ['In rules 8.1 to 8.32, in relation to any licenceholder, "**the**']
    ),
    end=starts_with(["   - (ix) the Collective Investment Schemes"]),
)


RuleBookR9p37 = SectionMarkers(
    start=starts_with(['- **"accommodation address']),
    end=starts_with(['- **"warrant"** has the same meaning as in the Order']),
)


RuleBookDefTools = DefinitionTools(
    section_markers=[
        RuleBookS4Defs,
        RuleBookR3p2,
        RuleBookR3p22,
        RuleBookR3p35,
        RuleBookR4p2,
        RuleBookR5p1,
        RuleBookR8p1,
        RuleBookR9p37,
    ],
    is_definition_line=starts_with(
        [
            '" **',
            "In this Part",
            '"**',
            "In this Rule Book",
            "- (1) In this Part",
            '- **"',
            ' "**',
        ]
    ),
    is_double_def_line=base_double_def_line,
    is_false_dub_def=base_false_double_def,
)

FsaTrimmer = SectionMarkers(
    start=starts_with(["**1** **Title**"]),
    end=starts_with(["not exercised by the licenceholder."]),
)


def split_on_list_item(text: str) -> list[str]:
    return re.split(r"\n(?=- )", text)


def cascade(*splitters: Callable[[str], list[str]]) -> Callable[[str], list[str]]:
    def inner(text: str) -> list[str]:
        if len(text) <= MAX_CHUNK_CHAR or not splitters:
            return [text]
        first, rest = splitters[0], cascade(*splitters[1:])
        return [piece for part in first(text) for piece in rest(part)]

    return inner


TemplateSplitters = ChunkSplitters(
    primary=split_on_bracketed_amended_num,
    fallback=cascade(split_on_bracketed_letter, split_on_paragraph, split_on_list_item),
)


def is_top(line: str) -> bool:
    return line.startswith(("**SCHEDULE", "**Appendix "))


def is_part(line: str) -> bool:
    return line.startswith(("#### **PART", "**APPENDIX "))


_FRONT_MATTER = re.compile(r"^\*\*\d\*\* \*\*")  # "**1** **Title**"


def is_rule(line: str) -> bool:
    return line.startswith("## **") or bool(_FRONT_MATTER.match(line))


RuleBook = ToolBelt(
    document="Financial Services Rule Book 2016",
    hierarchy="secondary legislation",
    sectors=fixed_sectors(ALL_SECTORS),
    input_url="https://www.iomfsa.im/media/1470/financialservicesrulebook20131.pdf",
    pdf_path=PROJECT_ROOT / "data/raw/custom/rule_book.pdf",
    use_ocr=True,
    use_layout=False,
    pdf_handlers=[rule_book_unbox_single_row_note_tables],
    trimmer=FsaTrimmer,
    header_matchers=[is_top, is_part, is_rule],
    definition_tools=RuleBookDefTools,
    clean_text=_clean_text,
    re_pack_splitters=TemplateSplitters,
    clean_body=base_body_cleaner,
    clean_header=base_header_cleaner,
    min_body_len=40,
)
