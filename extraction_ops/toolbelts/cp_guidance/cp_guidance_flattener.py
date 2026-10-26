import re

from extraction_ops.toolbelts.shared_funcs import replace_section

# the appendices are tables. pymupdf4llm splits the long cells and the 30% columns, so each
# table is rewritten by hand from the PDF; the wording in each row is the Authority's

_STAGES_FLAT = """[Editors note: the below is a flattened diagram]

- Stage One - Identification: Identify and investigate a serious regulatory failing
- Stage Two - Determination: Determine whether a civil penalty is the most appropriate regulatory action
- Stage Three - Calculation: Identify the Penalty Level; Ascertain the relevant income; Consider additional factors
- Stage Four - Implementation: Penalty notice and payment; Publication on website; Ongoing monitoring

"""

_APPENDIX_A_FLAT = """## **Appendix A - Key Factors for Consideration**

[Editors note: the below is a flattened table]

- Seriousness: The overall seriousness of the regulatory failing.
- Customer loss: The nature, extent and impact of any significant loss to customers (or a risk of such loss) as a result of the regulatory failing.
- Financial crime: Whether the regulatory failing resulted in financial crime (or a significant risk of such crime).
- Reputation: The nature, extent and impact of any damage to the reputation of the Isle of Man and its status as an international financial centre as a result of the regulatory failing.
- Affordability: The potential financial consequences to the regulated entity and to any third parties (including customers and creditors of the regulated entity) of imposing a discretionary civil penalty.
- Fitness and propriety: Matters of fitness and propriety relating to Key Persons and other staff of a regulated entity, for example - (a) is there evidence of negligent or reckless behaviour? (b) is there evidence that the regulated entity was aware a breach would result from the action taken? (c) has there been a deliberate attempt to conceal a breach or withhold pertinent information from the Authority (e.g. information that shows the true seriousness of the regulatory failing)?
- Fundamental failings: The nature, extent and impact of any weaknesses in - (a) the regulated entity's corporate governance (if applicable); (b) the regulated entity's systems or internal controls; or (c) the fitness and propriety of any of the regulated entity's directors, controllers or Key Persons, Such failings may relate to all or part of the business and result in multiple breaches of legislation.
- Improper gain: The nature, extent and impact of any benefit obtained (or loss mitigated) as a result of the regulatory failing.
- Breaches of legislation: The nature, extent and impact of any breaches of primary and secondary legislation incurred as a result of the regulatory failing.
- Identification: The length of time between occurrence of the regulatory failing (if possible to discern) and its identification by the regulated entity or the Authority.
- Notification: The length of time the regulated entity was aware of the regulatory failing prior to notifying the Authority and the circumstances surrounding notification.
- Remediation: The extent to which the regulated entity has attempted to address the regulatory failing and the efficiency of any remedial action taken.
- Compliance record: Whether the regulatory failing (or a similar failing) has occurred previously.
- Other cases: Discretionary civil penalties imposed by the Authority in other cases.

"""

_APPENDIX_B_FLAT = """## **Appendix B - Discretionary Civil Penalty Levels**

[Editors note: the below is a flattened table]

- Level 1 (Up to 5% of relevant income): A penalty may be imposed at this level in cases where there has been a serious regulatory failing where any of the following factors are present but none of the factors in Level 2 are present - (a) the serious regulatory failing has resulted in a risk of significant loss to any of the regulated entity's customers; (b) the serious regulatory failing has resulted in a significant risk of financial crime; or (c) the serious regulatory failing is attributable to serious negligence by any of the regulated entity's directors, controllers or key persons.
- Level 2 (Up to 8% of relevant income): A penalty may be imposed at this level in cases where there has been a serious regulatory failing where any of the following factors are present - (a) the serious regulatory failing has resulted in a significant loss to any of the regulated entity's customers; (b) the serious regulatory failing has resulted in financial crime; (c) the serious regulatory failing was incurred deliberately by any of the regulated entity's directors, controllers or key persons in order to obtain a benefit or mitigate a loss; (d) any of the regulated entity's directors, controllers or key persons have attempted to conceal the serious regulatory failing from the Authority; or (e) the serious regulatory failing is attributable to serious deficiencies in any of - (i) the regulated entity's corporate governance (if applicable); (ii) the regulated entity's systems and internal controls; or (iii) the fitness and propriety of any of the regulated entity's directors, controllers or key persons.

"""

_APPENDIX_C_FLAT = """## **Appendix C - Aggravating and Mitigating Factors**

[Editors note: the below is a flattened table]

- Nature, extent and impact of the regulatory failing - aggravating: Significant damage to the reputation of the Isle of Man (or a risk of such damage); mitigating: Little or no damage to the reputation of the Isle of Man (or little risk of such damage)
- Nature, extent and impact of the regulatory failing - aggravating: The results of the failing are persistent or long-lived; mitigating: The results of the failing are isolated or short-lived
- Nature, extent and impact of the regulatory failing - aggravating: Increased risk of the financial failure of the regulated entity; mitigating: Little or no risk of the financial failure of the regulated entity
- Financial crime - aggravating: Increased risk of financial crime such as money laundering or terrorist financing; mitigating: Little or no risk of financial crime such as money laundering or terrorist financing
- Customers - aggravating: Adverse impact upon customers (e.g. significant loss or a risk of such loss); mitigating: Little or no adverse impact upon customers (e.g. no significant loss or no risk of such loss)
- Fitness and propriety - aggravating: The failing has been incurred deliberately, negligently or recklessly; mitigating: The failing is inadvertent or a result of genuine error
- Fitness and propriety - aggravating: The failing was within the regulated entity's control (possibly senior staff involved); mitigating: The failing was wholly or partly outside the regulated entity's control
- Competency - aggravating: Indications of lack of competence in the handling of the situation; mitigating: Indications that the situation has been handled competently
- Competency - aggravating: The failing was not identified by the regulated entity in the first instance (e.g. it was identified by the Authority or an auditor etc.); mitigating: The failing was identified by the regulated entity in the first instance (e.g. not by the Authority or an auditor etc.)
- Competency - aggravating: Slow and/or inadequate remedial action; mitigating: Prompt and/or effective remedial action
- Fundamental issues - aggravating: Lack of, or inadequate procedures or controls (e.g. other similar matters have been handled inappropriately); mitigating: Generally adequate procedures and controls (e.g. other similar matters have been handled appropriately)
- Fundamental issues - aggravating: The serious regulatory failing has recurred (e.g. repetition of the same breach) or has remained unaddressed or uncorrected once the regulated entity became aware of it; mitigating: The serious regulatory failing is an isolated incident and has been addressed and corrected once the regulated entity became aware of it
- Fundamental issues - aggravating: Numerous breaches of different types which could indicate fundamentally weak controls or poor compliance; mitigating: Breaches of specific regulatory requirements only but with otherwise good compliance

"""

_APPENDIX_D_FLAT = """## **Appendix D - Sample Calculations**

[Editors note: the below is a flattened table]

- Relevant income £1,000,000,000: Level 1 maximum penalty (5% RI) £50,000,000, reduced by 30% £15,000,000; Level 2 maximum penalty (8% RI) £80,000,000, reduced by 30% £56,000,000
- Relevant income £500,000,000: Level 1 maximum penalty (5% RI) £25,000,000, reduced by 30% £17,500,000; Level 2 maximum penalty (8% RI) £40,000,000, reduced by 30% £28,000,000
- Relevant income £100,000,000: Level 1 maximum penalty (5% RI) £5,000,000, reduced by 30% £3,500,000; Level 2 maximum penalty (8% RI) £8,000,000, reduced by 30% £5,600,000
- Relevant income £25,000,000: Level 1 maximum penalty (5% RI) £1,250,000, reduced by 30% £875,000; Level 2 maximum penalty (8% RI) £2,000,000, reduced by 30% £1,400,000
- Relevant income £10,000,000: Level 1 maximum penalty (5% RI) £500,000, reduced by 30% £350,000; Level 2 maximum penalty (8% RI) £800,000, reduced by 30% £560,000
- Relevant income £5,000,000: Level 1 maximum penalty (5% RI) £250,000, reduced by 30% £175,000; Level 2 maximum penalty (8% RI) £400,000, reduced by 30% £280,000
- Relevant income £1,000,000: Level 1 maximum penalty (5% RI) £50,000, reduced by 30% £35,000; Level 2 maximum penalty (8% RI) £80,000, reduced by 30% £56,000
- Relevant income £750,000: Level 1 maximum penalty (5% RI) £37,500, reduced by 30% £26,250; Level 2 maximum penalty (8% RI) £60,000, reduced by 30% £42,000
- Relevant income £500,000: Level 1 maximum penalty (5% RI) £25,000, reduced by 30% £17,500; Level 2 maximum penalty (8% RI) £40,000, reduced by 30% £28,000
- Relevant income £250,000: Level 1 maximum penalty (5% RI) £12,500, reduced by 30% £8,750; Level 2 maximum penalty (8% RI) £20,000, reduced by 30% £14,000
- Relevant income £100,000: Level 1 maximum penalty (5% RI) £5,000, reduced by 30% £3,500; Level 2 maximum penalty (8% RI) £8,000, reduced by 30% £5,600
- Relevant income £50,000: Level 1 maximum penalty (5% RI) £2,500, reduced by 30% £1,750; Level 2 maximum penalty (8% RI) £4,000, reduced by 30% £2,800
- Relevant income £10,000: Level 1 maximum penalty (5% RI) £500, reduced by 30% £350; Level 2 maximum penalty (8% RI) £800, reduced by 30% £560

[Editors note: the first row is as printed in the source. 30% off £50,000,000 is £35,000,000, so £15,000,000 appears to be a typo in the original table.]

"""

_APPENDIX_E_TABLE_FLAT = """[Editors note: the below is a flattened table]

- Competence: The quality of being competent; adequacy; possession of required skill, knowledge, qualification, or capacity
- Deliberate: Done consciously and intentionally
- Inadvertent: Not resulting from or achieved through deliberate planning; unintentional; (of a mistake) made through lack of care; negligent
- Isolated: Separated from other persons or things; alone; solitary
- Negligent: Guilty of or characterised by neglect, as of duty; i.e. - (a) to pay no attention or too little attention to; disregard or slight; (b) to be remiss in the care or treatment of; (c) to omit, through indifference or carelessness; (d) to fail to carry out or perform (orders, duties, etc…); (e) to fail to take or use
- Persistent: Persisting, especially in spite of opposition, obstacles, discouragement, etc.; persevering; lasting or enduring tenaciously; constantly repeated; continued
- Reckless: (Of a person or their actions) Without thinking or caring about the consequences of an action
- Significant: Important; of consequence; having or expressing a meaning; indicative; suggestive; (statistics) of or relating to observations that are unlikely to occur by chance and that therefore indicate a systematic cause
- Uncorrected: Left faulty or wrong
"""


def flatten_staged_approach(text: str) -> str:
    return replace_section(
        text,
        "**==> picture [434 x 254] intentionally omitted <==**",
        "## **3.1 Stage One",
        _STAGES_FLAT,
    )


def flatten_appendices(text: str) -> str:
    text = replace_section(text, "## **Appendix A", "## **Appendix B", _APPENDIX_A_FLAT)
    text = replace_section(text, "## **Appendix B", "## **Appendix C", _APPENDIX_B_FLAT)
    text = replace_section(text, "## **Appendix C", "## **Appendix D", _APPENDIX_C_FLAT)
    text = replace_section(text, "## **Appendix D", "## **Appendix E", _APPENDIX_D_FLAT)
    # Appendix E keeps its two intro paragraphs, only the table is replaced
    table_start = text.find("|Concept|Common Definition|")
    if table_start == -1:
        raise ValueError("Appendix E table not found")
    return text[:table_start] + _APPENDIX_E_TABLE_FLAT


# "|**Regulation**|**Name**|**Civil penalties for**|**Calculation Method**|" tables, one row
# per regime. Rows become "- Regulation 5 - Discretionary Regime: ..."
_REGIME_TABLE = re.compile(
    r"^\|\*\*Regulation\*\*\|.*\n\|---\|.*\n((?:\|.*\|[ \t]*\n?)+)", re.MULTILINE
)


def _regime_row(line: str) -> str:
    cells = [
        re.sub(r"\s+", " ", c.replace("<br>", " ").replace("**", "")).strip()
        for c in line.strip()[1:-1].split("|")
    ]
    regulation, name, penalties_for, method = cells
    return f"- {regulation} - {name}: civil penalties for {penalties_for.lower()}; calculation method: {method.lower()}"


def flatten_regime_tables(text: str) -> str:
    def inner(match: re.Match[str]) -> str:
        rows = [
            _regime_row(line) for line in match.group(1).splitlines() if line.strip()
        ]
        return (
            "[Editors note: the below is a flattened table]\n\n"
            + "\n".join(rows)
            + "\n"
        )

    return _REGIME_TABLE.sub(inner, text)
