# definition line matchers
import re


def base_double_def_line(segs: list[str]) -> bool:
    return len(segs) == 5 and segs[2].strip() in ("or", "and")


def base_false_double_def(segs: list[str]) -> bool:
    return len(segs) == 5 and segs[2].strip() != "or"


# text cleaners
def base_header_cleaner(header: str) -> str:
    header = (
        header.replace("- ##", "")
        .replace("- **", "")
        .replace("#", "")
        .replace("*", "")
        .replace("_", "")
        .strip()
    )
    # lstrip added for handbook, extract to custom if it affects other docs
    return header.lstrip("- ")


def base_body_cleaner(line: str) -> str:
    line = (
        line.replace("## **", "")
        .replace("##", "")
        .replace("**", "")
        .replace("_", "")
        .strip()
    )
    return line


def default_primary_split(text: str) -> list[str]:
    return re.split(r"\n(?=[ \t]*(?:- )?\(\d+[A-Z]*\))", text)


def default_secondary_split(text: str) -> list[str]:
    return re.split(r"\n(?=[ \t]*(?:- )?\([a-z]+\))", text)
