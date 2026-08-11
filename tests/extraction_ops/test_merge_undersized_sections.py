import pytest
from extraction_ops.chunking import merge_undersized_sections
from extraction_ops.models import CleanSection, ToolBelt


test_1 = [
    CleanSection(headers=("section 1", "merge two"), body="this is a short section"),
    CleanSection(
        headers=("section 1", "merge two"), body="this is also a short section"
    ),
]

expected_1 = [
    CleanSection(
        headers=("section 1", "merge two"),
        body=("this is a short section\n\nthis is also a short section"),
    ),
]

test_2 = [
    CleanSection(
        headers=("section 2", "no merge"),
        body="this is a short section that shouldn't merge",
    ),
    CleanSection(
        headers=("section 2", "no header match"),
        body="the headers should match for a merge and these dont match",
    ),
]

expected_2 = [
    CleanSection(
        headers=("section 2", "no merge"),
        body="this is a short section that shouldn't merge",
    ),
    CleanSection(
        headers=("section 2", "no header match"),
        body="the headers should match for a merge and these dont match",
    ),
]

test_3 = [
    CleanSection(
        headers=("section 3", "shouldn't merge"),
        body=(
            "Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.\n"
            "Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.\n"
            "Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.\n"
            "Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.\n"
            "Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.\n"
            "Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.\n"
        ),
    ),
    CleanSection(
        headers=("section 3", "shouldn't merge"),
        body="even though this section is small, it shouldn't merge as the previous section",
    ),
]

expected_3 = [
    CleanSection(
        headers=("section 3", "shouldn't merge"),
        body=(
            "Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.\n"
            "Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.\n"
            "Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.\n"
            "Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.\n"
            "Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.\n"
            "Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.\n"
        ),
    ),
    CleanSection(
        headers=("section 3", "shouldn't merge"),
        body="even though this section is small, it shouldn't merge as the previous section",
    ),
]

test_4 = [
    CleanSection(
        headers=("section 4", "all sections should merge"),
        body="small body to allow multiple merges",
    ),
    CleanSection(
        headers=("section 4", "all sections should merge"),
        body="small body to allow multiple merges",
    ),
    CleanSection(
        headers=("section 4", "all sections should merge"),
        body="small body to allow multiple merges",
    ),
    CleanSection(
        headers=("section 4", "all sections should merge"),
        body="small body to allow multiple merges",
    ),
    CleanSection(
        headers=("section 4", "all sections should merge"),
        body="small body to allow multiple merges",
    ),
]

expected_4 = [
    CleanSection(
        headers=("section 4", "all sections should merge"),
        body=(
            "small body to allow multiple merges\n\n"
            "small body to allow multiple merges\n\n"
            "small body to allow multiple merges\n\n"
            "small body to allow multiple merges\n\n"
            "small body to allow multiple merges"
        ),
    )
]

MERGE_UNDERSIZED_SECTIONS_DATA = [
    (test_1, expected_1),
    (test_2, expected_2),
    (test_3, expected_3),
    (test_4, expected_4),
]


@pytest.mark.parametrize("unprocessed, expected", MERGE_UNDERSIZED_SECTIONS_DATA)
def test_merge_undersized_chunks(
    unprocessed: list[CleanSection],
    test_toolbelt: ToolBelt,
    expected: list[CleanSection],
):
    result = merge_undersized_sections(unprocessed)
    assert result == expected
