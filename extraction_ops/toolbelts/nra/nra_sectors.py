import re
from collections.abc import Callable

from core.sectors import (
    ALL_SECTORS,
    CLASS_1,
    CLASS_2,
    CLASS_3,
    CLASS_6,
    CLASS_7,
    CLASS_8,
    CLASS_9,
    ESTATE_AGENT,
    EXTERNAL_ACCOUNTANT,
    HIGH_VALUE_DEALER,
    IA08_FIRMS,
    LEGAL_PROFESSIONAL,
    LENDER,
    LIFE_CO,
    NON_LIFE_CO,
    PAYROLL_AGENT,
    SAFE_CUSTODY,
    TAX_ADVISER,
    TCSP,
    VASP,
)

"""<=== SECTORS FROM SECTOR-NAMED HEADINGS ===>"""

# The ML, TF and PF NRAs each have a chapter that works through the sectors one by one.
# Inside that chapter a chunk takes the sectors named by its headings; everywhere else (and
# for sectors with no registry entry - gambling, NPOs, pensions) it applies to everyone.
# Matches across all of a chunk's headings are combined rather than the deepest winning:
# a banking sub-section titled "TCSP Managed" is relevant to both, and a chunk tagged too
# widely is only noise, where one tagged too narrowly is silently hidden from a firm.

# checked in order, all matches kept. "non-life" must be tested before "life"
SECTOR_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    (r"\bnon[- ]life\b|\bgeneral insurance|\bcaptive", (NON_LIFE_CO,)),
    (r"(?<!non-)(?<!non )\blife\b", (LIFE_CO,)),
    (r"\binsurance (?:manager|intermediar)", IA08_FIRMS),
    (r"\bbank", (CLASS_1,)),
    (r"\bdeposit[- ]taking", (CLASS_1,)),
    (r"\bcredit union", (CLASS_9,)),
    (r"\binvestment business|\bfinancial advis", (CLASS_2,)),
    (
        r"\bcollective investment|\bfunds? (?:sector|administrat)|\bservices to (?:cis|collective)",
        (CLASS_3,),
    ),
    (r"\bcrowdfunding", (CLASS_6,)),
    (r"\bmanagement or administration", (CLASS_7,)),
    (
        r"\bmoney (?:transmission|service)|\bmsbs?\b|\bmts\b|\bbureau|\be-?money|\bpayment service",
        (CLASS_8,),
    ),
    (
        r"\btcsps?\b|\btrust and corporate|\bcorporate service provider|\btrust service",
        TCSP,
    ),
    (
        r"\baccountan|\btax advis|\bpayroll",
        (EXTERNAL_ACCOUNTANT, TAX_ADVISER, PAYROLL_AGENT),
    ),
    (r"\bestate agen", (ESTATE_AGENT,)),
    (
        r"\blegal (?:services|professional|sector)|\badvocates?\b|\blawyers?\b",
        (LEGAL_PROFESSIONAL,),
    ),
    (r"\bmoneylend|\blending\b", (LENDER,)),
    (r"\bhigh[- ]value (?:goods|dealer)|\bhvgd|\bhvds?\b", (HIGH_VALUE_DEALER,)),
    (r"\bsafe custody", (SAFE_CUSTODY,)),
    (r"\bvirtual asset|\bvasps?\b", (VASP,)),
]


def headings_sectors(headers: tuple[str, ...]) -> set[str]:
    found: set[str] = set()
    for header in headers:
        for pattern, sectors in SECTOR_PATTERNS:
            if re.search(pattern, header, re.IGNORECASE):
                found.update(sectors)
    return found


def sectoral_chapter_sectors(
    chapter: str, fallback: tuple[str, ...] = ALL_SECTORS
) -> Callable[[tuple[str, ...]], tuple[str, ...]]:
    """Sectors from the headings of chunks under the heading matching `chapter` (regex,
    searched at any level); the fallback for everything else."""

    def inner(headers: tuple[str, ...]) -> tuple[str, ...]:
        in_chapter = [
            i
            for i, h in enumerate(headers)
            if h and re.search(chapter, h, re.IGNORECASE)
        ]
        if not in_chapter:
            return fallback
        below = tuple(h for h in headers[in_chapter[0] + 1 :] if h)
        found = headings_sectors(below)
        if not found:
            return fallback
        return tuple(s for s in ALL_SECTORS if s in found)

    return inner
