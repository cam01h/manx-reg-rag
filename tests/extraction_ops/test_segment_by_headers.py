import pytest
from extraction_ops.chunking import segment_by_headers
from extraction_ops.models import Section, ToolBelt


unsegmented_1 = [
    "## header 1",
    "**header 1.1**",
    "Purus est efficitur laoreet mauris pharetra vestibulum",
    "fusce. Praesent dui felis venenatis ultrices proin libero",
    "feugiat. Nisl malesuada lacinia integer nunc posuere ut",
    "hendrerit. At luctus nibh finibus facilisis dapibus etiam",
    "interdum. Cubilia curae hac habitasse platea dictumst",
    "lorem ipsum. Himenaeos orci varius natoque penatibus et",
    "magnis dis. Euismod quam justo lectus commodo augue arcu",
    "dignissim. Placerat in id cursus mi pretium tellus duis.",
    "**header 1.2**",
    "Maximus eget fermentum odio phasellus non purus est. Fames",
    "primis vulputate ornare sagittis vehicula praesent dui. Nec",
    "metus bibendum egestas iaculis massa nisl malesuada. Sodales",
    "consequat magna ante condimentum neque at luctus. Senectus",
    "netus suscipit auctor curabitur facilisi cubilia curae.",
    "## header 2",
    "**header 2.1**",
    "Litora torquent per conubia nostra inceptos himenaeos orci.",
    "Tincidunt nam porta elementum a enim euismod quam. Faucibus",
    "ex sapien vitae pellentesque sem placerat in. Eros lobortis",
    "nulla molestie mattis scelerisque maximus eget. Ullamcorper",
    "rutrum gravida cras eleifend turpis fames primis. Urna",
    "tempor pulvinar vivamus fringilla lacus nec metus. Risus",
    "blandit quis suspendisse aliquet nisi sodales consequat.",
    "**header 2.2**",
    "Accumsan maecenas potenti ultricies habitant morbi senectus",
    "netus. Vel class aptent taciti sociosqu ad litora torquent.",
    "Ligula congue sollicitudin erat viverra ac tincidunt nam.",
    "Sit amet consectetur adipiscing elit quisque faucibus ex.",
    "Montes nascetur ridiculus mus donec rhoncus eros lobortis.",
    "Aliquam imperdiet mollis nullam volutpat porttitor ullam",
    "rutrum. Tempus leo eu aenean sed diam urna tempor. Laoreet",
    "mauris pharetra vestibulum fusce dictum risus blandit.",
    "Venenatis ultrices proin libero feugiat tristique accumsan",
    "maecenas. Integer nunc posuere ut hendrerit semper vel class.",
    "Finibus facilisis dapibus etiam interdum tortor ligula congue.",
    "Habitasse platea dictumst lorem ipsum dolor sit amet.",
]

expected_1_section_1 = Section(
    headers=("## header 1", "**header 1.1**"),
    body_lines=[
        "Purus est efficitur laoreet mauris pharetra vestibulum",
        "fusce. Praesent dui felis venenatis ultrices proin libero",
        "feugiat. Nisl malesuada lacinia integer nunc posuere ut",
        "hendrerit. At luctus nibh finibus facilisis dapibus etiam",
        "interdum. Cubilia curae hac habitasse platea dictumst",
        "lorem ipsum. Himenaeos orci varius natoque penatibus et",
        "magnis dis. Euismod quam justo lectus commodo augue arcu",
        "dignissim. Placerat in id cursus mi pretium tellus duis.",
    ],
)

expected_1_section_2 = Section(
    headers=("## header 1", "**header 1.2**"),
    body_lines=[
        "Maximus eget fermentum odio phasellus non purus est. Fames",
        "primis vulputate ornare sagittis vehicula praesent dui. Nec",
        "metus bibendum egestas iaculis massa nisl malesuada. Sodales",
        "consequat magna ante condimentum neque at luctus. Senectus",
        "netus suscipit auctor curabitur facilisi cubilia curae.",
    ],
)

expected_1_section_3 = Section(
    headers=("## header 2", "**header 2.1**"),
    body_lines=[
        "Litora torquent per conubia nostra inceptos himenaeos orci.",
        "Tincidunt nam porta elementum a enim euismod quam. Faucibus",
        "ex sapien vitae pellentesque sem placerat in. Eros lobortis",
        "nulla molestie mattis scelerisque maximus eget. Ullamcorper",
        "rutrum gravida cras eleifend turpis fames primis. Urna",
        "tempor pulvinar vivamus fringilla lacus nec metus. Risus",
        "blandit quis suspendisse aliquet nisi sodales consequat.",
    ],
)

expected_1_section_4 = Section(
    headers=("## header 2", "**header 2.2**"),
    body_lines=[
        "Accumsan maecenas potenti ultricies habitant morbi senectus",
        "netus. Vel class aptent taciti sociosqu ad litora torquent.",
        "Ligula congue sollicitudin erat viverra ac tincidunt nam.",
        "Sit amet consectetur adipiscing elit quisque faucibus ex.",
        "Montes nascetur ridiculus mus donec rhoncus eros lobortis.",
        "Aliquam imperdiet mollis nullam volutpat porttitor ullam",
        "rutrum. Tempus leo eu aenean sed diam urna tempor. Laoreet",
        "mauris pharetra vestibulum fusce dictum risus blandit.",
        "Venenatis ultrices proin libero feugiat tristique accumsan",
        "maecenas. Integer nunc posuere ut hendrerit semper vel class.",
        "Finibus facilisis dapibus etiam interdum tortor ligula congue.",
        "Habitasse platea dictumst lorem ipsum dolor sit amet.",
    ],
)


unsegmented_2 = [
    "Orphan text before the first header starts.",
    "Lorem ipsum dolor sit amet consectetur adipiscing elit.",
    "Quisque faucibus ex sapien vitae pellentesque sem placerat.",
    "## header A",
    "Body text for header A. Purus est efficitur laoreet mauris.",
    "Pharetra vestibulum fusce praesent dui felis venenatis ultrices.",
    "**header A.1**",
    "**header A.2**",
    "Body text for A.2. Proin libero feugiat tristique accumsan.",
    "Maecenas potenti ultricies habitant morbi senectus netus.",
    "## header B",
    "Body text for header B. Nisl malesuada lacinia integer nunc.",
    "Posuere ut hendrerit at luctus nibh finibus facilisis dapibus.",
    "**header B.1**",
]

expected_2_section_1 = Section(
    headers=("", ""),
    body_lines=[
        "Orphan text before the first header starts.",
        "Lorem ipsum dolor sit amet consectetur adipiscing elit.",
        "Quisque faucibus ex sapien vitae pellentesque sem placerat.",
    ],
)

expected_2_section_2 = Section(
    headers=("## header A", ""),
    body_lines=[
        "Body text for header A. Purus est efficitur laoreet mauris.",
        "Pharetra vestibulum fusce praesent dui felis venenatis ultrices.",
    ],
)

expected_2_section_3 = Section(
    headers=("## header A", "**header A.2**"),
    body_lines=[
        "Body text for A.2. Proin libero feugiat tristique accumsan.",
        "Maecenas potenti ultricies habitant morbi senectus netus.",
    ],
)

expected_2_section_4 = Section(
    headers=("## header B", ""),
    body_lines=[
        "Body text for header B. Nisl malesuada lacinia integer nunc.",
        "Posuere ut hendrerit at luctus nibh finibus facilisis dapibus.",
    ],
)

unsegmented_3 = [
    "## Part A: General Obligations",
    "This section outlines the primary compliance requirements for all regulated entities.",
    "Entities must establish robust internal controls to mitigate financial crime risks.",
    "",
    "**Section A.1: Risk Assessment**",
    "A comprehensive business risk assessment must be conducted annually.",
    "",
    "The assessment must document inherent risks and residual risk levels.",
    "## Part A: General Obligations",
    "This section is repeated to verify the Level 1 header is correctly wiped.",
    "**Section A.2: Reporting Requirements**",
    "Suspicious activity reports must be filed within 24 hours of detection.",
    "## Part B: Customer Due Diligence",
    "Enhanced due diligence is required for high-risk customers.",
    "Identification documents must be verified through independent sources.",
]

expected_3_section_1 = Section(
    headers=("## Part A: General Obligations", ""),
    body_lines=[
        "This section outlines the primary compliance requirements for all regulated entities.",
        "Entities must establish robust internal controls to mitigate financial crime risks.",
        "",
    ],
)

expected_3_section_2 = Section(
    headers=("## Part A: General Obligations", "**Section A.1: Risk Assessment**"),
    body_lines=[
        "A comprehensive business risk assessment must be conducted annually.",
        "",
        "The assessment must document inherent risks and residual risk levels.",
    ],
)

expected_3_section_3 = Section(
    headers=("## Part A: General Obligations", ""),
    body_lines=[
        "This section is repeated to verify the Level 1 header is correctly wiped.",
    ],
)

expected_3_section_4 = Section(
    headers=(
        "## Part A: General Obligations",
        "**Section A.2: Reporting Requirements**",
    ),
    body_lines=[
        "Suspicious activity reports must be filed within 24 hours of detection.",
    ],
)

expected_3_section_5 = Section(
    headers=("## Part B: Customer Due Diligence", ""),
    body_lines=[
        "Enhanced due diligence is required for high-risk customers.",
        "Identification documents must be verified through independent sources.",
    ],
)

SEGMENT_BY_HEADERS_TEST_DATA = [
    (
        unsegmented_1,
        [
            expected_1_section_1,
            expected_1_section_2,
            expected_1_section_3,
            expected_1_section_4,
        ],
    ),
    (
        unsegmented_2,
        [
            expected_2_section_1,
            expected_2_section_2,
            expected_2_section_3,
            expected_2_section_4,
        ],
    ),
    (
        unsegmented_3,
        [
            expected_3_section_1,
            expected_3_section_2,
            expected_3_section_3,
            expected_3_section_4,
            expected_3_section_5,
        ],
    ),
]


@pytest.mark.parametrize("unprocessed, expected", SEGMENT_BY_HEADERS_TEST_DATA)
def test_segment_by_headers(
    unprocessed: list[str],
    test_toolbelt: ToolBelt,
    expected: list[Section],
):
    result = segment_by_headers(unprocessed, test_toolbelt.header_matchers)
    assert result == expected
