import re
from collections.abc import Callable

"""<=== SHARED SET-UP FOR THE FIU PUBLICATIONS ===>"""

# TODO: replace with each document's direct PDF link. The PDFs are committed to data/raw,
# so --get-pdfs is not needed for these
FIU_LANDING_PAGE = "https://www.fiu.im/"

# The SAR guidance, consent FAQs and sanctions reporting guidance tell a reporter how to use
# the reporting regime - guidance. The typology reports illustrate risks with fictitious
# cases and red flags - supplemental.
FIU_GUIDANCE = "guidance"
FIU_SUPPLEMENTAL = "supplemental"


def drop_picture_markers(text: str) -> str:
    # "**==> picture [117 x 35] intentionally omitted <==**" - logos and page furniture
    return re.sub(
        r"^\*\*==> picture .*?<==\*\*[ \t]*$\n?", "", text, flags=re.MULTILINE
    )


def drop_empty_bullets(text: str) -> str:
    # list markers left behind when the item text was read elsewhere on the page
    text = re.sub(r"^[ \t]*-[ \t]*$\n?", "", text, flags=re.MULTILINE)
    # items pymupdf4llm indented as a nested list although they are not
    return re.sub(r"^[ \t]+- ", "- ", text, flags=re.MULTILINE)


def strip_footnote_numbers(text: str) -> str:
    # "Crime Act 2008[1] (POCA)", "NRA[5]", "RUSI.[6,7]", "security mechanisms.[41 ]",
    # "billion annually **[2]**"
    return re.sub(r" ?(\*\*)?\[\s*\d{1,2}(?:\s*,\s*\d{1,2})*\s*\](?(1)\*\*)", "", text)


def close_punctuation_gaps(text: str) -> str:
    # "**Themis** ," and "the Isle of Man ." - a space left before punctuation where a bold
    # run or a line of text ends
    return re.sub(r"(?<=[\w)*]) +([.,;:])(?=[\s*]|$)", r"\1", text)


def collapse_heading_spaces(text: str) -> str:
    # "## **1.3    Information Required - SARs**"
    return re.sub(r"^(#{1,6} \*\*\S+)[ \t]{2,}", r"\1 ", text, flags=re.MULTILINE)


def numbered_heading(depth: int) -> Callable[[str], bool]:
    """'## **3. Consent'' is depth 1, '## **3.3 The Notice' depth 2, '## **3.3.1 Notice'
    depth 3"""
    pattern = re.compile(r"^## \*\*\d+" + r"\.\d+" * (depth - 1) + r"\.?\s")

    def inner(line: str) -> bool:
        return bool(pattern.match(line))

    return inner


def demote_unnumbered_headings(text: str) -> str:
    """Bold run-in labels ("POCA", "As soon as practicable:", the shaded "Example" boxes)
    come through as headings. They belong to the numbered section they sit in."""

    def repl(match: re.Match) -> str:
        label = match.group(1).strip()
        example = re.match(r"^(?:[-–]\s*)?Example\s*[-–]?\s*(.*)$", label)
        if example:
            return f"**Example - {example.group(1).strip()}:**"
        return f"**{label}**"

    return re.sub(r"^## \*\*(?!\d)(.*?)\*\*[ \t]*$", repl, text, flags=re.MULTILINE)
