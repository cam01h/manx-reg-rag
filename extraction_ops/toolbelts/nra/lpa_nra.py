from core.sectors import ALL_SECTORS
from extraction_ops.models import SectionMarkers
from extraction_ops.toolbelts.nra.nra_base import NRA_LANDING_PAGE, build_nra_toolbelt
from extraction_ops.toolbelts.shared_funcs import fixed_sectors, starts_with

# Endnotes (citations) end the document, after appendix 10 (glossary)
_Trimmer = SectionMarkers(
    start=starts_with(["# In this assessment"]),
    end=starts_with(["### Endnotes"]),
)

_Glossary = SectionMarkers(
    start=starts_with(['"ACSP" Association of Corporate Service Providers']),
    end=starts_with(['"WB" World Bank']),
)

# every firm carries out CDD on legal persons and arrangements, so no sector narrowing
LpaNra = build_nra_toolbelt(
    document="Legal Persons and Arrangements National Risk Assessment (April 2026)",
    short_name="lpa_nra",
    input_url=NRA_LANDING_PAGE,
    trimmer=_Trimmer,
    sectors=fixed_sectors(ALL_SECTORS),
    glossary=_Glossary,
)
