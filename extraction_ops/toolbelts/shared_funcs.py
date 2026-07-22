import re


# helpers
def replace_from_dict(text: str, replacements: dict[str, str]) -> str:
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text


def strip_patterns(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        text = re.sub(pattern, "", text)
    return text


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
    line = line.replace("## **", "").replace("##", "").replace("**", "").strip()
    return line


def base_text_cleaner(text: str):
    replacements = {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2013": "-",
        "\u2014": "-",
    }
    return replace_from_dict(text, replacements)


# splitters
def split_on_bracketed_num(text: str) -> list[str]:
    return re.split(r"\n(?=- \(\d+\))", text)


def split_on_bracketed_letter(text: str) -> list[str]:
    return re.split(r"\n(?=- \([a-z]+\))", text)


def split_on_new_sentence(text: str) -> list[str]:
    return re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)


# definition line matchers
def base_def_line(line: str) -> bool:
    return in_line(line, ['- **"', '## **"']) or starts_with(line, ['**"'])


def base_double_def_line(segs: list[str]) -> bool:
    return len(segs) == 5 and segs[2].strip() in ("or", "and")


def base_false_double_def(segs: list[str]) -> bool:
    return len(segs) == 5 and segs[2].strip() != "or"
