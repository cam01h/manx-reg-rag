import re
from collections.abc import Callable

from config import MAX_CHUNK_CHAR
from extraction_ops.models import (
    ChunkSplitters,
    DefinitionTools,
    SectionMarkers,
    ToolBelt,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
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
    TRIPLE_DEF,
    TRIPLE_DEF_SPLIT,
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
from .rule_book_sectors import RB_ALL, RULE_BOOK_SECTORS

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
    'the position; "**option': 'the position;\n"**option',
    "Order; a client's \"**required": "Order;\na client's \"**required",
    # 3.22
    'corresponding meaning; "**margined client': 'corresponding meaning;\n"**margined client',
    "payment transaction; and in rules": "payment transaction;\nand in rules",
    'country; "**investment': 'country;\n"**investment',
    'investment scheme; "**registrable': 'investment scheme;\n"**registrable',
    'in a register; "**safe-custody': 'in a register;\n"**safe-custody',
    'relationship); "**title document': 'relationship);\n"**title document',
    'Part applies; "**specified': 'Part applies;\n"**specified',
    'margined transaction; "**margined transaction': 'margined transaction;\n"**margined transaction',
    "paragraph\n- (5) of Class": "paragraph (5) of Class",
    "Financial Services and Markets Act 20006": "Financial Services and Markets Act 2000",
    'a client\'s "**required contribution**"': '"**required contribution**" a client\'s required contribution',
    '"**the** **regulatory requirements**"': 'the "**regulatory requirements**"',
    '- **"trust service provider" ("TSP")**': '- **"trust service provider" or "TSP"**',
    '- **"adjusted capital base" ("ACB")**': '- **"adjusted capital base" or "ACB"**',
    '- **"corporate service provider" ("CSP")**': '- **"corporate service provider" or "CSP"**',
    '- **"internal capital adequacy assessment process" ("ICAAP")**': '- **"internal capital adequacy assessment process" or "ICAAP"**',
    '- **"large exposures capital base" ("LECB")**': '- **"large exposures capital base" or "LECB"**',
    '- **"risk-asset ratio" ("RAR")**': '- **"risk-asset ratio" or "RAR"**',
    "paragraph\n- (5) acting as": "paragraph (5) acting as",
    '- **"electronic money"** has the same meaning as in the Order;\n- **"e-money"** has the same meaning as electronic money;': '- **"electronic money" or "e-money"** has the same meaning as in the Order;',
    PII_ONE_LINE: PII_TABLE_FLAT,
    APPENDIX6_START: APPENDIX6_START_FIXED,
    TRIPLE_DEF: TRIPLE_DEF_SPLIT,
    # duplicate definitions
    '- **"the Act"** means the Financial Services Act 2008;': "",
    '- **"the Order"** means the Regulated Activities Order 2011;': "",
    '- **"specified client bank account"** has the meaning given by rule 3.2 for the purposes of Part 3;': "",
    '- **"client free money account"** has the meaning given by rule 3.2 for the purposes of Part 3;': "",
    '- **"client money"** has the meaning given by rule 3.2;': "",
    '- **"client settlement account"** has the meaning given by rule 3.2 for the purposes of Part 3;': "",
    "- **\"'client company' bank account\"** has the meaning given by rule 3.2 for the purposes of Part 3;": "",
    '- **"contract for differences"** has the meaning given in rule 3.22(10);': "",
    '- **"equity balance"** has the meaning given by rule 3.22(10);': "",
    '- **"future"** has the meaning given in rule 3.22(10);': "",
    '- **"general client bank account"** has the meaning given by rule 3.2 for the purposes of Part 3;': "",
    '- **"margined client money"** has the meaning given in rule 3.22(10);': "",
    '- **"margined transaction"** has the meaning given in rule 3.22(10);': "",
    '- **"money"** has the meaning given by rule 3.2 for the purposes of Part 3;': "",
    '- **"nominee bank account"** has the meaning given by rule 3.2 for the purposes of Part 3;': "",
    '- **"option"** has the meaning given in rule 3.22(10);': "",
    '- **"recognised bank"** has the meaning given by rule 3.2 for the purposes of Part 3;': "",
    '- **"relevant agreement"** has the meaning given by rule 3.2 for the purposes of Part 3;': "",
    '- **"relevant funds"** has the meaning given in rule 3.35;': "",
    '- **"required contribution"** has the meaning given in rule 3.22(10);': "",
    '- **"regulatory requirements"** has the meaning given in rule 8.1;': "",
    '- **"subscription and/or redemption account"** has the meaning given by rule 3.2 for the purposes of Part 3;': "",
    '- **"trust bank account"** has the same meaning as in the Order and has the meaning given by rule 3.2 for the purposes of Part 3;': "",
    '- **"trust money"** has the meaning given by rule 3.2;': "",
    '- **"client bank account"** has the meaning given by rule 3.2 for the purposes of Part 3;': "",
    '- **"auditor"** has the meaning given in rule 5.1;': "",
}


def _fix_italics_spacing(text: str) -> str:
    return re.sub(r"([A-Za-z])_(?=[A-Z])", r"\1 _", text)


def _typo_fix_on_icaap(text: str) -> str:
    return text.replace(
        '"internal capital adequacy assessment" process"',
        '"internal capital adequacy assessment process"',
    )


def _clean_text(text: str) -> str:
    text = base_text_cleaner(text)
    text = _fix_italics_spacing(text)
    text = flatten_rule_book_tables(text)
    text = fix_rule_3_24_table_order(text)
    text = flatten_definitions_table(text)
    text = flatten_appendix_2_table(text)
    text = flatten_appendix_3(text)
    text = flatten_appendix_4_table_b(text)
    text = strip_appendix_page_heads(text)
    text = _typo_fix_on_icaap(text)  # typo in orgional
    text = _RUNNING_HEAD.sub("", text)
    text = strip_footnote_markers(text)
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    return text


_RuleBookS4Defs = SectionMarkers(
    start=starts_with(['" **the Act** " means the']),
    end=starts_with(['" **the Order** " means the Regulated']),
)

_RuleBookR3p2 = SectionMarkers(
    start=starts_with(['In this Part - "**client']),
    end=starts_with(['"**trust money**" means money']),
)

_RuleBookR3p22 = SectionMarkers(
    start=starts_with(["- (10) In this rule - a client's \"**equity"]),
    end=starts_with(["   - (b) the aggregate of the client"]),
)

_RuleBookR3p35 = SectionMarkers(
    start=starts_with(['In this Rule Book, "**relevant']),
    end=starts_with(['and in rules 3.35 to 3.42 - "**recognised']),
)


_RuleBookR4p2 = SectionMarkers(
    start=starts_with(['- (1) In this Part - "**eligible custodian']),
    end=starts_with(["   - (b) acts only in accordance with the"]),
)


_RuleBookR5p1 = SectionMarkers(
    start=starts_with(['In this Rule Book, "**auditor']),
    end=starts_with(["   - (b) has been excepted"]),
)

_RuleBookR8p1 = SectionMarkers(
    start=starts_with(["In rules 8.1 to 8.32, in relation to any licenceholder,"]),
    end=starts_with(["   - (ix) the Collective Investment Schemes"]),
)


_RuleBookR9p37 = SectionMarkers(
    start=starts_with(['- **"accommodation address']),
    end=starts_with(['- **"warrant"** has the same meaning as in the Order']),
)


_DefTools = DefinitionTools(
    section_markers=[
        _RuleBookS4Defs,
        _RuleBookR3p2,
        _RuleBookR3p22,
        _RuleBookR3p35,
        _RuleBookR4p2,
        _RuleBookR5p1,
        _RuleBookR8p1,
        _RuleBookR9p37,
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
            "- (10) In this rule",
            "In rules 8.1 to 8.32",
            "and in rules 3.35 to 3.42",
        ]
    ),
)

_Trimmer = SectionMarkers(
    start=starts_with(["**1** **Title**"]),
    end=starts_with(["not exercised by the licenceholder."]),
)


def _split_on_list_item(text: str) -> list[str]:
    return re.split(r"\n(?=- )", text)


def _cascade(*splitters: Callable[[str], list[str]]) -> Callable[[str], list[str]]:
    def inner(text: str) -> list[str]:
        if len(text) <= MAX_CHUNK_CHAR or not splitters:
            return [text]
        first, rest = splitters[0], _cascade(*splitters[1:])
        return [piece for part in first(text) for piece in rest(part)]

    return inner


_Splitters = ChunkSplitters(
    primary=split_on_bracketed_amended_num,
    fallback=_cascade(
        split_on_bracketed_letter, split_on_paragraph, _split_on_list_item
    ),
)


def _is_top(line: str) -> bool:
    return line.startswith(("**SCHEDULE", "**Appendix "))


def _is_part(line: str) -> bool:
    return line.startswith(("#### **PART", "**APPENDIX "))


_FRONT_MATTER = re.compile(r"^\*\*\d\*\* \*\*")  # "**1** **Title**"


def _is_rule(line: str) -> bool:
    return line.startswith("## **") or bool(_FRONT_MATTER.match(line))


_RULE_NO = re.compile(r"^(\d+\.\d+[A-Z]?)\b")


def _rule_book_sectors(headers: tuple[str, ...]) -> tuple[str, ...]:
    for header in headers:
        match = _RULE_NO.match(header)
        if match:
            return RULE_BOOK_SECTORS[match.group(1)]
    return RB_ALL


RuleBook = ToolBelt(
    document="Financial Services Rule Book 2016",
    hierarchy="secondary legislation",
    sectors=_rule_book_sectors,
    input_url="https://www.iomfsa.im/media/1470/financialservicesrulebook20131.pdf",
    pdf_path=build_pdf_path("rule_book"),
    use_layout=False,
    pdf_handlers=[rule_book_unbox_single_row_note_tables],
    trimmer=_Trimmer,
    header_matchers=[_is_top, _is_part, _is_rule, starts_with(["Application:"])],
    definition_tools=_DefTools,
    clean_text=_clean_text,
    re_pack_splitters=_Splitters,
)
