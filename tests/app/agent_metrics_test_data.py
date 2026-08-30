from tests.app.models import Anchor, AgentTest


""" documents - must match the document field in chunks.jsonl exactly """
CODE = "The AML/CFT Code 2019"
HANDBOOK = "The AML Handbook (April 2026)"
POCA = "The Proceeds of Crime Act (POCA) 2008"
ATCA = "The Anti-Terrorism and Crime Act 2003"
RAO = "The Regulated Activities Order 2011"


""" test 1 - SOF applies to all customers, SOW only to a subset """
question1 = "what's the difference between source of funds and source of wealth?"
# paragraph 8(3) - SOF as part of standard CDD for every business relationship
anchor_1_a = "(e) taking reasonable measures to establish the source of funds"
# paragraph 14(3) - SOW only for higher risk domestic PEPs and any foreign PEP
anchor_1_b = "(3) A relevant person must take reasonable measures to establish the source of wealth"
# paragraph 15(3) - SOW for CDD
anchor_1_c = "(c) taking reasonable measures to establish the source of the wealth"

AgentTest1 = AgentTest(
    question=question1,
    anchors=(
        Anchor(document=CODE, text=anchor_1_a),
        Anchor(document=CODE, text=anchor_1_b),
        Anchor(document=CODE, text=anchor_1_c),
    ),
)


""" test 2 - multi-hop: exclusion reliant on the specified person definition """
question2 = (
    "can an advocate act as a trustee for a client without holding a Class 5 licence?"
)
# Schedule 1, Class 5 - the professional services exclusion
anchor_2_a = "5.(a) Where the activity -"

AgentTest2 = AgentTest(
    question=question2,
    anchors=(Anchor(document=RAO, text=anchor_2_a),),
)


""" test 3 - known dense retrieval failure, collides with PEP and legal person """
question3 = "what is a commercially exposed person?"
# 3.8.13.2 - definition
anchor_3_a = "The definition of a CEP is a natural person who, through their position or activity, may be exposed to an increased risk of bribery"
# 3.8.13.3 - CEP as a risk factor in the BRA and CRA
anchor_3_b = "Where a relevant person has customer accounts, business relationships, or occasional transactions with connections to a CEP"

AgentTest3 = AgentTest(
    question=question3,
    anchors=(
        Anchor(document=HANDBOOK, text=anchor_3_a),
        Anchor(document=HANDBOOK, text=anchor_3_b),
    ),
)


""" test 4 - false premise: SOW is not automatic for a domestic PEP """
question4 = (
    "it's true that you have to get source of wealth on an Isle of Man PEP right?"
)
# paragraph 14(3)(a) - domestic PEP, only where higher risk is identified
anchor_4_a = (
    "(a) a domestic PEP who has been identified as posing a higher risk of ML/FT"
)
# paragraph 14(3)(b) - all foreign PEPs will be in the same chunk

AgentTest4 = AgentTest(
    question=question4,
    anchors=(Anchor(document=CODE, text=anchor_4_a),),
)


""" test 5 - muddled premise: not laundering, is TF, and a procedural failure """
question5 = (
    "if a customer takes money from their salary and launders it to a terrorist, "
    "what offences could the firm face under POCA?"
)
# POCA section 139 - concealing etc.
anchor_5_a = "(e) removes criminal property from the Island."
# POCA section 140 - arrangements
anchor_5_b = "enters into or becomes concerned in an arrangement which the person knows or suspects facilitates"
# POCA section 141 - acquisition, use and possession
anchor_5_c = "(c) has possession of criminal property."
# ATCA section 10 - money laundering
anchor_5_d = "A person commits an offence if, for himself or another, he facilitates the retention or control of terrorist property"
# section 11(2) - failure to disclose
anchor_5_e = "(2) The person commits an offence if he does not disclose to the FIU as soon as is reasonably practicable"
# section 9 - facilitation of TF
anchor_5_f = "(a) he or she facilitates money or other property being made available to another person"
# paragraph 25 - internal disclosure procedures
anchor_5_g = "(2) The MLRO must make an external disclosure to the Financial Intelligence Unit in accordance with the reporting procedures"
# paragraph 41 - offences
anchor_5_h = (
    "(1) A person who contravenes the requirements of this Code is guilty of an offence"
)

AgentTest5 = AgentTest(
    question=question5,
    anchors=(
        Anchor(document=POCA, text=anchor_5_a),
        Anchor(document=POCA, text=anchor_5_b),
        Anchor(document=POCA, text=anchor_5_c),
        Anchor(document=ATCA, text=anchor_5_d),
        Anchor(document=ATCA, text=anchor_5_e),
        Anchor(document=ATCA, text=anchor_5_f),
        Anchor(document=CODE, text=anchor_5_g),
        Anchor(document=CODE, text=anchor_5_h),
    ),
)


AGENT_TEST_DATA = [
    AgentTest1,
    AgentTest2,
    AgentTest3,
    AgentTest4,
    AgentTest5,
]
