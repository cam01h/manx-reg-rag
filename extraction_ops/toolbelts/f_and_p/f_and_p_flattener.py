from extraction_ops.toolbelts.shared_funcs import replace_section

# the tables and the decision tree in the appendices, rewritten from the PDF table cells.
# the Appendix 2 row groups become "## " sub headers so each chunk keeps its group

_APPENDIX_2_TABLE_FLAT = """## Controllers and owners

[Editors note: the below is a flattened table - Controlled Function (type): guidance on role / responsibilities]

- R1. Controllers - of the regulated entity / of its immediate parent / of its ultimate parent company or the ultimate beneficial owner of the regulated entity (notified and accepted): This includes the legal entity that is the immediate parent or ultimate parent of the regulated entity, as well as individuals meeting the definition of controller [Footnote: See s48 FSA2008, s26 IA2008 and s54 RBSA2000] for the regulated entity / its immediate or ultimate parent company of a group structure as well as individuals that are ultimate beneficial owners of the regulated entity.
- R2. Not in use
- R3. Controllers - 'intermediate controllers' - i.e. non-individual controllers that do not meet the description of R1 but nevertheless are within the statutory definition of controller (notified and potentially accepted): These will be 'intermediate controllers' which do not fall within the description at R1; for example, a holding company in the chain of ownership which is neither the regulated entity's immediate nor ultimate parent.

## Members of governing bodies

[Editors note: the below is a flattened table - Controlled Function (type): guidance on role / responsibilities]

- R4A. Executive directors of an Isle of Man incorporated* regulated entity (notified and accepted): This Controlled Function also includes: employees of an Insurance Manager proposed to be directors of a managed insurer (R4A or R4B); employees of a Class 7 licenceholder proposed to be directors of a managed entity (R4A or R4B); members of the management committees of credit unions (R4A); persons proposed as directors of a corporate trustee of an authorised retirement benefits scheme (* whether or not that corporate trustee is incorporated in the IoM) (R4A).
- R4B. Non-independent, non-executive directors of an Isle of Man incorporated* regulated entity (notified and accepted)
- R4C. Independent non-executive directors of an Isle of Man incorporated* regulated entity (please refer to Appendix 10 for guidance on 'Independence') (notified and accepted)
- R5. Members of a governing body of a collective investment scheme (in respect of certain schemes only) (notified and accepted): All members of the governing bodies of collective investment schemes should be fit and proper. However, the Authority only regards those of the following scheme types to be Controlled Functions: Authorised Schemes / Full International Schemes / Regulated Funds / Recognised Funds.
- R6. An individual who is a professional trustee of an authorised retirement benefits scheme (notified and accepted): In this context, professional trustee means a trustee who undertakes this position by way of business.
- R7. An individual trustee who is not a professional trustee of a retirement benefits scheme (notified only)

## Senior management and officers of a regulated entity

[Editors note: the below is a flattened table - Controlled Function (type): guidance on role / responsibilities]

- R8. Chief Executive or Managing Director of an Isle of Man incorporated regulated entity, or the most senior executive in the Isle of Man responsible for a branch of a non-Isle of Man incorporated entity (notified and accepted): NB: A Managing Director will also need to hold an R4A Controlled Function. It is also very likely that a Chief Executive will be a director and thus need to hold an R4A Controlled Function.
- R9. Individual who is the company secretary of an Isle of Man incorporated regulated entity (notified only)
- R10. Key person (notified and accepted): If the Authority considers that a particular individual does not fall within a defined category of Controlled Function, but nevertheless appears to the Authority to have significant powers or responsibilities, then the Authority may require notification of the individual using F&P 1 - Individual Questionnaire, or F&P 3 - Controller Questionnaire (as appropriate), together with further information about their role and responsibilities. This is considered a 'notified and accepted Controlled Function'. This situation is expected to be rare, and can only be utilised by the Authority. A regulated entity cannot determine that an individual is in a notified and potentially accepted Controlled Function.
- R10A. Key person (notified and potentially accepted): If the Authority considers that a particular individual does not fall within a defined category of Controlled Function, but nevertheless appears to the Authority to have significant powers or responsibilities, then the Authority may require notification of the individual using F&P 2 - Notification Only Form, together with further information about their role and responsibilities. This is considered a 'notified only Controlled Function'. This situation is expected to be rare, and can only be utilised by the Authority. A regulated entity cannot determine that an individual is in a notified and potentially accepted Controlled Function.

## Assurance persons of or to a regulated entity

[Editors note: the below is a flattened table - Controlled Function (type): guidance on role / responsibilities]

- R11. Appointed actuary of an insurer under s18 IA2008, or Head of Actuarial Function (notified and accepted): NB. Head of Actuarial Function refers to the individual holding this function for a commercial insurer to whom para 5(1)(b) of the Corporate Governance Code of Practice for Commercial Insurers applies.
- R12. Principal control officer - of an entity regulated under the IA2008 (notified and accepted): This Controlled Function should be used for individuals controlling the exercise of functions within the regulated entity, i.e. a role that fits within the definition of principal control officer ('PCO') set out at section 54 of the IA2008. Despite the following roles being capable of falling within PCO, they have specific competencies attached to them, therefore the more specific Controlled Function should be used rather than R12: Head of compliance (R13) / Head of internal audit (R14) / MLRO (R15) / DMLRO (R16) / Head of Actuarial Function (R11).
- R13. Head of compliance (notified and accepted): The individual responsible for ensuring or monitoring compliance with the regulated entity's legal and regulatory obligations and required to provide objective assessment or objective reporting to the governing body of the regulated entity. In many regulated entities there will only be one compliance officer who will therefore be the Head of compliance, but in larger entities or groups there may be a team and an individual to whom other compliance officers / personnel report. In the case of groups, it is important for the regulated entity to identify the individual who will be / is exercising the functions of "Head of compliance" where this is set down in the relevant legislation. Depending on the structure of the group and the compliance team, this individual may be the one to whom the others report, or may be one of those compliance officers. However, there can be only one individual who holds the Head of compliance Controlled Function per regulated entity. In the case of branches, the Head of compliance will be the most senior individual with compliance responsibility locally, who may have a reporting function to Head Office / Group, but who will also be expected to provide reports to local senior management.

R13. Head of compliance (continued): This Controlled Function will, for example, encompass the individual nominated by certain Class 8 licenceholders under Rule 8.22(3) of the Financial Services Rule Book. Where a regulated entity outsources certain compliance services, please refer to section 11a of this guidance. Where an Insurance Manager is providing management services for an insurer, Head of compliance means an individual working for or on behalf of the insurer who is responsible for the compliance function of that insurer.
- R14. Head of internal audit (notified and accepted): If a regulated entity has an internal audit function, this Controlled Function will be the individual responsible for monitoring compliance with the regulated entity's internal strategies, policies and procedures; legal and regulatory obligations; risk management; or internal control systems and required to provide objective assessment or objective reporting to the governing body of the regulated entity.
- R15. MLRO (notified and accepted)
- R16. DMLRO (notified only): Please note, because the DMLRO is a notified only Controlled Function, if a DMLRO's role is intended to formally change to become MLRO, this will require an F&P 1, because the MLRO is a notified and accepted Controlled Function. However, where a DMLRO deputises in the MLRO's absence no F&P 1 is required.
- R17A. Person responsible for the submission of the regulatory returns to the Authority (notified only): The individual (other than one mentioned at * below) who is responsible for the detail within, and accuracy of, the regulatory returns. * An individual will not be in Controlled Function R17 if they are in any notified and accepted Controlled Function for the SAME regulated entity.
- R17B. Person responsible for the submission of AML/CFT data through STRIX to the Authority (notified only): The individual who is responsible for the submission of AML/CFT data through STRIX to the Authority.

## Other persons of a regulated entity

[Editors note: the below is a flattened table - Controlled Function (type): guidance on role / responsibilities]

- R18. Senior manager with significant influence (notified only): An individual (other than one mentioned at † below) who reports directly to the governing body as a whole, or directly to an individual member of the governing body and is able to exercise significant influence and is responsible for the day to day management of a function which undertakes the regulated business of the regulated entity; in accordance with strategies, policies and procedures set out by the governing body. See Appendix 7 for more guidance. † An individual will not be in Controlled Function R18 if they are in any of the following Controlled Functions for the SAME regulated entity: R1 to R4A, R4B, R8, R10 to R16, R19 to R21A, R22A or B and R28.
- R19. Financial controller (notified and accepted): An individual (other than one mentioned at # below) who is able to exercise significant influence and responsible for the day to day management of the accounting function of the regulated entity in accordance with strategies, policies and procedures set out by the governing body. # An individual will not be in Controlled Function R19 if they are in the Controlled Function of R4A (Executive Director) for the SAME regulated entity.
- R20. Head of operations (notified only): Where they are an individual (other than one mentioned at ~ below) who reports directly to the governing body or directly to an individual member of the governing body and who is able to exercise significant influence. ~ An individual will not be in Controlled Function R20 if they are in the Controlled Function of R4A (Executive Director) for the SAME regulated entity.
- R21. Senior manager with responsibility for persons providing investment or insurance advice (notified and accepted): An individual who is responsible for persons giving investment or insurance advice to clients.
- R21A. Individual providing investment advice to clients (notified and accepted): NB: If an individual already holds Controlled Function R21 for the SAME regulated entity, and takes on R21A subsequently, an F&P 1 is not required, but the regulated entity must notify the supervision team responsible for the entity within the Authority of this additional appointment. Also, the individual may need to obtain additional documentation, such as an IoM Statement of Professional Standing, if one is not already held.
- R21B. Individual providing insurance advice to clients (notified only): NB: This Controlled Function only applies to regulated entities that are registered under the IA2008.

## Branches of non-IOM incorporated regulated entities and non-EU permit holders under the IA2008 / Foreign branches of IoM incorporated entities

[Editors note: the below is a flattened table - Controlled Function (type): guidance on role / responsibilities]

- R22A. Head office personnel who have a clear and direct responsibility for the IoM branch or who will be overseeing the work of that branch (notified and accepted): The term 'branch' also includes a Class 1(3) Representative Office and a non-EU permit holder under the IA2008. Such individuals should be a member of the senior management of the company of which the branch is part, and will often be in a Controlled Function (or similar) in their home jurisdiction.
- R22B. The most senior executive in an overseas jurisdiction, and responsible for a branch in that jurisdiction, of an IoM incorporated entity (notified and accepted): Such individuals should be a member of the senior management of the company of which the branch is part, and will often be in a Controlled Function (or similar) in their host jurisdiction.

## Others, including officers of client entities

[Editors note: the below is a flattened table - Controlled Function (type): guidance on role / responsibilities]

- R23. Director (or equivalent) or company secretary of a client entity of a CSP (notified only)
- R24. Director (or equivalent) or company secretary of a body corporate acting as a director, nominee shareholder or company secretary of a client entity of a CSP (notified only)
- R25. Trustee of a client trust of a TSP (notified only)
- R26. Director (or equivalent) or company secretary of a corporate trustee of a TCSP (notified only)
- R27. Council member of a client foundation of a TCSP (notified only)
- R28. Isle of Man Resident Officer (notified and accepted): Applies to branches of non-IOM incorporated entities only that are regulated under the FSA08.
- R29. Other insurance managers (non-life insurers only) (notified and accepted): Any individual within the IA2008 definition of manager that is not included within any other Controlled Function. Applies to non-life insurers only.

## Insurance group roles (where the Authority is the Group Supervisor)

[Editors note: the below is a flattened table - Controlled Function (type): guidance on role / responsibilities]

- R30. Group Actuary (notified and accepted): See Appendix 9.

"""

# ticks moved into words: "by the regulated entity" / "by the Authority" / both
_APPENDIX_5_TABLE_FLAT = """[Editors note: the below is a flattened table - check (who carries it out)]

Competence:
- Documentary evidence to show the individual fulfils the Training & Competence Framework applicable (if any) for the Controlled Function(s) undertaken (by the regulated entity)
- Declaration within the relevant form that the individual fulfils the Training and Competence Framework requirements for the Controlled Function(s) undertaken (if any) (by the regulated entity)
- Professional body check (where applicable) (e.g. covering issues such as: is memberships held / is it current / has disciplinary action been taken) (by the regulated entity)
- Previous & current employers' references (minimum last 10 years where possible) (by the regulated entity)
- Capacity check (e.g. covering issues such as does the individual have enough time to devote to the role when considering other roles with the regulated entity, as well as other roles held elsewhere) (by the regulated entity)
- Declaration within the relevant form that the individual is able to perform the functions required without being exposed to unmanaged material conflict (by the regulated entity)
- Consideration of the reasonableness of the statement from the regulated entity of why the individual is competent and capable of fulfilling the Controlled Function(s) (by the Authority and the regulated entity)

Integrity:
- Criminal record check (individual) (by the regulated entity - notified and accepted CF only, although good practice in notified only cases too)
- Review of criminal record check data (by the regulated entity - notified and accepted CF only, although good practice in notified only cases too)
- Individual self-certification of all convictions (by the regulated entity)
- Comparison of individual self-certification of all unspent convictions to data from check (by the regulated entity - notified and accepted CF only)
- Review of spent convictions notified to the Authority (by the Authority)
- Search for regulatory actions against individual inc. director disqualifications (by the regulated entity)
- Inter-regulator checks (by the Authority)
- Review of individual's self-certification of all regulatory actions including pending actions and director or officer disqualifications (by the Authority and the regulated entity)
- Consideration of the reasonableness of the statement from the regulated entity of its assessment of the integrity of the individual (by the Authority and the regulated entity)

Financial standing:
- Court judgements search (by the regulated entity)
- Insolvency lists (by the regulated entity)
- Credit check (by the regulated entity)
- Consideration of individual self-certification of judgements etc. (by the Authority and the regulated entity)
- Consideration of the statement from the regulated entity of its assessment of the financial standing of the individual (by the Authority)

General:
- Identity and other due diligence checks (by the regulated entity)
- Consideration of the acceptability of the Controlled Function held by the signatory to the declarations required on behalf of the regulated entity (i.e. sufficiently senior / authorised to sign on behalf of the regulated entity) (by the regulated entity)
- Website checks (by the Authority and the regulated entity)
- Consideration of reasonableness of the declaration of individual that they meet the fitness and propriety standards (by the Authority and the regulated entity)

"""

_APPENDIX_6_TABLE_FLAT = """[Editors note: the below is a flattened table]

- Individual Questionnaire (F&P 1): To be completed when an individual is being proposed for a notified and accepted Controlled Function
- Notification Only Form (F&P 2): To be completed when an individual has been appointed to a notified only Controlled Function
- Controller Questionnaire (F&P 3): To be completed in respect of Controlled Function R1. This form is designed for use by both corporate controllers (Part B), and individuals that are controllers (Part C). For new individual controllers of the ultimate parent company of a captive insurance entity, or Isle of Man branches of overseas regulated entities only, see Appendix 3.
- Intermediate Controller Notification Form (F&P 4): To be completed in respect of Controlled Function R3 (where a proposed acquisition of control will only result in a change of intermediate parent within the regulated entity's group structure, and will not result in a change to the controllers of the regulated entity, its immediate parent or ultimate beneficial owners)
- Individual Controlled Function Cessation Form (F&P 5): To be completed in respect of any individual where a Controlled Function they hold ceases

"""

# the decision tree is an image with no text layer
_APPENDIX_7_FLAT = """## **Appendix 7 - R18 Senior Manager with Significant Influence - Decision Tree**

[Editors note: the below is a flattened diagram]

1. Is the individual in, or taking on, any of the following Controlled Functions for the SAME regulated entity: R1 to R4, R8, R10 to R16, R19 to R21A, R22A or B, and R28? If yes - not an R18. If no - go to 2.
2. Does the individual report directly to either the governing body (Board) as a whole, or directly to an individual who is a member of the governing body (director)? If no - not an R18. If yes - go to 3.
3. Is the individual able to exercise significant influence over regulated business? If no - not an R18. If yes - go to 4.
4. Is the individual responsible for the management of a function that undertakes the regulated business of the regulated entity?* If no - not an R18. If yes - is an R18.

* i.e. the HR function is not considered to be undertaking the regulated business of the regulated entity, as its influence over the regulated business is too far removed.

"""


def flatten_appendices(text: str) -> str:
    text = replace_section(
        text, "|Controlled Functions|Type|", "## **Appendix 3", _APPENDIX_2_TABLE_FLAT
    )
    text = replace_section(
        text, "|Due diligence|", "## **Appendix 6", _APPENDIX_5_TABLE_FLAT
    )
    text = replace_section(text, "|Form Name|", "**Appendix 7", _APPENDIX_6_TABLE_FLAT)
    text = replace_section(text, "**Appendix 7", "## **Appendix 8", _APPENDIX_7_FLAT)
    return text
