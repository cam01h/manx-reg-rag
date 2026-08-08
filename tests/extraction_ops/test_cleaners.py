import pytest
from extraction_ops.load_to_md import clean_md_to_lines


# test 1
dirty_1 = "fancy double quotes: the word “hello” is considered a greeting"
clean_1 = ['fancy double quotes: the word "hello" is considered a greeting']

# test 2
dirty_2 = "fancy single quotes: the word ‘goodbye’ is considered a farewell"
clean_2 = ["fancy single quotes: the word 'goodbye' is considered a farewell"]

# test 3
dirty_3 = "en dash: normally – should be replaced"
clean_3 = ["en dash: normally - should be replaced"]

# test 4
dirty_4 = "em dash: the introduction to a list — list values"
clean_4 = ["em dash: the introduction to a list - list values"]

# test 5
dirty_5 = """testing all steps:\n“fancy double quotes”\n‘fancy single quotes’\nen dash –\nem dash —"""
clean_5 = [
    "testing all steps:",
    '"fancy double quotes"',
    "'fancy single quotes'",
    "en dash -",
    "em dash -",
]

CLEANING_TEST_DATA = [
    (dirty_1, clean_1),
    (dirty_2, clean_2),
    (dirty_3, clean_3),
    (dirty_4, clean_4),
    (dirty_5, clean_5),
]


@pytest.mark.parametrize("dirty, expected", CLEANING_TEST_DATA)
def test_clean_md_to_lines(test_toolbelt, dirty: str, expected: list[str]):
    result = clean_md_to_lines(test_toolbelt.clean_text, dirty)
    assert result == expected
