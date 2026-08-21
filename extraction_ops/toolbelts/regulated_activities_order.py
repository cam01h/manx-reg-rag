from config import PROJECT_ROOT
from extraction_ops.models import (
    ChunkSplitters,
    DefinitionTools,
    SectionMarkers,
    ToolBelt,
)
from extraction_ops.toolbelts.shared_funcs import (
    base_body_cleaner,
    base_double_def_line,
    base_false_double_def,
    base_header_cleaner,
    base_text_cleaner,
    replace_from_dict,
    replace_section,
    split_on_bracketed_num,
    split_on_paragraph,
    starts_with,
    strip_footnote_markers,
)

PART_1_FLATENED_TABLE = (
    '"accommodation address facilities" means the provision of an address at, or within which any of the following services are provided -\n'
    "(a) the receipt or dispatch on behalf of a person of any communication or packet by post, a courier service, hand delivery, a telecommunications system, wireless telegraphy or any electronic medium;\n"
    "(b) the redirection of communications or packets on behalf of a person;\n"
    "(c) facilities for the service of process and notices on a company as provided by section 11(4) of the Foreign Companies Act 2014;\n"
    "\n"
    '"the Act" means the Financial Services Act 2008;\n'
    "\n"
    '"administration services" (in relation to company)\n'
    "includes the following activities -\n"
    "(a) the keeping of any register which require to be kept by a company under the Companies Acts 1931 to 2004;\n"
    "(b) the keeping of accounting records and the preparation of accounts which are required to be kept or prepared by the company under the Companies Act 1982;\n"
    "(c) the preparation and making of returns required to be made by a company to the Department of Economic Development under the Companies Acts 1931 to 2004;\n"
    "(d) the preparation and submission of documents which a company is required to prepare and submit under the Companies Acts 1931 to 2004;\n"
    "(e) the convening of general meetings of a company;\n"
    "(f) the taking, preparation and entry of minutes of proceedings at general meetings and directors’ meeting of a company;\n"
    "(g) the entry of written resolutions which are required to be entered in a minute book by a company under section 119A of the Companies Act 1931;\n"
    "(h) the entry of decisions of sole members which are required to be entered in a minute book by a company under section 119B of the Companies Act 1931\n"
    "(i) equivalent activities in relation to companies which are not constituted under the Companies Act 1931 to 2004.\n"
    "\n"
    '"agent" includes an attorney and a nominee, and also, for the purpose of Class 8 regulated activity, agent includes a person who provides payment services on behalf of an issuer of electronic money or a payment institution;\n'
    "\n"
    '"attorney" means the donee of power of attorney acting under power;\n'
    "\n"
    '"buy" means acquire for valuable consideration;\n'
    "\n"
    '"certificate representing securities" means any certificate or other instrument which confers -\n'
    "(a) property rights in respect of any share, debenture, government security or warrant;\n"
    "(b) any right to acquire, dispose of, underwrite or convert an instrument, being a right to which the holder would be entitled if he had any such investment to which the certificate or instrument relates; or\n"
    "(c) a contractual right (other than an option) to acquire any such investment otherwise than by subscription;\n"
    "\n"
    '"client" includes a customer (and vice versa)\n'
    "\n"
    '"client bank account" means a bank account which is -\n'
    "(a) specially created for the purpose of holding client money, and\n"
    "(b) segregated from any account holding money which is not client money;\n"
    "\n"
    '"client money" means money which, for the purpose or in the course of a business carried on by him, a person holds or receives on behalf of a customer or client;\n'
    "\n"
    '"close relative" in relation to an individual, means a child, step-child, parent, stepparent, brother, sister, step-brother, step-sister or spouse of that individual;\n'
    "\n"
    '"collective investment scheme" has the same meaning as in the Collective Investment Schemes Act 2008;\n'
    "\n"
    '"company" includes any body corporate, whether constituted under the law of the Island or elsewhere;\n'
    "\n"
    '"connected individuals" (in relation to a disposal or inquisition of shares in a company) means persons each of whom is, or is a close relative of, a person who is or (as the case may be) is to be a director manager of the company;\n'
    "\n"
    '"credit union" is a body described in and incorporated under the Credit Unions Act 1993;\n'
    "\n"
    '"debenture" includes debenture stock, loan stock, bonds and certificates of deposit and other instruments creating or acknowledging indebtedness, but does not include -\n'
    "(a) any instrument acknowledging or creating indebtedness for, or for money borrowed to defray, the consideration payable under a contract for the supply of goods or services;\n"
    "(b) a cheque or other bill of exchange, a banker’s draft or a letter of credit;\n"
    "(c) a banknote, a statement showing a balance in a current, deposit or saving account or (by reason of any financial obligation contained in it) relating to a lease or other disposition of property, deed of bond and security or an insurance policy;\n"
    "(d) a government security;\n"
    "\n"
    '"debenture warrant" means an instrument entitling the holder to, or to subscribe for, a debenture;\n'
    "\n"
    '"deposit" means a sum of money paid (otherwise than for or in respect of a debenture, Government security, warrant or certificate representing securities) on terms -\n'
    "(a) under which it will be repaid, with or without interest or premium, either on demand or at a time or in circumstances agreed by or on behalf of the person making the payment and the person receiving it; and\n"
    "(b) which are not referable to the provision of property (other than currency) or services or the giving of security, and references in this Order to money deposited and to the making of a deposit shall construed accordingly;\n"
    "and includes a sum of money paid by an investing member to a building society held in share and / or savings account but not sums invested in permanent interest bearing shares.\n"
    "A sum is not a deposit if it is received by a payment institution from a payment service user with a view to the provision of payment services; nor is it a deposit if it is immediately exchanged for electronic money.\n"
    "For the purposes of this definition, money is paid on terms which are referable to the provision of property or services or the giving of security if, and only if, -\n"
    "(i) it is paid by way of advance or part payment under contract for the sale, hire or other provision of property or services, and is repayable only in the event that the property or services is or are not in fact sold, hired or otherwise provided; or\n"
    "(ii) it is paid by way of security for the performance of a contract or by way of security in respect of loss which may result from the non-performance of a contract; or\n"
    "(iii) without prejudice to (ii) above, it is paid by way of security for the delivery up or return of any property, whether in a particular state of repair or otherwise;\n"
    "\n"
    '"director" has the same meaning as in the Act but also includes -\n'
    "(a) an alternate director; and\n"
    "(b) in relation to a limited partnership which has elected to have legal personality, an individual who is a general partner;\n"
    "\n"
    '"disposal" includes -\n'
    "(a) in the case of an investment consisting of rights under a contract or other arrangements, assuming the corresponding liabilities under the contract or arrangements;\n"
    "(b) in the case of any other investment, issuing or creating the investment or granting the rights or interests of which it consists;\n"
    "(c) in the case of an investment consisting of rights under a contract, surrendering, assigning or converting those rights;\n"
    "\n"
    '"electronic money" or "e-money" means electronically (including magnetically) stored monetary value as represented by a claim on the electronic money issuer which is -\n'
    "(a) issued on receipt of funds for the purpose of making payment transactions;\n"
    "(b) accepted by a person other than the electronic money issuer; and\n"
    "(c) is not excluded by exclusion 8(i);\n"
    "\n"
    '"eligible custodian" means -\n'
    "(a) a licenceholder authorised to carry on activities falling within paragraph (5) of Class 2;\n"
    "(b) a wholly-owned subsidiary of such a licence holder which -\n"
    "(i) carries on no other business than those activities; and\n"
    "(ii) acts only in accordance with the direction or instructions of the licence holder; or\n"
    "(c) in relation to such a licence holder, a person carrying on business in a country or territory outside the Island\n"
    "\n"
    '"enactment" includes a statute or other instrument of a legislative character having effect in the Island or a country or territory outside the Island;\n'
    "\n"
    '"exempt collective investment scheme" has the same meaning as in the Collective Investment Schemes Act 2008;\n'
    "\n"
    '"exempt-type scheme" means a scheme which does not, but would be an exempt scheme if it did, comply with paragraph 1(2) of Schedule 3 to the Collective Investment Schemes Act 2008;\n'
    "\n"
    '"express trust" means a trust created by the intentional act of the settlor either orally or evidenced in writing;\n'
    "\n"
    '"government security" means loan stock or a bond or other instrument creating or acknowledging indebtedness issued by or on behalf of -\n'
    "(a) the government of the Island or any country or territory outside the Island;\n"
    "(b) a local authority in the Island or elsewhere;\n"
    "(c) any international organisation the members of which include the Island or any Member State of the European Union;\n"
    "but does not include -\n"
    "(i) any instrument acknowledging or creating indebtedness for, or for money borrowed to defray, the consideration payable under a contract for the supply of goods or services;\n"
    "(ii) a cheque or other bill of exchange, a banker’s draft or a letter of credit;\n"
    "(iii) a banknote, a statement showing a balance in a current, deposit or savings account or (by reason of any financial obligation contained in it) to a lease or other disposition of property, a heritable security or an insurance policy;\n"
    "\n"
    '"instrument" includes any record which may be produced in a visible and legible form;\n'
    "\n"
    '"investment" means any of the following -\n'
    "(a) a share;\n"
    "(b) a debenture;\n"
    "(c) a government security;\n"
    "(d) a warrant;\n"
    "(e) a certificate representing securities;\n"
    "(f) a unit in a collective investment scheme;\n"
    "(g) an option to acquire or dispose of -\n"
    "(i) an investment falling within this or any other paragraph of this definition;\n"
    "(ii) currency of any country or territory,\n"
    "(iii) gold, palladium, platinum or silver ; or\n"
    "(iv) a commodity or goods of any description except under an option entered into for commercial and not investment purposes; or\n"
    "(v) an option to acquire or dispose of an option falling within sub-paragraph (i), (ii), (iii) or (iv).\n"
    "(h) rights under a contract for the sale of a commodity or goods of any other description under which delivery is to be made at a future date and at a price agreed on when the contract is made, except rights under contract made for commercial and not investment purposes;\n"
    "(i) rights under contract for differences or under any other contract the purpose or pretended purpose of which is to secure a profit or void a loss by reference to fluctuations in the value or price of property of any description or in an index or other factor designated for that purpose in the contract;\n"
    "(j) long-term insurance;\n"
    "(ja) in relation to activities falling within paragraph (6) or (7) of Class 2 only, rights under a personal pension scheme;\n"
    "(k) rights to and interests in anything falling within any other paragraph of this definition, except interests under the trusts of an occupational pension scheme.\n"
    "\n"
    '"Isle of Man person" means -\n'
    "(a) an individual who is resident in the Isle of Man; or\n"
    "(b) a company incorporated or carrying on business in the Isle of Man.\n"
    "\n"
    # every time participators is used, joint enterprise is also used on the same line, no need to extract, leave fancy quotes in and runs after base cleaner
    '"joint enterprise" means an enterprise into which 2 or more persons (“participators”) enter for commercial reasons related to a business or businesses (other than activities falling within Class 2) carried on by them, but does not include an enterprise the whole or main purpose of which is to undertake ant regulated activity; and for the purpose, where a participator is a company and a member of a group, each other member of the group shall also be regarded as a participator in the enterprise;\n'
    "\n"
    '"licensed" means licensed under section 7 of the Act;\n'
    "\n"
    '"long-term insurance" means rights under a contract of insurance falling within any of the following descriptions, namely life, annuity, marriage, birth, permanent health, tontines, capital redemption and pension fund management, but does not include pure protection contracts;\n'
    "\n"
    '"money remittance" means a payment service where funds are received from a payer, without any payment accounts being created in the name of the payee or payer, for the sole purpose of transferring a corresponding amount to a payee or another payment service provider acting on behalf of the payee or where such funds are received on behalf of and made available to the payee;\n'
    "\n"
    '"nominee company" means a company whose sole activity is to hold as nominee or bare trustee monies or investments beneficially owned by other persons;\n'
    "\n"
    '"occupational pension scheme" has the meaning given in section 1 of the Pension Schemes Act 1993 (of Parliament) as it has effect in the Isle of Man;\n'
    "\n"
    '"offer" includes an invitation to treat;\n'
    "\n"
    '"overseas person" means a person who -\n'
    "(a) does not carry on a regulated activity from a permanent place of business maintained by him in the Island; and\n"
    "(b) is not -\n"
    "(i) a company incorporated in the Island under the Companies Act 1931 to 2004 or the Companies Act 2006; or\n"
    "(ii) a company incorporated outside the Island which is registered under Part X1 of the Companies Act 1931; or\n"
    "(iii) a limited partnership registered in the Island under Part II of the Partnership Act 1909;\n"
    "(iv) a foundation established in the Island under the Foundations Act 2011;\n"
    "\n"
    '"Payee" means a person who is the intended recipient of the funds which have been the subject of a payment transaction;\n'
    "\n"
    '"Payer" means -\n'
    "(a) a person who holds a payment account and initiates, or consents to the initiation of, a payment order from that payment account; or\n"
    "(b) where there is no payment account, a person who gives a payment order;\n"
    "\n"
    '"payment account" means an account held in the name of one or more payment service users which is used for the execution of payment transactions;\n'
    "\n"
    '"payment institution" means -\n'
    "(a) a person licenced by the Authority to undertake the regulated activity of Class 8(2); or\n"
    "(b) a person subject to the transitional arrangement in paragraph 8.5 of Schedule 1 to the Financial Services (Exemption) Regulations 2011;\n"
    "\n"
    '"payment instrument" means any -\n'
    "(a) personalised device; or\n"
    "(b) personalised set of procedures agreed between the payment service user and the payment service provider,\n"
    "used by the payment service user in order to initiate a payment order;\n"
    "\n"
    '"payment order" means any instruction by a payer or a payee to their respective payment service provider requesting the execution of a payment transaction;\n'
    "\n"
    '"payment services" means any of the following activities when carried out as a business activity -\n'
    "(a) services enabling cash to be placed on a payment account together with all of the operations required for operating a payment account;\n"
    "(b) services enabling cash withdrawals from a payment account together with all of the operations required for operating a payment account;\n"
    "(c) the execution of the following types of payment transaction -\n"
    "(i) direct debits, including one-off direct debits;\n"
    "(ii) payment transactions executed through a payment card or a similar device;\n"
    "(iii) credit transfers, including standing orders;\n"
    "(d) the execution of the following types of payment transaction where the funds are covered by a credit line for the payment service user -\n"
    "(i) direct debits, including one-off direct debit,\n"
    "(ii) payment transactions executed through a payment card or a similar device;\n"
    "(iii) credit transfers, including standing orders;\n"
    "(e) issuing payment instructions or acquiring payment transactions;\n"
    "(f) money remittance;\n"
    "(g) the execution of payment transactions where the consent of the payer to execute the payment transaction is given by means of any telecommunication, digital or IT device and the payment is made to the telecommunication, IT system or network operator acting only as an intermediary between the payment service user and the supplier of the goods or services;\n"
    "\n"
    '"payment service provider" means any of the following persons when they carry out payment services -\n'
    "(a) deposit takers;\n"
    "(b) issuers of electronic money;\n"
    "(c) the Isle of Man Post Office;\n"
    "(d) payment institutions;\n"
    "(e) the Isle of Man Treasury, the European Central Bank and the national central bank of any EEA State, other than when acting in their capacity as a monetary authority or carrying out other functions of a public nature; and\n"
    "(f) Departments, Statutory Boards and local authorities, other than when carrying out functions of a public nature;\n"
    "\n"
    '"payment service user" means a person when making use of a payment service in the capacity of a payer or payee, or both;\n'
    "\n"
    '"payment transaction" means an act, initiated by the payer or payee, or on behalf of the payer, of placing, transferring or withdrawing funds, irrespective of any underlying obligations between the payer and payee;\n'
    "\n"
    '"person" includes any body of persons, whether incorporated or unincorporated, as well as an individual;\n'
    "\n"
    '"personal pension scheme" means a scheme or arrangement which is not an occupational pension scheme and which is comprised of one or more instruments or agreements, having or capable of having effect so as to provide benefits to or in respect of people -\n'
    "(a) on retirement;\n"
    "(b) on having reached a particular age; or\n"
    "(c) on termination of service in an employment;\n"
    "\n"
    '"private company" means a company which is prohibited by the law of the country or territory in which it is incorporated from making an offer (either in that country or territory or elsewhere) to the public or inviting any section of the public to subscribe for share in or debentures of the company, and also for the purposes of this Order includes a company registered under the Companies Act 2006 that does not offer its shares or debentures to the public;\n'
    "\n"
    '"professional dealer" means any person who -\n'
    "(a) is a market maker in investments; or\n"
    "(b) regularly solicits members of the public (whether in the Island or elsewhere) to deal in investments;\n"
    "and for this purpose “market maker”, in relation to an investment of any description, means a person who (otherwise than in his capacity as the manager or administrator of a collective investment scheme) holds himself out as able and willing to enter into transactions of buying or selling investments of that description at prises determined by him generally and continuously rather than in respect of each particular transaction;\n"
    "\n"
    '"property" includes the currency of any country or territory;\n'
    "\n"
    '"pure protection contract" means a long term insurance contract in respect of which the following conditions are met -\n'
    "(a) the benefits are payable only on death or in respect of incapacity due to injury, sickness or infirmity;\n"
    "(b) there is no surrender value or the consideration consists of a single premium and the surrender value does not exceed that premium; and\n"
    "(c) there is no provision for its conversion or extension in a manner that would result in its ceasing to comply with (a) or (b) of this definition;\n"
    "\n"
    '"registered legal practitioner" means a person who is entered in the register maintained under the Legal Practitioners Registration Act 1986;\n'
    "\n"
    '"restricted depositor" means -\n'
    "(a) a body corporate;\n"
    "(b) an individual (in his personal capacity and not as trustee or nominee) who certifies that he has a minimum of £500,000 net worth excluding -\n"
    "(i) his home or any money raised through a loan secured on that property; and\n"
    "(ii) any rights under a contract of insurance; and\n"
    "(iii) any benefits (in the form of pensions or otherwise) which are payable on the termination of his service or on his death or retirement and to which he or his dependants are or may be entitled; or\n"
    "(c) an individual who is a trustee of a particular trust, who certifies that that the assets of that trust are valued at a minimum of £500,000, excluding real property that is any person’s principal place of residence that -\n"
    "(i) certifies their confirmation of understanding that deposits placed with a class 1(2) deposit taker do not benefit from a compensation scheme; and\n"
    "(ii) for the avoidance of doubt, in the case of deposits held jointly, each depositor must meet one of the above criteria in their own right;\n"
    "\n"
    '"retirement benefits scheme" has the same meaning as in the Retirement Benefits Scheme Act 2000 regardless of any exceptions contained in the Retirement Benefits Schemes (Excepted Schemes) Regulations 2001;\n'
    "\n"
    '"the Rule Book" means the rules, or any part of the rules, made by the Authority under section 18 of the Act;\n'
    "\n"
    '"securities" means shares, debentures, warrants or certificates representing securities and any rights to or interests in such securities;\n'
    "\n"
    '"sell" means dispose of for valuable consideration;\n'
    "\n"
    '"share" a share, including stock, in the share capital of a company;\n'
    "\n"
    '"share warrant" means an instrument entitling the holder to, or to subscribe for shares;\n'
    "\n"
    '"specified person" means a person who -\n'
    "(a) is an advocate or firm of advocates; or\n"
    "(b) is a registered legal practitioner or a firm of registered legal practitioners;\n"
    "(c) is a member of one of the following bodies -\n"
    "(i) the Institute of Chartered Accountants in England and Wales;\n"
    "(ii) the Institute of Chartered Accountants of Scotland;\n"
    "(iii) the Institute of Chartered Accountants in Ireland; or\n"
    "(iv) the Association of Chartered Certified Accountants;\n"
    "\n"
    '"trust" means a legal relationship which falls within Article 2 of the Convention set out in Schedule to the Recognition of Trusts Act 1988, whether such relationship was created in, or under the law of, Island or any other country or territory;\n'
    "\n"
    '"trust bank account" means an bank account held by a trustee or a trust which -\n'
    "(a) holds, and is intended to hold, trust money of that trust (and no other money), and\n"
    "(b) is segregated from any account holding money which is not trust money of that trust.\n"
    "\n"
    '"trust money" means money, forming part of all of the assets of a trust, which a person holds or receives as, or as agent or nominee of, a trustee of that trust;\n'
    "\n"
    '"units" (in relation to a collective investment scheme) has the same meaning as in the Collective Investments Schemes Act 2008;\n'
    "\n"
    '"unit trust scheme" has the same meaning as in the Collective Investments Schemes Act 2008;\n'
    "\n"
    '"warrant" includes -\n'
    "(a) a share warrant,\n"
    "(b) a debenture warrant, or\n"
    "(c) an instrument entitling the holder to, or to subscribe for, a government security.\n"
)


RAO_REPLACEMENT_DICT = {
    "## **4** \n\n## **Regulated": "## **4 Regulated",
    "12 1996 c.4 \n\n c ": "",
    "> 7 2006 c.13 8 2011 c \n\n9 VIII p.327 ": "",
    "> 5 2008 c.16 6 2008 c.14 ": "",
    "## Article 3. ": "",
    # header minipulation
    "## **SCHEDULE 1** ": "## **SCHEDULE 1 - REGULATED ACTIVITIES**",
    "## **REGULATED ACTIVITIES** ": "",
}


def rao_text_text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = strip_footnote_markers(text)
    text = replace_section(
        text,
        "## **INTERPRETATION**",
        "## **PART 2 -FURTHER",
        PART_1_FLATENED_TABLE,
    )
    text = replace_from_dict(text, RAO_REPLACEMENT_DICT)
    return text


RaoTrimmer = SectionMarkers(
    start=starts_with(["## **3 Interpretation"]),
    end=starts_with(["- (4) In determining for the"]),
)

RaoDefMarkers = SectionMarkers(
    start=starts_with(['"accommodation address facilities" means']),
    end=starts_with(["(c) an instrument entitling"]),
)

RaoDefTools = DefinitionTools(
    section_markers=[RaoDefMarkers],
    is_definition_line=starts_with(['"']),
    is_double_def_line=base_double_def_line,
    is_false_dub_def=base_false_double_def,
)

RaoSplitters = ChunkSplitters(
    primary=split_on_bracketed_num, fallback=split_on_paragraph
)

Rao = ToolBelt(
    document="The Regulated Activities Order 2011",
    hierarchy="secondary legislation",
    input_url="https://legislation.gov.im/cms/images/LEGISLATION/SUBORDINATE/2011/2011-0884/2011-0884_8.pdf",
    pdf_path=PROJECT_ROOT / "data/raw/custom/regulated_activities_order.pdf",
    use_ocr=True,
    pdf_handlers=None,
    trimmer=RaoTrimmer,
    header_matchers=[
        lambda line: (
            line.startswith("## **SCHEDULE")
            or line.startswith("## **")
            and line[5].isdigit()
        ),
        starts_with(["## **CLASS"]),
        starts_with(["## **Regulated activities", "## **Exclusion", "## **PART"]),
        starts_with(["## _", "_"]),
    ],
    definition_tools=RaoDefTools,
    clean_text=rao_text_text_cleaner,
    re_pack_splitters=RaoSplitters,
    clean_body=base_body_cleaner,
    clean_header=base_header_cleaner,
    min_body_len=40,
)
