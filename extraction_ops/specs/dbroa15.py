import re
from config import project_root
from extraction_ops.specs.shared_funcs import flatten_schedule_table, replace_from_dict
from .specs import DocSpecs


GLUED_WORD_FIXES = {
    "Apayroll": "A payroll",
    "inparagraph": "in paragraph",
    "toparagraph": "to paragraph",
    "activityof": "activity of",
    "serviceprovider": "service provider",
    "Administeringor managingmoneyon behalf of anotherperson": "Administering or managing money on behalf of another person",
    "moneyon": "money on",
    "agent,as": "agent, as",
    "currency)that": "currency) that",
}


def re_steps(text: str) -> str:
    text = re.sub(r"\*\*\[\d+\]\*\*|\[\d+\]|\[Sections? [^\]]*\]", "", text)
    text = re.sub(
        r"## \*\*(\d+[A-Z]?)\*\*\s*\n\s*## \*\*([^\n*]+)\*\*",
        r"## **\1 \2**",
        text,
    )
    text = flatten_schedule_table(text)
    text = replace_from_dict(text, GLUED_WORD_FIXES)
    return text


Dbroa = DocSpecs(
    document="DESIGNATED BUSINESSES (REGISTRATION AND OVERSIGHT) ACT 2015",
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/PRINCIPAL/2015/2015-0009/2015-0009.pdf?zoom_highlight=Designated+Businesses+Registration+and+Oversight+Act+2015#search=%22Designated%20Businesses%20Registration%20and%20Oversight%20Act%202015%22",
    hierarchy="legislation",
    input_path=project_root / "data/raw/custom/dbroa15.pdf",
    major_name="part",
    minor_name="paragraph",
    start_line=93,
    end_line=1306,
    definitions_start=16,
    definitions_end=147,
    re_steps=re_steps,
    header_matchers=[
        lambda line: line.startswith("## **SCHEDULE"),
        lambda line: line.startswith("## **PART"),
        lambda line: line.startswith("## DIVISION"),
        lambda line: line.startswith("## **") and line[5].isdigit(),
    ],
    has_definition_section=True,
    is_definition_line=lambda line: (
        line.startswith('- " **')
        or line.startswith('## " **')
        or 'In this Act " **' in line
    ),
    is_double_def_line=lambda segs: len(segs) == 5 and segs[2].strip() in ("or", "and"),
    is_false_dub_def=lambda segs: len(segs) == 5 and segs[2].strip() != "or",
    re_pack_splitter=lambda text: re.split(
        r"\n(?=\d+\.\s|- \(\d+\)|- \([a-z]{1,2}\)|- [a-z]\.)", text, flags=re.IGNORECASE
    ),
    # TODO: splits schedule 1 on the (h), (o), (u) which loses the intro to the what its a lst of. Add intro line buffer for back up split
    strip_md=lambda line: (
        line.replace("## **", "").replace("**", "").strip().replace("_", "")
    ),
    h_strip_md=lambda line: (
        line.replace("- **", "")
        .replace("##", "")
        .replace("**", "")
        .replace(" — ", "")
        .replace("_", "")
        .strip()
    ),
)
