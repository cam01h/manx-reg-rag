from extraction_ops.models import SectionMarkers
from extraction_ops.toolbelts.nra.nra_base import NRA_LANDING_PAGE, build_nra_toolbelt
from extraction_ops.toolbelts.nra.nra_sectors import sectoral_chapter_sectors
from extraction_ops.toolbelts.shared_funcs import starts_with

# the glossary is the last thing in the document, so its last term ends both
_LAST_LINE = '"WMD" Weapon of Mass Destruction'

_Trimmer = SectionMarkers(
    start=starts_with(["# In this assessment"]),
    end=starts_with([_LAST_LINE]),
)

_Glossary = SectionMarkers(
    start=starts_with(['"AG" Attorney General']),
    end=starts_with([_LAST_LINE]),
)

TfNra = build_nra_toolbelt(
    document="Terrorist Financing National Risk Assessment (July 2025)",
    short_name="tf_nra",
    input_url=NRA_LANDING_PAGE,
    trimmer=_Trimmer,
    # 6.3 works through each sector in turn
    sectors=sectoral_chapter_sectors(
        r"Step 3: TF Threat & Vulnerability at Sectoral Level"
    ),
    glossary=_Glossary,
)
