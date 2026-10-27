from core.sectors import TCSP
from extraction_ops.models import SectionMarkers
from extraction_ops.toolbelts.nra.nra_base import NRA_LANDING_PAGE, build_nra_toolbelt
from extraction_ops.toolbelts.shared_funcs import fixed_sectors, starts_with

# the glossary is the last thing in the document, so its last term ends both
_LAST_LINE = '"WB" World Bank'

_Trimmer = SectionMarkers(
    start=starts_with(["# In this assessment"]),
    end=starts_with([_LAST_LINE]),
)

_Glossary = SectionMarkers(
    start=starts_with(['"AI" Artificial Intelligence']),
    end=starts_with([_LAST_LINE]),
)

TcspNra = build_nra_toolbelt(
    document="Trust and Corporate Service Providers National Risk Assessment (March 2026)",
    short_name="tcsp_nra",
    input_url=NRA_LANDING_PAGE,
    trimmer=_Trimmer,
    sectors=fixed_sectors(TCSP),
    glossary=_Glossary,
)
