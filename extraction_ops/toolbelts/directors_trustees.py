from core.sectors import TCSP
from extraction_ops.models import ChunkSplitters, ToolBelt
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    rejoin_page_breaks,
    replace_from_dict,
    replace_section,
    split_on_paragraph,
    split_on_paragraph_not_list,
    starts_with,
    strip_footnote_bullets,
)

# pymupdf4llm runs words together in the first column ("Privateyacht", "owningcompany")
# and footnote 4 belongs to one cell, so the table is rewritten by hand
_VEHICLE_TABLE_FLAT = """[Editors note: the below is a flattened table]

Type of vehicle - typical level of specialist knowledge required; financial risk to the wider public:

- Public company - knowledge: High; financial risk: High
- Collective investment scheme - not a private arrangement - knowledge: High; financial risk: High
- Closed-ended investment company - not a private arrangement - knowledge: High; financial risk: High
- Private trading company - knowledge: Varies; financial risk: Medium
- Private yacht or aircraft owning company - knowledge: High; financial risk: Low [Footnote: The table concentrates on financial risk. However there are significant risks to public safety if yachts or aircraft are not properly managed. Similar considerations apply to (for example) the safety of factories or buildings.]
- Trust - not a collective investment scheme - knowledge: Medium or High; financial risk: Low
- Private foundation - knowledge: Medium or High; financial risk: Low
- Private asset or property owning company - knowledge: Medium or Low; financial risk: Low

"""

# footnotes are short citations or definitions, so they are moved inline at their marker
_REPLACEMENT_DICT = {
    "regulated activities[1] ;": "regulated activities [Footnote: Financial Services Act 2008, section 2(2)(a)];",
    "reputation of the Island[2] ;": "reputation of the Island [Footnote: Financial Services Act 2008, Schedule 1, paragraph 3(e).];",
    "client vehicles[3] should": 'client vehicles [Footnote: The guidance follows the GIFCS Standard (see page 5) in using the term "vehicles" as a collective term for trusts, companies, foundations and all other forms for the structuring of client business.] should',
    "systems and support[5]": "systems and support [Footnote: See page 1 - effectiveness of management controls, systems and support]",
    "Licensing Policy[6] ,": "Licensing Policy [Footnote: Paragraph 3.1.2],",
    # heading that lost its "##"
    "**Qualitative factors - the relative": "## **Qualitative factors - the relative",
}


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_section(
        text, "|**Type**|", "## **Listed or quoted companies", _VEHICLE_TABLE_FLAT
    )
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    text = strip_footnote_bullets(text)
    # two sentences run over a page break, with the footnotes in between
    text = rejoin_page_breaks(text)
    return text


_Trimmer = build_simple_markers(
    "## **Financial Services Act 2008 Guidance on Directorships",
    "In line with the GIFCS Standard",
)

_Splitters = ChunkSplitters(
    primary=split_on_paragraph_not_list, fallback=split_on_paragraph
)

# client vehicle directorships and trusteeships, including professional officers
DirectorsTrustees = ToolBelt(
    document="Guidance on Directorships, Trusteeships and similar Responsibilities held by Directors and individuals in 'controlled functions'",
    hierarchy="guidance",
    sectors=fixed_sectors(TCSP),
    input_url="https://www.iomfsa.im/media/1582/directorshipsguidancemar2015.pdf",
    pdf_path=build_pdf_path("directors_trustees"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[starts_with(["## **"])],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
