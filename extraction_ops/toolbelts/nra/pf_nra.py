from extraction_ops.models import SectionMarkers
from extraction_ops.toolbelts.nra.nra_base import NRA_LANDING_PAGE, build_nra_toolbelt
from extraction_ops.toolbelts.nra.nra_sectors import sectoral_chapter_sectors
from extraction_ops.toolbelts.shared_funcs import starts_with

# appendices 2 and 3 follow the glossary; the endnotes (citations) close the document
_Trimmer = SectionMarkers(
    start=starts_with(["# In this assessment"]),
    end=starts_with(["# 4. Endnotes"]),
)

_Glossary = SectionMarkers(
    start=starts_with(['"AECs" Anonymity Enhancing Cryptocurrencies']),
    end=starts_with(['"WMD" Weapons of Mass Destruction']),
)

PfNra = build_nra_toolbelt(
    document="Proliferation Financing National Risk Assessment (July 2026)",
    short_name="pf_nra",
    input_url=NRA_LANDING_PAGE,
    trimmer=_Trimmer,
    # chapter 6 works through each sector in turn
    sectors=sectoral_chapter_sectors(r"Sectoral Analysis"),
    glossary=_Glossary,
)
