import logging
import re
from collections.abc import Callable
from pathlib import Path
from types import MappingProxyType

from config import MAX_CHUNK_CHAR, TARGET_CHUNK_CHAR
from extraction_ops.models import (
    ChunkSplitters,
    DefinitionTools,
    SectionMarkers,
    ToolBelt,
)
from extraction_ops.toolbelts.nra.nra_cleaning import (
    drop_pull_quotes,
    rejoin_split_paragraphs,
    relevel_headings,
)
from extraction_ops.toolbelts.nra.nra_styles import NRA_STYLE_RULES, StyleRule
from extraction_ops.toolbelts.nra.nra_tables import (
    flatten_tables,
    glossary_to_definitions,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    replace_from_dict,
    split_on_new_sentence,
    split_on_paragraph_not_list,
    split_on_paragraph_or_list_item,
    starts_with,
)

logger = logging.getLogger(__name__)

"""<=== SHARED SET-UP FOR THE NATIONAL RISK ASSESSMENTS ===>"""

# The AML/CFT Code (para 5(3)(b)) requires a business risk assessment to have regard to the
# relevant findings of the most recent NRA, so the NRAs are neither guidance nor merely
# supplemental. See the matching line in system_prompt.md.
NRA_HIERARCHY = "national risk assessment"

# TODO: replace with each NRA's direct PDF link. gov.im blocks automated downloads, so the
# PDFs are committed to data/raw and --get-pdfs cannot fetch these (as with legislation.gov.im)
NRA_LANDING_PAGE = "https://www.gov.im/about-the-government/departments/cabinet-office/national-risk-assessment"


def keep_native_text(page, **kwargs) -> None:
    """An "OCR function" that does nothing.

    In layout mode pymupdf4llm treats an OCR'd page differently: it skips its
    clean_pictures/clean_tables pass. On the NRAs that pass is what breaks tables - every
    table has full-width row shading, clean_pictures grows the table box to cover it, and
    the oversized box is then reclassified as a picture, so the table comes out as <br>
    text. Forcing "OCR" with this no-op takes the OCR'd route without running an OCR
    engine: the PDF's own text is kept, tables survive, and the output no longer depends on
    whether tesseract is installed on the machine."""
    return


NRA_MD_OPTIONS = MappingProxyType(
    {
        "force_ocr": True,
        "ocr_function": keep_native_text,
        # "--- end of page.page_number=N ---" lets the cleaner check each page against fitz
        "page_separators": True,
    }
)

# levels written by relevel_headings: "#" chapter ... "######" run-in heading
NRA_HEADER_MATCHERS: list[Callable[[str], bool]] = [
    starts_with(["# "]),
    starts_with(["## "]),
    starts_with(["### "]),
    starts_with(["#### "]),
    starts_with(["##### "]),
    starts_with(["###### "]),
]


def _split_on_words(text: str, limit: int) -> list[str]:
    pieces: list[str] = []
    current = ""
    for word in text.split(" "):
        if current and len(current) + len(word) + 1 > limit:
            pieces.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        pieces.append(current)
    return pieces


def split_on_paragraph_item_or_sentence(text: str) -> list[str]:
    """Paragraphs and list items; any piece still over the chunk ceiling (a long paragraph,
    a long table row) is cut between sentences, and as a last resort (text read off a
    picture, with no sentence breaks) between words."""
    pieces: list[str] = []
    for piece in split_on_paragraph_or_list_item(text):
        if len(piece) <= MAX_CHUNK_CHAR:
            pieces.append(piece)
            continue
        for sentence in split_on_new_sentence(piece):
            if len(sentence) <= MAX_CHUNK_CHAR:
                pieces.append(sentence)
            else:
                pieces.extend(_split_on_words(sentence, TARGET_CHUNK_CHAR))
    return pieces


NRA_SPLITTERS = ChunkSplitters(
    primary=split_on_paragraph_not_list,
    fallback=split_on_paragraph_item_or_sentence,
)


def is_glossary_line(line: str) -> bool:
    return bool(re.match(r'^"[^"]+" \S', line))


"""<=== MD CLEANERS ===>"""


_PICTURE_TEXT = re.compile(
    r"\*\*----- Start of picture text -----\*\*(?:<br>)?(.*?)\*\*----- End of picture text -----\*\*(?:<br>)?",
    re.DOTALL,
)
_MIN_PROSE_WORDS = 40


def _is_prose(lines: list[str]) -> bool:
    words = " ".join(lines).split()
    long_lines = [line for line in lines if len(line) >= 40]
    return len(words) >= _MIN_PROSE_WORDS and len(long_lines) >= len(lines) / 2


def keep_prose_pictures(text: str) -> str:
    """pymupdf4llm reads text off anything it classes as a picture. For charts and diagrams
    that is axis labels and figures - dropped. But some large text tables (eg a "summary of
    key vulnerabilities") are classed as pictures too, and their text is the content - kept,
    with sentences re-flowed into paragraphs."""

    def repl(match: re.Match) -> str:
        lines = [line.strip() for line in match.group(1).split("<br>") if line.strip()]
        if not _is_prose(lines):
            return ""
        flowed = re.sub(r"(?<=[.:;])\n", "\n\n", "\n".join(lines))
        return "\n\n" + re.sub(r"(?<!\n)\n(?!\n)", " ", flowed) + "\n\n"

    text = re.sub(r"\*\*==> picture.*?intentionally omitted <==\*\*", "", text)
    return _PICTURE_TEXT.sub(repl, text)


# "**12** text", "> **1** text" or, on some pages, a list item "- **53** text"
_FOOTNOTE_LINE = re.compile(
    r"^(?:>|[ \t]*-)?[ \t]*\*\*\d{1,3}\*\*[ \t]+\S.*$", re.MULTILINE
)
_FOOTNOTE_ITEM = re.compile(
    r"\*\*(\d{1,3})\*\*[ \t]*(.*?)(?=\s*\*\*\d{1,3}\*\*|\Z)", re.DOTALL
)
_MIN_NOTE_CHARS = 80


def footnotes_to_notes(text: str) -> str:
    """Footnotes arrive as a line at the foot of the page: "**12** In today's digital age...",
    sometimes several on one line. Citations (a link, a short reference) are dropped;
    footnotes with substance are kept as their own "Note 12: ..." paragraph."""

    def repl(match: re.Match) -> str:
        notes = []
        for number, body in _FOOTNOTE_ITEM.findall(match.group().lstrip("> -\t")):
            body = body.strip()
            if len(body) < _MIN_NOTE_CHARS or re.search(r"https?://|www\.", body):
                continue
            notes.append(f"Note {number}: {body}")
        return "\n\n".join(notes)

    text = _FOOTNOTE_LINE.sub(repl, text)
    # markers left in the text: "[14]", "[ 17 ]", "[.86]"
    return re.sub(r" ?\[\s*\.?\d{1,3}\s*\]", "", text)


def strip_glyphs(text: str) -> str:
    text = text.replace("\x07", "").replace("­", "")
    # page-turn arrows at the end of a column, sometimes rendered as ">"
    text = re.sub(r"[ \t]*[›»▶➤][ \t]*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"(?<=\S)[ \t]+>[ \t]*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>[ \t]*$\n?", "", text, flags=re.MULTILINE)
    text = text.replace("›", "")
    # bullets that came through as characters rather than md list items
    text = re.sub(r"^[ \t]*[●○■•◦][ \t]*", "- ", text, flags=re.MULTILINE)
    # numbered paragraphs that pymupdf4llm made list items: "- 2.1   The Isle of Man..."
    text = re.sub(r"^- (\d+\.\d+)[ \t]+", r"\1 ", text, flags=re.MULTILINE)
    return re.sub(r"[ \t]{2,}", " ", text)


def tidy_blank_lines(text: str) -> str:
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def build_nra_cleaner(
    pdf_path: Path,
    rules: list[StyleRule] = NRA_STYLE_RULES,
    replacements: dict[str, str] | None = None,
    extra: Callable[[str], str] | None = None,
) -> Callable[[str], str]:
    def clean(text: str) -> str:
        text = keep_prose_pictures(text)
        if replacements:
            text = replace_from_dict(text, replacements)
        text = relevel_headings(text, pdf_path, rules)
        text = drop_pull_quotes(text, pdf_path, rules)
        text = footnotes_to_notes(text)
        text = strip_glyphs(text)
        text = rejoin_split_paragraphs(text, pdf_path)
        text = glossary_to_definitions(text)
        text = flatten_tables(text)
        text = base_text_cleaner(text)
        if extra is not None:
            text = extra(text)
        return tidy_blank_lines(text)

    return clean


"""<=== TOOLBELT FACTORY ===>"""


def build_nra_toolbelt(
    *,
    document: str,
    short_name: str,
    input_url: str,
    trimmer: SectionMarkers,
    sectors: Callable[[tuple[str, ...]], tuple[str, ...]],
    glossary: SectionMarkers | None,
    rules: list[StyleRule] = NRA_STYLE_RULES,
    replacements: dict[str, str] | None = None,
    extra_cleaner: Callable[[str], str] | None = None,
) -> ToolBelt:
    pdf_path = build_pdf_path(short_name)
    definition_tools = (
        DefinitionTools(section_markers=[glossary], is_definition_line=is_glossary_line)
        if glossary is not None
        else None
    )
    return ToolBelt(
        document=document,
        hierarchy=NRA_HIERARCHY,
        sectors=sectors,
        input_url=input_url,
        pdf_path=pdf_path,
        trimmer=trimmer,
        header_matchers=NRA_HEADER_MATCHERS,
        clean_text=build_nra_cleaner(pdf_path, rules, replacements, extra_cleaner),
        re_pack_splitters=NRA_SPLITTERS,
        use_ocr=True,
        use_layout=True,
        md_options=NRA_MD_OPTIONS,
        definition_tools=definition_tools,
    )
