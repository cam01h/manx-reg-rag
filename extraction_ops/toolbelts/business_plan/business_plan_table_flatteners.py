from extraction_ops.toolbelts.shared_funcs import replace_section

_TABLE_2P2_FLAT = """

[Editors note: the below is a flattened table]

A summary of the proposed key control functions, including the following for each function as indicated (internal audit, compliance and risk management):

- Structure of the function including reporting lines: all three functions.
- Overview of personnel including relevant experience and qualifications for the role: all three functions.
- Role, objectives and key activities of the function: all three functions.
- Overview of the policy/procedures of the function for reporting to the board, including expected frequency: all three functions.
- Expected frequency of performance of work: internal audit only.
- Details of whether the function is independent from the operational activities of the applicant: internal audit only.
"""


def flatten_2p2_table(text: str) -> str:
    return replace_section(
        text,
        "- A summary of the proposed key control",
        "\n- Details of the proposed relationship between",
        _TABLE_2P2_FLAT,
    )


_TABLE_3P1_FLAT = """Supporting documentation checklist - documents to be included within, or enclosed with, the business plan.

[Editors note: the below is a flattened table]

All FSA08 applicants:
- (section 2.1) Where applicant is part of a group - detailed group structure chart
- (section 2.1) Where applicant is part of a group - copy of latest available audited accounts for the group and funding company(ies) (if not publicly available)
- (section 2.2) Proposed staff organisational structure chart
- (section 2.2) Where applicant intends to use a locum - copy of draft agreement
- (section 2.3) Where applicant proposes material outsourcing arrangement(s) - copy of draft agreement(s) and outsourcing function flow chart(s)
- (section 2.4) Summary of projected profit and loss account, balance sheet and cash flow forecasts with detailed supporting financial projection calculations
- (section 2.4) Where applicant is an established company - copy of applicant's accounts
- (section 2.4) Statement(s) of financial resources

FSA08 applicants with material outsourcing:
- (section 2.3) Copy of the Outsourcing Agreement
- (section 2.3) Where applicable, outsourced function flow chart(s)
- (section 2.3) Copy of any Service Level Agreement
- (section 2.3) Copy of any Management Agreement
- (section 2.4) Copy of the group PII policy
- (section 2.4) Copy of the Letter of Comfort wording where supporting the PII
"""


def flatten_3p1_table(text: str) -> str:
    return replace_section(
        text,
        "Has the following supporting documentation",
        "\nIf any of the above documentation has",
        _TABLE_3P1_FLAT,
    )


_TABLE_3P2_FLAT = """Supporting documentation checklist (IA08 applicants) - documents to be included within, or enclosed with, the business plan.

[Editors note: the below is a flattened table]

All IA08 applicants:
- (section 2.1) Where applicant is part of a group - detailed group structure chart
- (section 2.1) Where the applicant is part of a group - copy of latest available audited accounts for the group and funding company(ies) (if not publicly available)
- (section 2.2) Proposed staff organisational structure chart
- (section 2.3) Where applicant proposes material outsourcing arrangement(s), which is not insurance management (see Appendix 3(iii)) - copy of draft agreement(s) and outsourcing function flow chart(s)
- (section 2.4) Summary of projected profit and loss account, balance sheet and cash flow forecasts with detailed supporting financial projection calculations
- (section 2.4) Underlying supporting claims data
- (Appendix 3(iv)) Schematic diagram of the insurance program(s)
- (Appendix 3(v)) Year 1 realistic scenario SCR form and supporting helper templates

IA08 partially managed applicants only:
- (Appendix 3(iii)) Copy of the proposed insurance management agreement

IA08 Class 12 applicants only:
- (Appendix 3(i)) Class 12 requirements compliance

IA08 non-Class 12 applicants only:
- (Appendix 3(ii)) Copy of the written management policy for underwriting risk
- (Appendix 3(ii)) Copy of the written management policy for reserving (provisions) risk
- (Appendix 3(ii)) Copy of the written management policy for asset liability management
- (Appendix 3(ii)) Copy of the written management policy for investment risk
- (Appendix 3(ii)) Copy of the written management policy for liquidity risk
- (Appendix 3(ii)) Copy of the written management policy for concentration risk
- (Appendix 3(ii)) Copy of the written management policy for operational risk
- (Appendix 3(ii)) Copy of the written management policy for reinsurance and other risk-mitigation techniques
- (Appendix 3(ii)) Written capital management policy
- (Appendix 3(v)) Year 1 pessimistic scenario SCR form and supporting helper templates

Where any of the above documentation is marked as N/A, the applicant must provide a further explanation, including a reference to the relevant section.
"""


def flatten_3p2_table(text: str) -> str:
    return replace_section(
        text,
        "Has the following supporting documentation",
        "\n## **Appendix 1:  Example Financial",
        _TABLE_3P2_FLAT,
    )


_APPENDIX_1_FLATTENED = """## Appendix 1: Example Financial Summary Tables

These are example formats for the financial summaries required in section 2.4 (applicants may present the information in tabular or text format).

## **(i) Group financial information**
[Editors note: the below is a flattened table]
For each group company: financial period ended, total revenue, profit for the period, total assets and shareholder funds (each in stated currency).

## **(ii) FSA08 financial resources statement**
[Editors note: the below is a flattened table]
See rule 2.30 (Appendix 3 of the Rule Book) for the financial resource requirements for regulated entities. A spreadsheet to assist with producing the statement of financial resources is available on the Authority's website, in the section on "Quarterly Financial Returns and Calculations".

## **(iii) IA08 non long-term applicant forecast financial information**
[Editors note: the below is a flattened table]
Presented for each year of the 3-year forecast period:
- Income statement: premiums written, reinsurance premium written, change in unearned premium reserve (UPR) and reinsurance UPR, giving net premium earned; claims paid, movements in claims reserves, unexpired risk reserve (URR) and incurred but not reported (IBNR) reserve, reinsurance recovered and movement in reinsurance recoverable, giving net claims; reinsurance broking fees and change in deferred broking fees; underwriting profit/(loss); investment income; expenses; profit/(loss) for the period; dividends.
- Balance sheet: assets (bank balances and cash, intercompany loan, unearned reinsurance premium reserve, deferred reinsurance broking costs, recoverable from reinsurers, prepaid expenses, total assets); general business insurance provisions (UPR, claims reserves, URR); other liabilities (accrued expenses); net assets; represented by share capital, share premium and retained earnings, giving total shareholder's funds.
- Solvency Capital Requirement (SCR): absolute own funds, SCR figure, shareholder's funds, solvency surplus/(deficit) and solvency ratio.

## **(iv) IA08 long-term applicant forecast financial information**
[Editors note: the below is a flattened table]
Presented for each year of the 5-year forecast period:
- Revenue account: written premiums, fee income, investment income, realised and unrealised gains/(losses) on linked and non-linked assets and other income, giving total income (A); surrenders and partial surrenders and other claims, giving total claims (B); acquisition and renewal expenses (including commission), investment management expenses, one-off expenses, other expenses and taxation, giving total expenses (C); net assets brought forward, excess of income over expenditure (A)+(B)+(C), capital injected, dividends paid or payable, and net assets carried forward.
- Solvency: SCR, eligible capital resources and SCR ratio; Minimum Capital Requirement (MCR), eligible capital resources and MCR ratio.
"""


def flatten_appendix_1_table(text: str) -> str:
    return replace_section(
        text,
        "## **Appendix 1:  Example Financial",
        "\n## **Appendix 2: Financial",
        _APPENDIX_1_FLATTENED,
    )


_APPPENDIX_3_FLATTENED = """Provide a summary of the proposed key operational functions, covering the following for each function as indicated:

[Editors Note: the below is a flattened table]

- Structure of the function including reporting lines: underwriting, policy and claims, finance and investment.
- Overview of personnel including relevant experience and qualifications for the role: underwriting, policy and claims, finance and investment.
- Role, objectives and key activities of the function: underwriting, finance and investment (not required for policy and claims).
- Key reports utilised and frequency of reporting of the function: underwriting, policy and claims, finance and investment.

For policy and claims, each information requirement is to be provided for policy administration and claims administration separately.

"""


def flatten_appendix_3_table(text: str) -> str:
    return replace_section(
        text,
        "- Provide a summary of the proposed key",
        "- Provide the following information in respect",
        _APPPENDIX_3_FLATTENED,
    )
