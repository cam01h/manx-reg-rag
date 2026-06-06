# **manx-reg-rag**

A Retrieval Augmented Generation tool for Isle of Man Licence holders and Designated Businesses. Make any LLM an expert in financial services legislation and regulation.

## 1. Why did I build this tool?

#### The problem

AIs are trained on vast quantities of data and this training data forms the backbone of their system knowledge where there isn't enough data, there isn't a good basis for system knowledge. Financial Services Regulation and legislation is a complicated field with a wide variety of overlapped sources. Most Isle of Man financial services compliance practitioners will already be aware that LLM's that are prompted regarding specific regulatory requirements will often refer to the UK laws (because its a bigger data set) or less capable models will simply hallucinate.

#### The solution

The ideal way for an AI to call the specific knowledge it needs when lacking system knowledge is through Retrieval Augmented Generation (RAG). This is a well trodden path and far from a new technology but the first time it will be available in an open a free format (free from me at least, you will have to bring your own LLM and if your using an API, you will have to pay for that but I'm afraid).

## 2. How does it work?

#### Caveats

I am a compliance professional by trade and manx-reg-rag is far from complete and currently only prints to the terminal and though in testing I have started getting some high quality answers with citations, this is not a tool ready for implementation by any firm in its current format.

### 2.1 Ingestion of documents

Documents are entered in PDF format and extracted to and md format PyMuPDF4LL. The lines are trimmed and regex is used to clean the md file ready for chunking. The chunking function extracts the text into a jsonl format with rich and descriptive meta data that currently includes:

- the document title
- legal hierarchy (legislation, guidance, etc)
- the major heading (part, chapter, etc.)
- the minor heading (paragraph, sub-section, etc)
- defined terms
- defined terms used (see below)

### 2.2 Definitions

One of the key failings of most RAG projects that tackle legal text is the chunk it served to the LLM without any specific legal definitions attached to the terms used in said chunk. Among the currently accessible documents, all defined terms are also extracted.

### 2.3 Embedding and retrieval

The stack uses a Qdrant vector database. If that means nothing to you, you're not alone — and you don't need to follow the exact mechanics. As a simple metaphor, books can be grouped by subject at a library. For example books on cars and trains are both about transport so they have some semantic similarities so they might be in the same section but maybe not right next to each other. If you had a books about electric cars and hybrid cars, they might be right next to each other. That's essentially what the vector DB is doing, it groups the chunks by semantic similarity. That's roughly what happens here. Every chunk of legislation is read once and given a position — not on a physical shelf, but in a kind of map of meaning. Chunks about similar things end up close together on the map, even when they use different words.

When you ask a question, the question gets a position on the same map. We then grab the chunks sitting nearest to it — the ones most likely to be talking about what you asked.

### 2.4 The response

Once the chunks are retrieved, the chunks are served to the LLM and it can see the chunks and the metadata around those chunks, as well as any definitions required to interpret them and give an evidence based answer grounded in the IOM legislation and guidance it is served with.

The agent is managed via the Pydantic AI ecosystem so the LLM gives a structured response including:

- the text response
- citations: this currently comes in the form of listing the chunks it used and describing the relevance of the chunk and how it used the chunk to answer the question.

## 3. Current state of the project

This is a solo project started in May 2026 and progress will occur as time allows. This is my first full project and feedback is very much welcome from on both the compliance side and the software side.

### 3.1 Documents

Though more will be added in due course, to date there are only two documents ingested and embedded:

- The AML/CFT Code 2019
- The AML Handbook Apr 2026

### 3.2 UI

The output is currently to a terminal but a full GUI will be allowing for the expected prompt and answer will be added in due course.

### 3.3 Usability

Currently OpenAI is hard coded into the project but in due course, it will be model agnostic allowing for a range of cloud and local options.

## 4. Example prompt and answers

### **Example 1**

```
System prompt: You are an expert in Isle of Man financial services regulation that is advising the user on the opperations of an Isle of Man regulated business. For every question, call the retrieval tool first to get relevant chunks from the legislation and guidance. Answer only from the retrieved content — do not draw on outside knowledge. If the retrieved chunks don't contain the answer, say so explicitly rather than guessing. For each chunk you draw on, include a Citation explaining what it contributed to your answer.
Q: what should be included in terms of statistics in my BRA?
A: In your Business Risk Assessment (BRA), you should include several statistical elements:

1. **Findings, Trends, and Vulnerabilities**: Incorporate an assessment of any identified findings, trends, vulnerabilities, and risks associated with your sector as outlined in the Isle's latest National Risk Assessment (NRA). This ensures that your BRA reflects current industry insights and risks.
   - *Citation*: Chapter 2, Section 2.2.8.3 of the AML Handbook highlights the importance of considering sectoral and topical NRAs in the BRA.

2. **Quantitative and Qualitative Information**: Utilize quantitative and qualitative data from both internal and external sources to assess risks appropriately. This should not rely on a single source but rather a variety to capture a comprehensive risk profile.
   - *Citation*: Chapter 2, Section 2.2.4.1.1 illustrates the need for varying information sources, including statistical organizations and academia.

3. **Estimations of ML/FT Risks**: Your BRA should include estimations of the risk of money laundering and financing of terrorism (ML/FT) posed by your business and customers. This encompasses the inherent risks, exposure levels, and probability statistics related to financial crime.
   - *Citation*: Chapter 2, Section 2.2.8 outlines that the BRA should document estimation of the firm's residual risk to financial crime.

4. **Customer Risk Assessments**: Integrate customer risk profiles which include assessment metrics that highlight customer activities, relationship complexities, and any third-party involvement in customer due diligence processes.
   - *Citation*: Chapter 2, Section 2.2.9.2 indicates that the nature, scale, and complexity of customer activities can present higher risks and should be assessed.

5. **Regular Updates and Reviews**: Ensure your BRA is treated as a living document that is regularly updated with new data, findings, and trends to maintain its relevance and effectiveness.
   - *Citation*: Chapter 2, Section 2.2.8 explains the necessity for ongoing reviews of the BRA to keep it current.

By including these statistical elements, your BRA will be well-positioned to reflect the risks associated with your operations effectively and comply with relevant guidelines
-----------------------------

The AML Handbook (April 2026)::Chapter 2 - General Requirements and Risk Based Approach::2.2.8.3 Relevant risk factors::9ec84fed
Highlights the need for assessment based on sectoral NRAs
-----------------------------

The AML Handbook (April 2026)::Chapter 2 - General Requirements and Risk Based Approach Emphasizes the importance of using diverse data sources
-----------------------------

The AML Handbook (April 2026)::Chapter 2 - General Requirements and Risk Based Approach::2.2.8 Business risk assessment ("BRA") Code 5(1) 5 Business risk assessment::232d2490
Describes the need for estimating ML/FT risks
-----------------------------

The AML Handbook (April 2026)::Chapter 2 - General Requirements and Risk Based Approach::2.2.9.2 Relevant risk factors including matters that pose or may pose higher
ML/FT/PF risks::ab5959f3
Discusses assessments related to customer activities that pose risks
-----------------------------

The AML Handbook (April 2026)::Chapter 2 - General Requirements and Risk Based Approach::2.2.8.3 Relevant risk factors::5121cbf5
Mentions the requirement for regular updates to the BRA
==============================
```

#### **Example 2**

```
System prompt: You are an expert in Isle of Man financial services regulation that is advising the user on the operations of an Isle of Man regulated business. For every question, call the retrieval tool first to get relevant chunks from the legislation and guidance. Answer only from the retrieved content — do not draw on outside knowledge. If the retrieved chunks don't contain the answer, say so explicitly rather than guessing. For each chunk you draw on, include a Citation explaining what it contributed to your answer.
Q: What does the position of MLRO entail?
A: The position of the Money Laundering Reporting Officer (MLRO) entails several critical responsibilities as defined in the AML Code 2019. The MLRO must be appointed by a relevant person to oversee essential functions, including:

1. **Senior Position**: The MLRO must be sufficiently senior within the organization or possess adequate experience and authority to fulfill the role effectively (The AML Code 2019, PART 7 – REPORTING AND REGISTERS, 23 Money Laundering Reporting Officer).

2. **Direct Access**: The MLRO must have direct access to the organization's officers to facilitate communication and reporting (The AML Code 2019, PART 7 – REPORTING AND REGISTERS, 23 Money Laundering Reporting Officer).

3. **Time and Resources**: The MLRO should have sufficient time and resources dedicated to discharge their responsibilities (The AML Code 2019, PART 7 – REPORTING AND REGISTERS, 23 Money Laundering Reporting Officer).

4. **External Disclosures**: The MLRO is responsible for all external disclosures, particularly concerning money laundering or financing of terrorism (ML/FT). This includes making disclosures to the Financial Intelligence Unit when necessary (The AML Code 2019, PART 7 – REPORTING AND REGISTERS, 27 External disclosures).

5. **Evaluation of Internal Disclosures**: The MLRO must assess internal disclosures for suspected ML/FT activities and must report externally if there are reasonable grounds for suspicion (The AML Code 2019, PART 7 – REPORTING AND REGISTERS, 27 External disclosures).

6. **Maintain Reporting Procedures**: The MLRO must ensure that robust reporting procedures are maintained within the organization, guiding how employees should report suspicious activities (The AML Code 2019, PART 7 – REPORTING AND REGISTERS, 25 Reporting procedures).

Additionally, organizations may appoint a Deputy MLRO to assist in these duties, especially in the absence of the MLRO (The AML Code 2019, PART 7 – REPORTING AND REGISTERS, 23 Money Laundering Reporting Officer)
-----------------------------

The AML Code 2019::PART 7 – REPORTING AND REGISTERS::23 Money Laundering Reporting Officer::0d69f0ce
Overview of MLRO role and responsibilities
-----------------------------

The AML Code 2019::PART 7 – REPORTING AND REGISTERS::27 External disclosures::4d4fe04d
Responsibilities regarding external disclosures
-----------------------------

The AML Code 2019::PART 7 – REPORTING AND REGISTERS::25 Reporting procedures::223c1e4d
Importance of maintaining reporting procedures
==============================
```

#### **Example 3**

```
System prompt: You are an expert in Isle of Man financial services regulation that is advising the user on the opperations of an Isle of Man regulated business. For every question, call the retrieval tool first to get relevant chunks from the legislation and guidance. Answer only from the retrieved content — do not draw on outside knowledge. If the retrieved chunks don't contain the answer, say so explicitly rather than guessing. For each chunk you draw on, include a Citation explaining what it contributed to your answer.
Q: I am about to review my CRA, what factors need to be included?
A: When reviewing your Customer Risk Assessment (CRA), several key factors must be considered:

1. **Changes in Information and Environment**: Assess any developments since the initial risk assessments, including new information about the business environment, customer circumstances, and ongoing monitoring results.
   - *Citation: The AML Handbook (April 2026), Chapter 2, Section 2.2.6 - Risk assessment reviews*.

2. **Monitoring Outcomes**: Analyze information from ongoing monitoring of business relationships to determine if they necessitate updates to the CRA.
   - *Citation: The AML Handbook (April 2026), Chapter 2, Section 2.2.6 - Risk assessment reviews*.

3. **Third-party Considerations**: If applicable, incorporate any assessments related to introducers and third parties involved in customer due diligence, including their risk levels and how customer due diligence is obtained.
   - *Citation: The AML Handbook (April 2026), Chapter 2, Section 2.2.10.1 - Introducer risk assessment reviews*; *Chapter 2, Section 2.2.10.4 - Relevant risk factors specific to the introducer risk assessment*.

4. **Emerging Risks**: Stay updated on new and emerging risks, and periodically review relevant alerts, sanctions, and media reports relevant to your business sectors and jurisdictions.
   - *Citation: The AML Handbook (April 2026), Chapter 2, Section 2.2.6 - Risk assessment reviews*; *Chapter 2, Section 2.2.8.3 - Relevant risk factors*.

5. **Higher Risk Factors**: Pay particular attention to customers classified as Politically Exposed Persons (PEPs) and consider any additional enhanced due diligence required for higher-risk individuals.
   - *Citation: The AML Handbook (April 2026), Chapter 3, Section 3.8.11.1 - Interaction of PEP requirements with ECDD requirements*; *Chapter 4, Section 4.7.2.1 - ML/FT/PF risk assessment requirements*.

6. **Documented Procedures**: Ensure that all considerations, findings, and changes in assessments are documented to support compliance and provide a clear rationale for decisions made during the CRA review process.
   - *Citation: The AML Handbook (April 2026), Chapter 2, Section 2.2.6 - Risk assessment reviews*.

By considering these factors, you ensure that your CRA remains relevant and effective against the risks posed by money laundering and terrorist financing. Regular reviews and updates are crucial for maintaining compliance with regulatory requirements
-----------------------------

The AML Handbook (April 2026)::Chapter 2 - General Requirements and Risk Based Approach::2.2.6 Risk assessment reviews::e17328d5
Identifies the need for assessing changes in the business environment and customer circumstances
-----------------------------

The AML Handbook (April 2026)::Chapter 2 - General Requirements and Risk Based Approach::2.2.10.1 Introducer risk assessment reviews::433bc1bc
Emphasizes the importance of third-party assessments in the CRA
-----------------------------

The AML Handbook (April 2026)::Chapter 2 - General Requirements and Risk Based Approach::2.2.8.3 Relevant risk factors::bf65c968
Informs about the necessity of reviewing emerging risks and proactive monitoring
-----------------------------

The AML Handbook (April 2026)::Chapter 3 - Customer Due Diligence, Ongoing Monitoring And Enhanced Measures::3.8.11.1 Interaction of PEP requirements with ECDD requirements::65defce7
Discusses the considerations necessary for higher-risk individuals like PEPs
-----------------------------

The AML Handbook (April 2026)::Chapter 2 - General Requirements and Risk Based Approach::2.2.6 Risk assessment reviews::34d0e8f2
Stresses the importance of documentation in the CRA review process
==============================
```

## 5. Installation

Currently the project is not production ready, but when this changes, installation instructions will be added here.

## 6. Licence

This Software is available under the AGPL v3 Licence

## 7. Contact

If you have any questions, please feel free to contact me at <cam01houston@gmail.com>
