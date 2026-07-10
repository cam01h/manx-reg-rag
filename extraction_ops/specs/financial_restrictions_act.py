import re
from config import project_root
from .specs import DocSpecs


def re_steps(text: str) -> str:
    text = re.sub(
        r"## \*\*(\d+[A-Z]?)\*\*\s*\n\s*## \*\*([^\n*]+)\*\*",
        r"## **\1 \2**",
        text,
    )
    text = re.sub(r"\*\*\[\d+\]\*\*|\[\d+\]|\[Sections? [^\]]*\]", "", text)
    text = re.sub(r"^> \d+ .*$\n?", "", text, flags=re.MULTILINE)
    text = re.sub(
        r"warrant issued under the \.\s*\n+\s*-\s*(_Interception of Communications Act 1988_)",
        r"warrant issued under the \1.",
        text,
    )
    text = text.replace("AntiTerrorism", "Anti-Terrorism")
    return text


FinancialRestrictionsAct = DocSpecs(
    document="Terrorism and Other Crime (Financial Restrictions) Act 2014",
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/PRINCIPAL/2014/2014-0013/2014-0013.pdf?zoom_highlight=Financial+Restrictions+Act+2014#search=%22Financial%20Restrictions%20Act%202014%22",
    hierarchy="legislation",
    input_path=project_root / "data/raw/custom/financial_restrictions_act.pdf",
    major_name="part",
    minor_name="paragraph",
    start_line=168,
    end_line=2279,
    definitions_start=16,
    definitions_end=141,
    re_steps=re_steps,
    header_matchers=[
        lambda line: line.startswith("## **PART") or line.startswith("## **SCHEDULE"),
        lambda line: line.startswith("## DIVISION") or line.startswith("DIVISION"),
        lambda line: (
            line.startswith("## SUB-DIVISION") or line.startswith("SUB-DIVISION")
        ),
        lambda line: line.startswith("## **") and line[5].isdigit(),
    ],
    has_definition_section=True,
    is_definition_line=lambda line: '## " **' in line or '- " **' in line,
    is_double_def_line=lambda segs: len(segs) == 5 and segs[2].strip() in ("or", "and"),
    is_false_dub_def=lambda segs: len(segs) == 5 and segs[2].strip() != "or",
    re_pack_splitter=lambda text: re.split(r"\n(?=- \(\d+[A-Z]*\))", text),
    # TODO: large chunk at 2297 chars. large list and needs the intro carry mentioned in DBROA
    strip_md=lambda line: (
        line.replace("##", "").replace("**", "").replace("_", "").strip()
    ),
    h_strip_md=lambda line: (
        line.replace("- **", "")
        .replace("##", "")
        .replace("**", "")
        .replace("_", "")
        .strip()
    ),
)
