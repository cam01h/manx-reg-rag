from core.sectors import VASP
from extraction_ops.models import SectionMarkers
from extraction_ops.toolbelts.nra.nra_base import NRA_LANDING_PAGE, build_nra_toolbelt
from extraction_ops.toolbelts.shared_funcs import fixed_sectors, starts_with

# Endnotes (citations) end the document, after the abbreviations appendix
_Trimmer = SectionMarkers(
    start=starts_with(["# In this Assessment"]),
    end=starts_with(["# Endnotes"]),
)

_Glossary = SectionMarkers(
    start=starts_with(['"AGC" Attorney General']),
    end=starts_with(['"VISTA" Virgin Islands Special Trusts Act']),
)

VaspNra = build_nra_toolbelt(
    document="Virtual Assets and Virtual Asset Service Providers National Risk Assessment (April 2026)",
    short_name="vasp_nra",
    input_url=NRA_LANDING_PAGE,
    trimmer=_Trimmer,
    sectors=fixed_sectors((VASP,)),
    glossary=_Glossary,
)
