from core.sectors import CLASS_1
from extraction_ops.models import SectionMarkers
from extraction_ops.toolbelts.nra.nra_base import build_nra_toolbelt
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

BankingNra = build_nra_toolbelt(
    document="Banking Sector National Risk Assessment (October 2025)",
    short_name="banking_nra",
    input_url="https://counteringfinancialcrime.im/media/jnbn3y1j/banking-sector-nra.pdf",
    trimmer=_Trimmer,
    sectors=fixed_sectors((CLASS_1,)),
    glossary=_Glossary,
)
