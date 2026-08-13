"""
def base_def_line(line: str) -> bool:
    prefixes = ['- **"', '## **"', '**"']
    return any(line.startswith(p) for p in prefixes)


def base_double_def_line(segs: list[str]) -> bool:
    return len(segs) == 5 and segs[2].strip() in ("or", "and")


def base_false_double_def(segs: list[str]) -> bool:
    return len(segs) == 5 and segs[2].strip() != "or"
"""

import pytest
from extraction_ops.definitions import extract_to_definitions
from extraction_ops.models import Definition, ToolBelt


input_1 = [
    '- **"thing"** means an item',
    "or some other general thingy",
    '- **"item"** means a thing',
    "and can also mean a thingy",
]

expected_1 = [
    Definition(
        document="test model",
        term="thing",
        definition="means an item\nor some other general thingy",
    ),
    Definition(
        document="test model",
        term="item",
        definition="means a thing\nand can also mean a thingy",
    ),
]
input_2 = [
    '- **"this"** or **"that"** means a specific thing',
    "and includes some extra body text",
    '- **"another"** means something else',
]

expected_2 = [
    Definition(
        document="test model",
        term="this",
        definition="means a specific thing\nand includes some extra body text",
    ),
    Definition(
        document="test model",
        term="that",
        definition="means a specific thing\nand includes some extra body text",
    ),
    Definition(
        document="test model",
        term="another",
        definition="means something else",
    ),
]

input_3 = [
    '- **"term"** means a specific thing',
    "this will test unusual format of lines",
    "",
    " (a) ulvinar vivamus fringilla lacus nec metus bibendum egestas.",
    "     Iaculis massa nisl malesuada lacinia integer nunc posuere.",
    "     Ut hendrerit semper vel class aptent taciti sociosqu",
    "",
    "## **random subheader**",
    "- ulvinar vivamus fringilla lacus nec metus bibendum egestas",
]
expected_3 = [
    Definition(
        document="test model",
        term="term",
        definition=(
            "means a specific thing\n"
            "this will test unusual format of lines\n"
            "\n"
            "(a) ulvinar vivamus fringilla lacus nec metus bibendum egestas.\n"
            "Iaculis massa nisl malesuada lacinia integer nunc posuere.\n"
            "Ut hendrerit semper vel class aptent taciti sociosqu\n"
            "\n"
            "random subheader\n"
            "- ulvinar vivamus fringilla lacus nec metus bibendum egestas"
        ),
    ),
]

input_4 = [
    '- **"term"** means a "quoted phrase" in the text',
    "and some extra body text",
]

expected_4 = [
    Definition(
        document="test model",
        term="term",
        definition='means a "quoted phrase" in the text\nand some extra body text',
    ),
]

input_5 = [
    '- **"fallback term"** means a very long definition that has a "broken quote inside the definition body text which makes the segment count equal to four instead of three or five, triggering the fallback logic in the parser',
    "and this is some extra body text to make it a long test case as requested",
]

expected_5 = [
    Definition(
        document="test model",
        term="fallback term",
        definition=(
            "means a very long definition that has a broken quote "
            "inside the definition body text which makes the segment count equal to four instead of three or five, triggering the fallback logic in the parser\n"
            "and this is some extra body text to make it a long test case as requested"
        ),
    ),
]

EXTRACT_TO_DEFINITIONS_DATA = [
    (input_1, expected_1),
    (input_2, expected_2),
    (input_3, expected_3),
    (input_4, expected_4),
    (input_5, expected_5),
]


@pytest.mark.parametrize("unprocessed, expected", EXTRACT_TO_DEFINITIONS_DATA)
def test_extract_to_definitions(
    unprocessed: list[str], test_toolbelt: ToolBelt, expected: list[Definition]
) -> None:
    result = extract_to_definitions(test_toolbelt, unprocessed)
    assert result == expected
