from extraction_ops.models import SectionMarkers
from extraction_ops.toolbelts.nra.nra_base import build_nra_toolbelt
from extraction_ops.toolbelts.nra.nra_sectors import sectoral_chapter_sectors
from extraction_ops.toolbelts.shared_funcs import starts_with

# Endnotes (citations) end the document, after the glossary
_Trimmer = SectionMarkers(
    start=starts_with(["# In this assessment"]),
    end=starts_with(["# Endnotes"]),
)

_Glossary = SectionMarkers(
    start=starts_with(['"ABC" Anti-Bribery and Corruption Strategy']),
    end=starts_with(['"WB" World Bank']),
)

MlNra = build_nra_toolbelt(
    document="Money Laundering National Risk Assessment (March 2026)",
    short_name="ml_nra",
    input_url="https://counteringfinancialcrime.im/media/a2fnlfi0/money-laundering-nra-march26v3.pdf",
    trimmer=_Trimmer,
    # chapter 12 works through each sector in turn
    sectors=sectoral_chapter_sectors(r"ML Threat & Vulnerability at Sectoral Level"),
    glossary=_Glossary,
)
