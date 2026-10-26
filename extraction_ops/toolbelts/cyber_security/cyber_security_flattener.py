from extraction_ops.toolbelts.shared_funcs import replace_section

# Appendices 1 and 2 are tables that run over several pages. pymupdf4llm splits cells across
# pages, shares one comments cell between rows and drops list markers, so both are rewritten
# by hand from the PDF. Appendix 1 sections become "### " sub-headers; the wording is the
# Authority's. Appendix 3 is rewritten because the URLs break over lines.

GLOSSARY = """- "Authority" Isle of Man Financial Services Authority
- "CGC2010" Corporate Governance Code of Practice for Regulated Insurance Entities (applicable to insurance managers)
- "CGC2020" Insurance Intermediaries (Corporate Governance)(General Business) Code 2020 (applicable to insurance intermediaries)
- "CGC2021" Corporate Governance Code of Practice for Insurers 2021 (applicable to authorised insurers and permit holders)
- "CISA2008" Collective Investment Schemes Act 2008
- "FSA2008" Financial Services Act 2008
- "IA2008" Insurance Act 2008
- "RBSA2000" Retirement Benefits Schemes Act 2000
- "Rule Book" Financial Services Rule Book 2016

"""

_APPENDIX_1_TABLE_FLAT = """[Editors note: the below is a flattened table]

Each section lists the relevant Rule Book and Corporate Governance Code (CGC) provisions, a summary of them and the Authority's comments.

### **1. Cyber Security Framework & Governance**

Rule Book: Rule 8.2. CGC: CGC2010: Para 3.3; CGC2020: Para 7; CGC2021: Para 7.

Summary: The Rule Book, sections 17A and 27D of the IA2008 and the CGC2010, the CGC2020 and the CGC2021 contain provisions that broadly require regulated entities to have in place appropriate arrangements for effective corporate governance.

Comments:

- Sound governance is key to the effective management of all forms of risk, including cyber risks.
- In particular, the engagement and commitment of the board and senior management is essential, as this will help to create organisation-wide support for cyber risk management and enable appropriate resources and expertise to be made available to address cyber risks.
- Examples of best practices include -
  - promotion of organisation-wide support for cyber risk management by the board;
  - regular inclusion of cyber security on board agendas;
  - appointment of someone suitably senior within the organisation to be responsible for cyber security matters. This could, for example, be a senior manager with appropriate knowledge and experience or a board member who has received appropriate training;
  - establishing the risk tolerance of the firm and overseeing the design, implementation and effectiveness of a cyber security framework which is tailored to the nature, size, complexity, risk profile and culture of the business;
  - articulating lines of reporting and escalation.

### **2. Risk, Controls and Monitoring**

2.1 Rule Book: Rules 8.3 and 8.6. CGC: CGC2010: Paras 7.12, 7.13, 9, 15, 16 and 17; CGC2020: Paras 24 and 26; CGC2021: Paras 9, 36, 37, 42 and Part 11 and Part 12.

Summary: The Rule Book, the CGC2010, the CGC2020 and the CGC2021 contain provisions that broadly require applicable regulated entities to establish and maintain an effective risk management framework for managing the risks associated with their business, including all operational risks, as well as a requirement to establish and maintain appropriate internal controls relating to all aspects of their business. These provisions also require applicable regulated entities to monitor the relevant risks on an ongoing basis.

2.2 Rule Book: Rules 3.37(6), 8.3(2)(h) and 8.6(4)(a)(iii). CGC: CGC2010: Paras 5.7 and 7.11(c); CGC2020: Paras 24(2)(d), (e) and (f); CGC2021: Paras 13, 14, 35(c) and 73(2)(f).

Summary: There are also a number of specific provisions in the Rule Book, the CGC2010, the CGC2020 and the CGC2021 in relation to safeguarding data and assets.

2.3 Rule Book: Rule 8.3(4)(a). CGC: CGC2010: Paras 5.6, 7.1(d), 9(a) to (c), 12.3(b) and (c), 13.4, 16.2(b), and 17(c); CGC2020: Paras 9 and 24(4) and (5); CGC2021: Paras 12, 26(4), 42(a) to (c), 50(2)(b) and (c), 55, 68(1)(b), 69(c) and 73(1).

Summary: The Rule Book contains provisions which require regulated entities to ensure staff and others who conduct regulated activities that they are responsible for are suitable, adequately trained, properly supervised and do not exceed any limitations placed on those persons. Similarly, the CGC2010, the CGC2020 and the CGC2021 require regulated entities to have an appropriate level of management, with adequate and competent staffing and resources, that provides for its sound and prudent management. There are also provisions in the CGC2010 and the CGC2021 which broadly require regulated entities to establish, implement and maintain internal strategies, policies and procedures in order to ensure that the regulated entity complies with its legal and regulatory obligations, including provisions which require various levels of oversight, checks and balances, and, where appropriate, training for staff.

Comments:

- Where relevant legal and regulatory requirements apply, the Authority expects regulated entities to -
  - identify and assess risks associated with IT vulnerabilities such as cyber attacks as part of their risk management framework;
  - implement appropriate and effective controls, for example systems, policies, procedures and training initiatives, to help protect against and manage the risks associated with cyber attacks;
  - proactively monitor activity within your network to detect potential cyber incidents;
  - review, and where appropriate revise, the controls associated with cyber threats at appropriate intervals.
- Former and current employees, contractors, consultants and third party service providers can be a significant source of cyber incidents (which may be deliberate or unwittingly facilitated), therefore this should be taken into account within the risk management framework and associated internal controls.
- Cyber criminals also often target consumers directly, for example by using 'phishing' emails and emulating unsecured Wi-Fi facilities in public places. Therefore, the cyber risks associated with such practices should also be taken into account.
- Examples of best practices include -
  - identification of functions, activities, systems, assets, information, products and services - including interconnections, dependencies and third parties - prioritising their relative importance, and assessing their respective cyber risks;
  - implementation of appropriate policies and procedures, including procedures to verify the legitimacy of all requests received by all methods of communication (the verification procedures should require the verification of all details, for example, including the beneficiary's name and bank details rather than just the amount in relation to payment requests);
  - management and control of user privileges, control of removable media usage, and monitoring of mobile and home working procedures;
  - ensuring that systems are secure, for example, by keeping operating systems, software and web browsers up to date, installing anti-virus solutions on all systems, backing up important information on a regular basis (it is advisable to store backup files in a secure offsite location), and ensuring that mobile devices with access to their systems are secure (e.g. via encryption and password protection using strong passwords);
  - monitoring the use of all equipment and IT systems to detect anomalies and events indicating a potential cyber incident;
  - ongoing cyber awareness and training initiatives to ensure that staff understand the risks associated with cyber attacks and the procedures that have been put in place to mitigate the risks associated with the same;
  - if a firm is involved in payment card processing or it stores, processes or transmits cardholder data and/or sensitive authentication data, it should consider the best practices set out in the Payment Card Industry (PCI) Data Security Standard;
  - conducting cyber security tests, for example penetration testing of systems (firms may wish to consider engaging the services of an external specialist to carry out such tests);
  - keeping up to date on current cyber threats and where appropriate revising controls accordingly - being alert and responsive to new cyber threats is crucial given the escalating risks that cyber threats pose.

### **3. Outsourcing**

3.1 Rule Book: Rule 8.16. CGC: CGC2010: Paras 7.1, 7.5 and 10; CGC2020: Para 30; CGC2021: Paras 26, 30 and 43.

Summary: Provisions in the Rule Book, the CGC2010, CGC2020 and the CGC2021 also contain a number of requirements in relation to outsourcing and delegation.

Comments:

- Where the relevant provisions require a written agreement between the regulated entity and the service provider, that agreement should include the respective responsibilities of the parties to it. Consequently, such an agreement may need to include provisions dealing with each respective parties responsibilities relating to IT security.
- Whether an activity constitutes a material management or business function/significant outsourced function will depend, for example, on the nature of the business concerned and the services that have been outsourced. However, the significance of the risks that service providers pose is not necessarily proportionate to the materiality of the service that is outsourced or delegated. Therefore, the risks in relation to all outsourced services and delegated functions should be managed as part of the broader risk management framework, for example by taking measures to prevent access to systems and confidential data or taking appropriate measures to determine that service providers have appropriate and adequate cyber security standards and procedures in place to protect assets and client related information.
- In relation to delegations which are subject to rule 8.16(1) of the Rule Book, the Authority may, in appropriate cases, consider whether a licenceholder has taken such appropriate measures prior to granting consent.

### **4. Contingency Planning & Incident Response**

4.1 Rule Book: Rule 8.14(1). CGC: CGC2010: Para 5.10; CGC2020: Para 13; CGC2021: Para 16.

Summary: Provisions in the Rule Book, the CGC2010, CGC2020 and the CGC2021 broadly require applicable regulated entities to establish and maintain appropriate business resumption and contingency arrangements.

Comments:

- Where relevant legal and regulatory requirements apply, regulated entities ought to have in place business resumption and contingency arrangements which would enable them to suitably respond to, and recover quickly from, a successful cyber attack.
- The associated policies and controls should clearly set out decision making responsibilities, define escalation procedures and establish processes for communicating with appropriate stakeholders (see also reporting incidents below).
- In the event that a cyber incident occurs, the response should also involve an assessment of scope, nature and impact of the incident and steps to contain and mitigate the impact of it, including removing any ongoing threat such as malware.
- The response and recovery plans should also take into account the fact that communication methods such as email may not be operational.
- The resumption and contingency arrangements should be tested and reviewed at appropriate intervals in order to make contingency planning effective.
- Recovery should include remediating vulnerabilities to prevent similar incidents occurring in future.

### **5. Reporting Incidents**

5.1 Rule Book: Rules 8.17(1), 8.18(1), 8.20 (2)(a) and (i), and 8.30(b). CGC: CGC2010: Paras 18, 17(a) and 20; CGC2020: Paras 29 and 31; CGC2021: Paras 69(a)(i), 71 and 75.

Summary:
- A number of provisions in the Rule Book, the CGC2010, the CGC2020 and the CGC2021 and the RBSA2000 require certain matters to be reported to the Authority.
- For example, the Rule Book requires a licenceholder to notify the Authority, inter alia, where it has reason to believe that an employee is involved in fraud or it becomes aware that fraud has been committed by a third party and it may be material to the safety, soundness or reputation of the licenceholder, certain breakdowns of computer systems, the material loss of consumer or other data, and any material breach of the regulatory requirements. The Rule Book also requires licenceholders to promptly inform the Authority of anything relevant to the exercise of its regulatory functions.
- Similarly, the CGC2010, the CGC2020 and the CGC2021 provide that a regulated entity must establish, implement and maintain adequate and appropriate policies and procedures in respect of reporting fraud to the appropriate authorities, and to encourage the reporting of any other improper or unlawful behaviour. In addition, the relevant Codes also require the regulated entity to maintain open, honest and timely communications with the Authority; and the CGC2021 includes a specific requirement to notify the Authority of anything which the Authority would reasonably expect to have notice of having regard to its regulatory objectives.

Comments:

- Regardless of regulatory requirements, the Authority expects regulated entities to promptly notify the Authority of any serious or significant incident involving data loss, financial loss, disruption to services or denial of services type attacks.
- Regulated entities should also notify the Authority of any serious or significant attacks (of which they are aware) that were prevented.
- Information sharing provides numerous benefits, including helping the Authority to gain a better understanding of the cyber security landscape and, where appropriate, facilitating the sharing of anonymised cyber security information among industry participants in the Island. Ultimately, sharing information may reduce systemic risks by enabling regulated entities to quickly and effectively react to a cyber threat.

### **6. Insurance Cover**

6.1 Rule Book: Rule 8.57(3) Regulation 7 Insurance Intermediaries (General Business) Regulations 2020. CGC: No specific provisions in the CGC2010 or CGC2021. However, please see the summary and comments opposite, and note that regulated entities' own insurance arrangements form part of their wider operational risk management.

Summary: Rule 8.57(3) of the Rule Book and regulation 7 of the Insurance Intermediaries (General Business) Regulations 2020 require certain licenceholders and insurance intermediaries to maintain a minimum level of professional indemnity insurance ('PII') cover.

Comments:

- PII cover may sometimes include cyber liability cover, however, cyber liability cover is not a regulatory requirement.
- Nonetheless, given that cyber security measures may not prevent all cyber attacks, this could be something that regulated entities may wish to consider as part of their overall risk management framework.

### **7. Stakeholder Interests**

7.1 Rule Book: Rules 6.5(1) and 8.3(2)(c). CGC: CGC2010: Paras 5.4, 7.7(c), 7.11(b)(iii), 7.15(c), 8(b), 9(c)(iii), 10(d)(iii) and 19; CGC2020: Paras 10, 24(1),24(2)(a) and (c) and 30(e)(iii); CGC2021: 9(1)(b)(iv), 31(c), 35(b)(iii), 38(d), 39(a), 41(d) and (e), 42(a)(ii) and (c), 43(e)(iii), 73 and 74.

Summary:
- The Rule Book provides that a licenceholder must not carry on business of such a kind or in such a way as may be likely to bring the Island into disrepute or damage its standing as a financial centre.
- The Rule Book also contains' provisions which require internal controls to ensure the fair treatment of clients.
- Similarly, the CGC2010, the CGC2020 and the CGC2021 provide that a regulated entity must have due regard for the interests of its stakeholders and treat them fairly. In support of the foregoing, the relevant Codes include provisions which require the adoption of appropriate standards of conduct, effective communication systems and an internal corporate culture which promotes the fair treatment of stakeholders. There are also further provisions which relate specifically to the fair treatment of policyholders.

Comments:

- Successful cyber attacks have the potential to cause significant and long term detriment to affected clients.
- Successful cyber attacks also have the potential to undermine confidence in the Island's financial services sector as a whole.
- Therefore, relevant regulated entities should ensure that these factors are taken into account within their governance arrangements and risk management framework in the context of cyber risks.

"""

_APPENDIX_2_FLAT = """## **Appendix 2 - Examples of cyber security incidents**

### **Example 1 - Payment Requests**

[Editors note: the below is a flattened table]

What happened?

- Several incidents in the Island have involved regulated entities receiving fraudulent payment requests by email after clients' email accounts had been hacked.
- In another case, an employee of a regulated entity had their email account hacked and the hacker placed an auto forward rule on the employee's email account to enable monitoring over a period of time. When a client sent a number of genuine payment requests by email to the employee whose account had been hacked, the genuine payment requests were deleted by the hacker and substituted with fraudulent payment requests sent from an almost identical email address to that of the client and the requested payment amounts were the same as those in the original emails, but the beneficiary name and bank account details had been changed.
- A number of payments ranging from £20,000 to over £1,000,000 were made by the affected regulated entities.

What was the impact?

- Many of the payments have never been recovered or were only partially recovered.

How can these types of incidents be prevented?

- There are various steps that firms can take that may help to prevent these types of incidents, including having procedures (such as call back procedures) in place to verify the legitimacy of requests.
- Ideally, the legitimacy of all requests should be verified.
- Otherwise verification procedures should establish appropriate triggers, for example transfers to unfamiliar accounts. Also, when establishing triggers (e.g. amount thresholds), regulated entities should also consider that sometimes frauds may be carried out as a series of transactions and the value of each individual transaction may be relatively low.
- Also, all of the details should be verified (e.g. the beneficiary's name and bank details rather than just the amount, as a fraudulent payment request may replicate the amount in a genuine payment request).
- As well as establishing and implementing appropriate verification procedures, cyber security awareness training and procedures to verify that employees are following the procedures that have been put in place to mitigate the risks associated with cyber threats can help to reduce the risk of non-compliance therewith.


### **Example 2 - Information Request**

[Editors note: the below is a flattened table]

What happened?

- A fraudster created an email address which was almost identical to the firm's own (one letter of the email address was different, but the fraudster used the similarity between some letters in certain fonts to create an email address which looked almost the same as the firm's own).
- The fraudster then attempted to obtain confidential information from a member of staff by posing as a colleague.

What was the impact?

- No funds were lost, however a data protection breach occurred.

How can this type of incident be prevented?

- Again, this type of incident might be prevented, for example, by having appropriate procedures in place to verify the legitimacy of requests.


### **Example 3 - Ransom Demand**

[Editors note: the below is a flattened table]

What happened?

- A regulated entity received a ransom note from an organised cyber-crime group who attempted to extort money from the firm by threating to subject it to a substantial and sustained distributed denial of service attack ('DDoS') due to start imminently thereafter.
- On the same day that the ransom note was received, the firm escalated the matter to its IT Security & Risk Team. The firm also immediately notified its cyber insurers who were able to provide support. In addition, the firm carried out a review to assess its technical defences and service impacts, scope of impact, legal implications and regulatory and law enforcement notifications.
- The firm already had DDoS protection through a third party service provider; however, as a consequence of the ransom note, it brought forward a planned changeover to DDoS protection with another service provider in order to provide greater resilience to future attacks.
- The firm ensured that a response team was available over the weekend when the attack was expected.
- The firm's crisis team also held regular meetings to monitor the situation and ensure appropriate actions were in place to mitigate the risk. The firm also considered the possibility that the DDoS threat was being used as a distraction technique.
- Thereafter, the firm reported the incident to the Authority and Action Fraud and continued to closely monitor the situation.

What was the impact?

- None (there was no data breach or interruption to services).

How can this type of incident be prevented or mitigated?

- There are various steps that firms can take that may help to prevent these types of incidents from occurring or help to mitigate their impact if they do occur, including having adequate and effective business resumption and contingency arrangements in place which would enable them to suitably respond to, and recover quickly from, a successful cyber attack.
- In the event that a cyber incident occurs, the response should include taking appropriate steps to contain and mitigate the impact of it, including removing any ongoing threat such as malware.
- See section 4 of the table in Appendix 1 for further details regarding contingency planning and incident response.

"""

_APPENDIX_3_FLAT = """## **Appendix 3 - Other resources**

- European Central Bank (2016) G7 fundamental elements for cyber security - https://www.ecb.europa.eu/paym/pol/shared/pdf/G7_Fundamental_Elements_Oct_2016.pdf
- Gov.uk: Cyber security guidance for business - https://www.gov.uk/government/collections/cyber-security-guidance-for-business
- International Association of Insurance Supervisors: Issues Paper on Cyber Risk to the Insurance Sector - http://www.iaisweb.org/page/supervisory-material/issues-papers/file/61857/issues-paper-on-cyber-risk-to-the-insurance-sector
- International Organization of Securities Commissions (2016) Cyber Security in Securities Markets - An International Perspective - https://www.iosco.org/library/pubdocs/pdf/IOSCOPD528.pdf
- International Organization of Securities Commissions (2016) Guidance on cyber resilience for financial market infrastructures - https://www.iosco.org/library/pubdocs/pdf/IOSCOPD535.pdf
- International Organization of Securities Commissions (2005) Principles on Outsourcing of Financial Services for Market Intermediaries, Topics 2 and 3 - https://www.iosco.org/library/pubdocs/pdf/IOSCOPD187.pdf
- National Association of Corporate Directors (2014) Cyber-Risk Oversight - https://www.nacdonline.org/files/NACD%20Cyber-Risk%20Oversight%20Executive%20Summary.pdf
- National Cyber Security Centre - https://www.ncsc.gov.uk/
- National Cyber Security Centre: Cyber aware - https://www.ncsc.gov.uk/cyberaware/home
- National Cyber Security Centre: Small Business Guide: Cyber Security - https://www.ncsc.gov.uk/collection/small-business-guide
- National Cyber Security Centre: 10 Steps to Cyber Security - https://www.ncsc.gov.uk/collection/10-steps
- National Protection Security Authority - https://www.npsa.gov.uk/
- PCI Security Standards Council: Document Library - https://www.pcisecuritystandards.org/document_library/
- PwC (2016) Turnaround and transformation in cybersecurity: Key findings from The Global State of Information Security Survey 2016 - https://www.pwc.com/sg/en/publications/assets/pwc-global-state-of-information-security-survey-2016.pdf
"""


def flatten_appendices(text: str) -> str:
    # Appendix 1 keeps its two intro paragraphs, only the table is replaced
    text = replace_section(
        text, "|1|Cyber Security", "## **Appendix 2", _APPENDIX_1_TABLE_FLAT
    )
    text = replace_section(text, "## **Appendix 2", "## **Appendix 3", _APPENDIX_2_FLAT)
    appendix_3 = text.find("## **Appendix 3")
    if appendix_3 == -1:
        raise ValueError("Appendix 3 not found")
    return text[:appendix_3] + _APPENDIX_3_FLAT
