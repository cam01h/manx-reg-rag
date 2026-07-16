import re


# line -> bool
def in_line(line: str, strings: list[str]) -> bool:
    for string in strings:
        if string in line:
            return True
    return False


def starts_with(line: str, strings: list[str]) -> bool:
    for string in strings:
        if line.startswith(string):
            return True
    return False


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
    return header


def base_body_cleaner(line: str) -> str:
    line.replace("## **", "").replace("##", "").replace("**", "").strip()
    return line


# splitters
def split_on_bracketed_num(text: str) -> list[str]:
    return re.split(r"\n(?=- \(\d+\))", text)


def split_on_bracketed_letter(text: str) -> list[str]:
    return re.split(r"\n(?=- \([a-z]+\))", text)


# definition line matchers
def base_def_line(line: str) -> bool:
    return in_line(line, ['- **"', '## **"']) or starts_with(line, ['**"'])


def base_double_def_line(segs: list[str]) -> bool:
    return len(segs) == 5 and segs[2].strip() in ("or", "and")


def base_false_double_def(segs: list[str]) -> bool:
    return len(segs) == 5 and segs[2].strip() != "or"
