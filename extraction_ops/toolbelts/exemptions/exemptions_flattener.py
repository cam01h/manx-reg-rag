EXEMPTIONS_DEFINITION_TABLE = """|**_Expression_**|**_Definition_**|
|---|---|
|the Authority|means the Isle of Man Financial Services Authority;|
|company|includes any body corporate, whether constituted<br>under the law of the Island or elsewhere;|
|composition or scheme of<br>arrangement|includes a deed of arrangement within the meaning<br>of section 78 of the BankruptcyCode 1892;|
|the Commission|[Revoked]|
|director|has the same meaning as in the Act but also<br>includes -<br>(a) an alternate director; and<br>(b) in relation to a limited partnership which has<br>elected to have legal personality, an individual who is<br>ageneralpartner;|
|electronic money|has the same meaningas in the Order;|
|Group|has the same meaningas in the Act;|
|joint board|has the same meaning as in the Local Government<br>Act 1985;|
|licenceholder|means the holder of a licence issued under section 7<br>of the Act;|
|licensed|means licensed under section 7 of the Act;|
|nominee company|means a company whose sole activity is to hold as<br>nominee or bare trustee monies or investments<br>beneficiallyowned byotherpersons;|
|overseasperson|has the same meaningas in the Order;|
|payment institution|has the same meaningas in the Order;|
|payment services|has the same meaningas in the Order;|
|person|includes any body of persons, whether incorporated<br>or unincorporated,as well as an individual;|
|receiver of a patient|means a receiver of a patient appointed, or treated as<br>if appointed, under Part 7 of the Mental Health Act<br>1998, and includes a person acting by the authority. of<br>a judge of the High Court or the Attorney General<br>pursuant to the said Part 7;|
|registered legal practitioner|means a person who is entered in the register<br>maintained under the Legal Practitioners Registration<br>Act 1986|
|regulator|means a person (whether or not a public authority)<br>whose functions are or include the regulation in a<br>country or territory outside the Island of activities<br>which would be regulated activities if they were<br>carried on in or from the Island;|
|regulated entity|regulated entity means a company which is -<br>(a) licensed under the Act;<br>(b)authorised under section 8 of the Insurance Act|



||2008;<br>(c) the holder of a permit issued under section 22 of<br>the Insurance Act 2008;<br>(d) registered under section 23 of the Insurance Act<br>2008;<br>(e) registered under section 36(1) of the Retirement<br>Benefits Schemes Act 2000;<br>(f) a trustee of a retirement benefits scheme that is<br>registered as authorised or recognised under the<br>Retirement Benefits Schemes Act 2000; or<br>(g) regulated by the Isle of Man Gambling<br>Supervision Commission;|
|---|---|
|the Rule Book|means the rules, or any part of the rules, made by the<br>Authorityunder section 18 of the Act;|
|specified person|means a person who -<br>(a) is an advocate or firm of advocates; or<br>(b) is a registered legal practitioner or a firm of<br>registered legal practitioners;<br>(c) is a member of one of the following bodies -<br>(i) the Institute of Chartered Accountants in England<br>and Wales;<br>(ii) the Institute of Chartered Accountants of<br>Scotland;<br>(iii) the Institute of Chartered Accountants in Ireland;<br>or<br>(iv) the Association of Chartered Certified<br>Accountants.|
|trustee in bankruptcy|means a trustee appointed under section 7(1) of the<br>Bankruptcy Code 1892, and includes an official<br>trustee nominated to act as trustee under that section.|"""


EXEMPTIONS_DEFINITION_TABLE_FLAT = """
- "the Authority" means the Isle of Man Financial Services Authority;
- "company" includes any body corporate, whether constituted under the law of the Island or elsewhere;
- "composition or scheme of arrangement" includes a deed of arrangement within the meaning of section 78 of the Bankruptcy Code 1892;
- "director" has the same meaning as in the Act but also includes -
    - (a) an alternate director; and
    - (b) in relation to a limited partnership which has elected to have legal personality, an individual who is a general partner;
- "electronic money" has the same meaning as in the Order;
- "Group" has the same meaning as in the Act;
- "joint board" has the same meaning as in the Local Government Act 1985;
- "licenceholder" means the holder of a licence issued under section 7 of the Act;
- "licensed" means licensed under section 7 of the Act;
- "nominee company" means a company whose sole activity is to hold as nominee or bare trustee monies or investments beneficially owned by other persons;
- "overseas person" has the same meaning as in the Order;
- "payment institution" has the same meaning as in the Order;
- "payment services" has the same meaning as in the Order;
- "person" includes any body of persons, whether incorporated or unincorporated, as well as an individual;
- "receiver of a patient" means a receiver of a patient appointed, or treated as if appointed, under Part 7 of the Mental Health Act 1998, and includes a person acting by the authority of a judge of the High Court or the Attorney General pursuant to the said Part 7;
- "registered legal practitioner" means a person who is entered in the register maintained under the Legal Practitioners Registration Act 1986;
- "regulator" means a person (whether or not a public authority) whose functions are or include the regulation in a country or territory outside the Island of activities which would be regulated activities if they were carried on in or from the Island;
- "regulated entity" means a company which is -
    - (a) licensed under the Act;
    - (b) authorised under section 8 of the Insurance Act 2008;
    - (c) the holder of a permit issued under section 22 of the Insurance Act 2008;
    - (d) registered under section 23 of the Insurance Act 2008;
    - (e) registered under section 36(1) of the Retirement Benefits Schemes Act 2000;
    - (f) a trustee of a retirement benefits scheme that is registered as authorised or recognised under the Retirement Benefits Schemes Act 2000; or
    - (g) regulated by the Isle of Man Gambling Supervision Commission;
- "the Rule Book" means the rules, or any part of the rules, made by the Authority under section 18 of the Act;
- "specified person" means a person who -
    - (a) is an advocate or firm of advocates; or
    - (b) is a registered legal practitioner or a firm of registered legal practitioners;
    - (c) is a member of one of the following bodies -
        - (i) the Institute of Chartered Accountants in England and Wales;
        - (ii) the Institute of Chartered Accountants of Scotland;
        - (iii) the Institute of Chartered Accountants in Ireland; or
        - (iv) the Association of Chartered Certified Accountants.
- "trustee in bankruptcy" means a trustee appointed under section 7(1) of the Bankruptcy Code 1892, and includes an official trustee nominated to act as trustee under that section."""


def flatten_exemptions_table(text: str) -> str:
    return text.replace(EXEMPTIONS_DEFINITION_TABLE, EXEMPTIONS_DEFINITION_TABLE_FLAT)
