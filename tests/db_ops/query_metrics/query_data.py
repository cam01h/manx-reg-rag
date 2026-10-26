from pydantic import BaseModel


class RetrievalTest(BaseModel):
    search_term: str
    expected_strings: tuple[tuple[str, str], ...]


""" documents - must match the document field in chunks.jsonl exactly """
CODE = "The AML/CFT Code 2019"
HANDBOOK = "The AML Handbook (August 2026)"
SID = "AML/CFT Supplemental Information Document (July 2021)"
POCA = "The Proceeds of Crime Act (POCA) 2008"
ATCA = "The Anti-Terrorism and Crime Act 2003"
FRA = "Terrorism And Other Crime (Financial Restrictions) Act 2014"
FIU_ACT = "The Financial Intelligence Unit Act 2016"
RAO = "The Regulated Activities Order 2011"
DBROA = "Designated Businesses (Registration and Oversight) Act 2015"
SANCTIONS = "Sanctions Act 2024"
CIVIL_PENALTIES = (
    "Anti-Money Laundering And Countering The Financing Of Terrorism "
    "(Civil Penalties) Regulations 2019"
)
FSA08 = "Financial Services Act 2008"
RULE_BOOK = "Financial Services Rule Book 2016"
EXEMPTIONS = "Financial Services (Exemptions) Regulations 2011"
FS_CIVIL_PENALTIES = "Financial Services (Civil Penalties) Regulations 2015"
IA08 = "Insurance Act 2008"
INSURANCE_REGS = "Insurance Regulations 2025"
INSURANCE_CIVIL_PENALTIES = "Insurance (Civil Penalties) Regulations 2023"
CONFLICTS = "Conflicts of Interest Policy - Guidance Note - Rule 8.9"
BUSINESS_PLAN = "Business Plan Guidance"
RBOOK_GUIDANCE = "Guidance on the Financial Services Rule Book 2016"
CHANGE_OWNERSHIP = "Guidance on Rules 7.3 to 7.8 - Changes in Ownership and Structure"
INSPECTIONS = "Inspections Guidance for Firms"
NB_GOVERNANCE = "Guidance on Corporate Governance (all licenceholders except Deposit Takers and Professional Officers)"
CYBER = "Regulatory Guidance - Cyber Security"
DIRECTORS = "Guidance on Directorships, Trusteeships and similar Responsibilities held by Directors and individuals in 'controlled functions'"
CP_GUIDANCE = "Discretionary Civil Penalties under the Financial Services Act 2008 and the Insurance Act 2008 - Guidance Note"
TSP = "Guidelines on Expected Practice for Trust Service Providers"
RBREACH = "Guidance Note - Rule 8.17 - Breaches of Regulatory Requirements"
OUTSOURCING = "Guidance on Rule 8.16 - Outsourcing and Delegation of Functions"
F_AND_P = "Regulatory Guidance - Fitness and Propriety"
QSL = "Guidance on Rule 2.30 and Appendix 3 (Note 4) - Qualifying Subordinated Loans"
RECORD_KEEPING = "Financial Services Rule Book 2016 - Rules relating to record keeping"
CONSENT_NOTIFY = (
    "Financial Services Rule Book 2016 - Consent and Information Summary Table"
)
REGISTERS = "Financial Services Rule Book 2016 - Obligations to keep registers"
POLICIES = "Financial Services Rule Book 2016 - Rules relating to policies"


""" test 1 - bare acronym, collides with PEP """
query1 = "CEP"
# 3.8.13.2 - definition
expected_1_a = "The definition of a CEP is a natural person who, through their position or activity, may be exposed to an increased risk of bribery"
# 3.8.13.3 - CEP as a risk factor in the BRA and CRA
expected_1_b = "Where a relevant person has customer accounts, business relationships, or occasional transactions with connections to a CEP"

QueryTest1 = RetrievalTest(
    search_term=query1,
    expected_strings=((HANDBOOK, expected_1_a), (HANDBOOK, expected_1_b)),
)

""" test 2 - expanded form of test 1, should reach the same chunks """
query2 = "commercially exposed person"
# 3.8.13.2 - definition
expected_2_a = "The definition of a CEP is a natural person who, through their position or activity, may be exposed to an increased risk of bribery"
# 3.8.13.3 - CEP as a risk factor in the BRA and CRA
expected_2_b = "Where a relevant person has customer accounts, business relationships, or occasional transactions with connections to a CEP"

QueryTest2 = RetrievalTest(
    search_term=query2,
    expected_strings=((HANDBOOK, expected_2_a), (HANDBOOK, expected_2_b)),
)

""" test 3 - spans three documents """
query3 = "SARs disclosure to the FIU"
# section 24 - disclosure of information to the FIU
expected_3_a = "Any person may disclose information to the FIU if the disclosure is made for the purposes of the exercise"
# section 143 - failure to disclose, nominated officers
expected_3_b = (
    "A person nominated to receive disclosures under section 142 commits an offence"
)
# paragraph 28 - registers of disclosures
expected_3_c = "A relevant person must establish and maintain separate registers of"

QueryTest3 = RetrievalTest(
    search_term=query3,
    expected_strings=(
        (FIU_ACT, expected_3_a),
        (POCA, expected_3_b),
        (CODE, expected_3_c),
    ),
)

""" test 4 - definition-resolution chain: is a lawyer a 'specified person'? """
query4 = "lawyer solicitor advocate exemption exclusion from financial services licence"
# Schedule 1, Class 2 - investment business, professional services exclusion
expected_4_a = (
    "2.(n) In the case of an activity falling within paragraph (3) to (7) of Class 2"
)
# Schedule 1, Class 5 - trust services, professional services exclusion
expected_4_b = "5.(a) Where the activity -"
# Schedule 1, Class 8 - money transmission, activities incidental to professional services
expected_4_c = (
    "8.(b) In the case of an activity falling within paragraph (2) of Class 8"
)

QueryTest4 = RetrievalTest(
    search_term=query4,
    expected_strings=(
        (RAO, expected_4_a),
        (RAO, expected_4_b),
        (RAO, expected_4_c),
    ),
)

""" test 5 - is Code compliance a defence? mandatory consideration vs express defence """
query5 = "compliance with the AML/CFT code as a defence"
# section 142(12) - court must consider compliance and guidance
expected_5_a = (
    "(12) In deciding whether a person committed an offence under this section"
)
# section 143(10) - same, nominated officers
expected_5_b = (
    "(10) In deciding whether a person committed an offence under this section"
)
# section 13C - express reasonable excuse defence
expected_5_c = "It is a defence for a person charged with an offence under any of sections 7, 8, 9, 9A or 10 to prove that"

QueryTest5 = RetrievalTest(
    search_term=query5,
    expected_strings=(
        (POCA, expected_5_a),
        (POCA, expected_5_b),
        (ATCA, expected_5_c),
    ),
)

""" test 6 - SOW is not required for everyone; threshold is higher risk / PEP """
query6 = "do I need source of wealth for every customer or only some of them"
# paragraph 14(3) - SOW for higher risk domestic PEPs and any foreign PEP
expected_6_a = "(3) A relevant person must take reasonable measures to establish the source of wealth of"
# paragraph 15(2)(c) - SOW is a specified ECDD measure
expected_6_b = (
    "taking reasonable measures to establish the source of the wealth of a customer"
)
# 3.8.5 - SOW starts from a higher risk threshold, unlike SOF
expected_6_c = "source of wealth requirements start from a higher risk threshold"

QueryTest6 = RetrievalTest(
    search_term=query6,
    expected_strings=(
        (CODE, expected_6_a),
        (CODE, expected_6_b),
        (HANDBOOK, expected_6_c),
    ),
)

""" test 7 - record retention period """
query7 = "how long do we have to keep customer records after the relationship ends"
# paragraph 34(3) - 5 years from completion of the transaction
expected_7_a = "the records must be kept for a period of 5 years from the date of the completion of the transaction"
# paragraph 33 - what must be kept
expected_7_b = "such other records as are sufficient to permit reconstruction of individual transactions"

QueryTest7 = RetrievalTest(
    search_term=query7,
    expected_strings=((CODE, expected_7_a), (CODE, expected_7_b)),
)

""" test 8 - tipping off, same offence in two Acts """
query8 = "can I tell the customer that we have reported them"
# section 145 - tipping off: regulated sector
expected_8_a = "an offence is committed under subsections (1) and (3) whether or not"
# section 15ZA - tipping off: regulated sector, terrorist property
expected_8_b = "in accordance with a procedure established by that person's employer for the making of disclosures"

QueryTest8 = RetrievalTest(
    search_term=query8,
    expected_strings=((POCA, expected_8_a), (ATCA, expected_8_b)),
)

""" test 9 - MLRO appointment and seniority """
query9 = "who has to be appointed as MLRO and how senior do they need to be"
# paragraph 23(1) - appointment
expected_9_a = "must appoint a Money Laundering Reporting Officer"
# paragraph 23(2)(d) - retains responsibility for external disclosures
expected_9_b = "retain responsibility for all external disclosures, including where a branch or subsidiary"

QueryTest9 = RetrievalTest(
    search_term=query9,
    expected_strings=((CODE, expected_9_a), (CODE, expected_9_b)),
)

""" test 10 - the three principal ML offences """
query10 = "what are the main money laundering offences"
# section 139 - concealing etc.
expected_10_a = "(e) removes criminal property from the Island."
# section 140 - arrangements
expected_10_b = "enters into or becomes concerned in an arrangement which the person knows or suspects facilitates"
# section 141 - acquisition, use and possession
expected_10_c = "(c) has possession of criminal property."

QueryTest10 = RetrievalTest(
    search_term=query10,
    expected_strings=(
        (POCA, expected_10_a),
        (POCA, expected_10_b),
        (POCA, expected_10_c),
    ),
)

""" test 11 - consent regime and the moratorium """
query11 = "can we go ahead with the payment once we have reported it"
# section 151(1) - what the appropriate consent is
expected_11_a = "the consent of a nominated officer to do a prohibited act if an authorised disclosure"
# section 151(6) - the 31 day moratorium period
expected_11_b = "The moratorium period is the period of 31 days starting with the day on which the person receives notice"
# section 152 - nominated officer must not give consent unless a condition is met
expected_11_c = "A nominated officer must not give the appropriate consent to the doing of a prohibited act unless"

QueryTest11 = RetrievalTest(
    search_term=query11,
    expected_strings=(
        (POCA, expected_11_a),
        (POCA, expected_11_b),
        (POCA, expected_11_c),
    ),
)

""" test 12 - civil penalty levels and amounts """
query12 = "how much can the Authority fine us for an AML breach"
# Schedule - the penalty table
expected_12_a = "Up to 5% of the relevant person's income"
# regulation 5(3) - Level 2 factors
expected_12_b = "the relevant person failed to bring the contravention to the Authority"

QueryTest12 = RetrievalTest(
    search_term=query12,
    expected_strings=(
        (CIVIL_PENALTIES, expected_12_a),
        (CIVIL_PENALTIES, expected_12_b),
    ),
)

""" test 13 - the 25% threshold is Handbook guidance, not in the Code """
query13 = "what shareholding percentage makes someone a beneficial owner of a company"
# 3.4.5 - 25% or more of shares or voting rights
expected_13_a = "25% or more of the shares or voting rights in the legal person"
# paragraph 12(5) - controlling interest in a legal person
expected_13_b = "obtaining the identity of the beneficial owner who ultimately has a controlling interest"

QueryTest13 = RetrievalTest(
    search_term=query13,
    expected_strings=((HANDBOOK, expected_13_a), (CODE, expected_13_b)),
)

""" test 14 - registration requirement for designated businesses """
query14 = "does an estate agent have to register with the Authority"
# section 7(1) - prohibition on carrying on unless registered
expected_14_a = "must not carry on, or hold itself out as carrying on, a designated business in or from the Island"
# section 4 - Schedule 1 lists designated businesses and exemptions
expected_14_b = "certain Designated Non-Financial Businesses and Professions"

QueryTest14 = RetrievalTest(
    search_term=query14,
    expected_strings=((DBROA, expected_14_a), (DBROA, expected_14_b)),
)

""" test 15 - asset freezing """
query15 = "freezing order funds made available to a designated person"
# section 13 - freezing orders: general
expected_15_a = (
    "A freezing order is an order that prohibits persons from making funds available"
)
# section 16 - duration of freezing orders
expected_15_b = (
    "at the end of the period of 30 days starting with the date on which it was made"
)

QueryTest15 = RetrievalTest(
    search_term=query15,
    expected_strings=((FRA, expected_15_a), (FRA, expected_15_b)),
)

""" test 16 - training frequency """
query16 = "how often does AML training have to be given to staff"
# paragraph 32(1) - at least annually
expected_16_a = "must provide or arrange education and training, including refresher training, at least annually"

QueryTest16 = RetrievalTest(
    search_term=query16,
    expected_strings=((CODE, expected_16_a),),
)

""" test 17 - business risk assessment content """
query17 = "what does the business risk assessment have to take into account"
# paragraph 5(1) - what the BRA estimates
expected_17_a = "an assessment that estimates the risk of ML/FT posed by the relevant person's business and customers"
# paragraph 5(3)(b) - must have regard to the NRA
expected_17_b = "any relevant findings of the most recent National Risk Assessment relating to the Island"

QueryTest17 = RetrievalTest(
    search_term=query17,
    expected_strings=((CODE, expected_17_a), (CODE, expected_17_b)),
)

""" test 18 - introduced business """
query18 = "relying on an introducer to carry out CDD on our behalf"
# paragraph 9(1) - when introduced business applies
expected_18_a = (
    "This paragraph applies where a customer is introduced to a relevant person"
)
# paragraph 9(4) - what the risk assessment must include
expected_18_b = "whether the introducer has met the customer;"

QueryTest18 = RetrievalTest(
    search_term=query18,
    expected_strings=((CODE, expected_18_a), (CODE, expected_18_b)),
)

""" test 19 - same cash threshold stated in two different instruments """
query19 = "cash payment threshold high value dealer"
# Schedule 4 - sectors to which the Code applies
expected_19_a = (
    "accepting a total cash payment (in any currency) that is equivalent to at least"
)
# Schedule 1 - designated businesses (note: no space after the bracket in this document)
expected_19_b = (
    "accepting a total cash payment (in any currency)that is equivalent to at least"
)

QueryTest19 = RetrievalTest(
    search_term=query19,
    expected_strings=((POCA, expected_19_a), (DBROA, expected_19_b)),
)

""" test 20 - terrorist financing offences """
query20 = "terrorist financing offences fundraising and use of money"
# section 7 - fund-raising
expected_20_a = "invites another to provide money or other property"
# section 10 - money laundering of terrorist property
expected_20_b = "facilitates the retention or control of terrorist property"

QueryTest20 = RetrievalTest(
    search_term=query20,
    expected_strings=((ATCA, expected_20_a), (ATCA, expected_20_b)),
)

""" test 21 - FSA08, penalty and revocation are alternatives """
query21 = "can the FSA fine us and take away our licence for the same breach"
# section 16(3)(a) - a penalty and revocation cannot both be used for the same contravention
expected_21_a = "both require a person to pay a penalty under this section and revoke a licence issued under section 7"

QueryTest21 = RetrievalTest(
    search_term=query21,
    expected_strings=((FSA08, expected_21_a),),
)

""" test 22 - Rule Book, combining roles (test 9 covers MLRO appointment under the Code) """
query22 = "can our head of compliance also be the MLRO"
# rule 8.21(2) - the same individual may hold both roles
expected_22_a = (
    "The same individual may be appointed as Head of compliance and as MLRO or DMLRO."
)

QueryTest22 = RetrievalTest(
    search_term=query22,
    expected_strings=((RULE_BOOK, expected_22_a),),
)

""" test 23 - Exemptions Regulations, the de minimis directorship exemption """
query23 = (
    "do I need a corporate services licence if I am only a director of a few companies"
)
# Schedule 1, Class 4, paragraph 4.2(1) - 10 or fewer appointments
expected_23_a = "section 4 does not apply to an individual who holds 10 or fewer appointments as a director"

QueryTest23 = RetrievalTest(
    search_term=query23,
    expected_strings=((EXEMPTIONS, expected_23_a),),
)

""" test 24 - SID, non face to face customers """
query24 = "can we meet a new customer over a video call or does it have to be in person"
# 3.6 - a telephone call is not meeting the customer, video can be
expected_24_a = "A non-visual medium such as a telephone call does not qualify as meeting the customer."

QueryTest24 = RetrievalTest(
    search_term=query24,
    expected_strings=((SID, expected_24_a),),
)

""" test 25 - Sanctions Act, strict liability for monetary penalties """
query25 = "can we be fined for breaching financial sanctions if we did not know the person was sanctioned"
# section 7(2) - knowledge or suspicion is ignored
expected_25_a = "any requirement imposed by or under that provision for the person to have known, suspected or believed any matter is to be ignored"

QueryTest25 = RetrievalTest(
    search_term=query25,
    expected_strings=((SANCTIONS, expected_25_a),),
)

""" test 26 - conflicts guidance, Appendix 1 contents list """
query26 = "what should our conflicts of interest policy cover"
# Appendix 1, item 5 - steps to remove, control or mitigate
expected_26_a = (
    "Steps which could be taken to remove, control, or mitigate the conflict"
)

QueryTest26 = RetrievalTest(
    search_term=query26,
    expected_strings=((CONFLICTS, expected_26_a),),
)

""" test 27 - business plan guidance """
query27 = (
    "what financial forecasts do we need in the business plan for a licence application"
)
# 2.4 - three bases of projection
expected_27_a = "Financial projections to be prepared on pessimistic, realistic and optimistic bases"

QueryTest27 = RetrievalTest(
    search_term=query27,
    expected_strings=((BUSINESS_PLAN, expected_27_a),),
)

""" test 28 - Rule Book guidance, only in the guidance not the rule """
query28 = "can we send notifications to the FSA by email"
# guidance on rule 1.1 - letter or e-mail accepted
expected_28_a = "The Authority accepts notification either by letter or by e-mail except where a signed document is required by a rule"

QueryTest28 = RetrievalTest(
    search_term=query28,
    expected_strings=((RBOOK_GUIDANCE, expected_28_a),),
)

""" test 29 - change in ownership guidance """
query29 = "what do we need to send the Authority when a buyer wants to take control of our firm"
# 1.4 - draft sale and purchase agreement
expected_29_a = (
    "A copy of the sale and purchase agreement (this will often be in draft initially)"
)

QueryTest29 = RetrievalTest(
    search_term=query29,
    expected_strings=((CHANGE_OWNERSHIP, expected_29_a),),
)

""" test 30 - inspections guidance """
query30 = "will the FSA always give us notice before an inspection"
# 6.1 - when short notice or unannounced inspections are used
expected_30_a = "Short notice, or unannounced inspections are undertaken when the identified or perceived risk is so material"

QueryTest30 = RetrievalTest(
    search_term=query30,
    expected_strings=((INSPECTIONS, expected_30_a),),
)

""" test 31 - non-bank governance guidance, small firms """
query31 = "how often should the board of a small owner-managed firm meet"
# 3.3 - at least two board meetings a year
expected_31_a = "It is recommended that the board holds at least two meetings per annum"

QueryTest31 = RetrievalTest(
    search_term=query31,
    expected_strings=((NB_GOVERNANCE, expected_31_a),),
)

""" test 32 - cyber guidance, Appendix 2 example (flattened table) """
query32 = "a client's email was hacked and we were sent a fake request to pay money out"
# Appendix 2, Example 1 - payment requests
expected_32_a = "receiving fraudulent payment requests by email after clients' email accounts had been hacked"

QueryTest32 = RetrievalTest(
    search_term=query32,
    expected_strings=((CYBER, expected_32_a),),
)

""" test 33 - directorships guidance, no fixed cap """
query33 = "is there a maximum number of directorships one of our staff can hold"
# Numbers - depends on a range of factors, no fixed number
expected_33_a = "the determination of an appropriate number of posts depends upon a range of factors"

QueryTest33 = RetrievalTest(
    search_term=query33,
    expected_strings=((DIRECTORS, expected_33_a),),
)

""" test 34 - civil penalties guidance, publication """
query34 = "will a civil penalty against us be made public"
# 3.4.2 - limited details published on the website
expected_34_a = "Limited details of discretionary civil penalties imposed by the Authority will be published on the Authority's website"

QueryTest34 = RetrievalTest(
    search_term=query34,
    expected_strings=((CP_GUIDANCE, expected_34_a),),
)

""" test 35 - FSA08 civil penalties regs, late return (flattened table) """
query35 = "what is the fine for submitting a regulatory return a week late"
# Schedule, Table 2 - a week late is the 5 to 20 business days row
expected_35_a = (
    "Return submitted/provided from 5 to 20 business days after end of specified period"
)

QueryTest35 = RetrievalTest(
    search_term=query35,
    expected_strings=((FS_CIVIL_PENALTIES, expected_35_a),),
)

""" test 36 - trust service providers guidance """
query36 = "do trustees have to keep formal minutes of their decisions"
# Record keeping - trust law is not prescriptive about minutes
expected_36_a = "trust law is not prescriptive in its requirements for trustee deliberations to be formally documented in minutes"

QueryTest36 = RetrievalTest(
    search_term=query36,
    expected_strings=((TSP, expected_36_a),),
)

""" test 37 - rule breaches guidance, record everything """
query37 = "do we have to record breaches that are not material"
# Recording a breach - why all breaches are recorded
expected_37_a = "Recording all breaches avoids debates about whether a breach is or is not recordable"

QueryTest37 = RetrievalTest(
    search_term=query37,
    expected_strings=((RBREACH, expected_37_a),),
)

""" test 38 - outsourcing guidance, outsourced compliance """
query38 = "can we use an external consultant as our compliance function"
# FAQ 3 - outsourced compliance in larger licenceholders
expected_38_a = "The Authority would only expect to see outsourcing of compliance services by a larger licenceholder"

QueryTest38 = RetrievalTest(
    search_term=query38,
    expected_strings=((OUTSOURCING, expected_38_a),),
)

""" test 39 - F&P guidance, criminal record checks """
query39 = "does a new director need a criminal record check before we apply to the FSA"
# 8(c) - criminal record check for notified and accepted Controlled Functions
expected_39_a = "Individuals proposed for notified and accepted Controlled Functions should be subject to a criminal record check"

QueryTest39 = RetrievalTest(
    search_term=query39,
    expected_strings=((F_AND_P, expected_39_a),),
)

""" test 40 - qualifying subordinated loans guidance """
query40 = "can a subordinated loan from our parent company be paid back early"
# key features - cannot be repaid or unwound
expected_40_a = "They cannot be repaid or unwound (even upon maturity or the insolvency of the licenceholder)"

QueryTest40 = RetrievalTest(
    search_term=query40,
    expected_strings=((QSL, expected_40_a),),
)

""" test 41 - record keeping summary table, one row per rule """
query41 = "do we have to keep recordings of phone calls with clients"
# Table A, rule 8.28 - clients' records
expected_41_a = (
    "including recordings of telephone conversations or electronic communications"
)

QueryTest41 = RetrievalTest(
    search_term=query41,
    expected_strings=((RECORD_KEEPING, expected_41_a),),
)

""" test 42 - consent and notification summary table, one row per rule """
query42 = "do we need FSA consent before opening a branch overseas"
# rule 7.3(1)(d) - prior consent (same wording is in the Rule Book itself)
expected_42_a = "acquiring or establishing a trading subsidiary, branch or representative office in the Island or elsewhere"

QueryTest42 = RetrievalTest(
    search_term=query42,
    expected_strings=((CONSENT_NOTIFY, expected_42_a),),
)

""" test 43 - registers summary table, one row per rule """
query43 = "do we need to log every pricing error or only the big ones"
# rule 8.60(3) - all pricing errors, not just those over 0.5%
expected_43_a = "limited to errors of more than 0.5%"

QueryTest43 = RetrievalTest(
    search_term=query43,
    expected_strings=((REGISTERS, expected_43_a),),
)

""" test 44 - policies summary table, one row per rule """
query44 = "which licence classes need a remuneration policy"
# rule 8.7 - remuneration policy row
expected_44_a = "Class 1, Class 2 and Class 3(6),(7) or (8)"

QueryTest44 = RetrievalTest(
    search_term=query44,
    expected_strings=((POLICIES, expected_44_a),),
)

""" test 45 - Insurance Act, dividends and the SCR """
query45 = (
    "can an insurer pay a dividend while it is below its solvency capital requirement"
)
# section 12A(1) - no dividend in breach of SCR
expected_45_a = "No authorised insurer may declare or pay a dividend or make any distribution to any person other than a policyholder where"

QueryTest45 = RetrievalTest(
    search_term=query45,
    expected_strings=((IA08, expected_45_a),),
)

""" test 46 - Insurance Regulations, class table (flattened table) """
query46 = "which class of insurance authorisation does a captive insurer need"
# regulation 3(3) - class 12
expected_46_a = "Contracts within classes 1 to 11 which comply with the requirements set out in Schedule 1"

QueryTest46 = RetrievalTest(
    search_term=query46,
    expected_strings=((INSURANCE_REGS, expected_46_a),),
)

""" test 47 - insurance civil penalties regs, same wording as the FSA08 regs """
query47 = "what level of civil penalty applies if an insurer's directors tried to hide a failing from the FSA"
# Schedule, Level 2 (d) - concealment (also in the FSA08 2015 regs, this test needs the insurance one)
expected_47_a = (
    "have attempted to conceal the serious regulatory failing from the Authority"
)

QueryTest47 = RetrievalTest(
    search_term=query47,
    expected_strings=((INSURANCE_CIVIL_PENALTIES, expected_47_a),),
)


QUERY_TEST_DATA = [
    QueryTest1,
    QueryTest2,
    QueryTest3,
    QueryTest4,
    QueryTest5,
    QueryTest6,
    QueryTest7,
    QueryTest8,
    QueryTest9,
    QueryTest10,
    QueryTest11,
    QueryTest12,
    QueryTest13,
    QueryTest14,
    QueryTest15,
    QueryTest16,
    QueryTest17,
    QueryTest18,
    QueryTest19,
    QueryTest20,
    QueryTest21,
    QueryTest22,
    QueryTest23,
    QueryTest24,
    QueryTest25,
    QueryTest26,
    QueryTest27,
    QueryTest28,
    QueryTest29,
    QueryTest30,
    QueryTest31,
    QueryTest32,
    QueryTest33,
    QueryTest34,
    QueryTest35,
    QueryTest36,
    QueryTest37,
    QueryTest38,
    QueryTest39,
    QueryTest40,
    QueryTest41,
    QueryTest42,
    QueryTest43,
    QueryTest44,
    QueryTest45,
    QueryTest46,
    QueryTest47,
]
