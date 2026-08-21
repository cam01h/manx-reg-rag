from pydantic import BaseModel


class RetrievalTest(BaseModel):
    search_term: str
    expected_strings: tuple[tuple[str, str], ...]


""" documents - must match the document field in chunks.jsonl exactly """
CODE = "The AML/CFT Code 2019"
HANDBOOK = "The AML Handbook (April 2026)"
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
]
