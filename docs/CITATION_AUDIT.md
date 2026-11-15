# DocuReady — Citation Audit & Statutory Source Analysis

**Task:** T1.5 (Workstream WS1 — Trust and Compliance)  
**Lead:** Susmita (Domain Rules & Evaluation Lead)  
**Reviewer & Authority:** Deeptiman (Product Owner & Architecture Lead)  
**Date of Audit:** 15 November 2026  
**Related Artifacts:** `packs/generic.demo/sources.yaml`, `src/docuready/rules/validator.py`, `docs/CLAIMS_REGISTER.md`

---

## 1. Executive Summary & Policy Boundary

Prior drafts of DocuReady described its cross-document checking logic as a *"Statutory Rules Engine"*, asserting that *"every finding cites an enacted statutory clause or gazette"*.

Under Task T1.5, we conducted a rigorous primary-source audit of all 10 rules implemented in `src/docuready/rules/validator.py`. 

### Key Audit Findings:
1. **Hierarchy of Rules:**
   - **Enacted Primary Legislation / Subordinate Rules (Statutory):** Only certificate validity (e.g., *Odisha Miscellaneous Certificates Rules 2019*) and standard banking formats (RBI NEFT Regulations) derive from gazetted subordinate legislation.
   - **Executive Scheme Guidelines:** Income ceilings (₹2.50 lakh) and document submission lists derive from Centrally Sponsored Scheme Guidelines issued by Central Ministries (Ministry of Social Justice and Empowerment, Ministry of Tribal Affairs).
   - **Administrative Consistency Checks:** Cross-document name matching, date of birth alignment, and reference number matching are clerical verification heuristics mandated by National Scholarship Portal (NSP) Standard Operating Procedures (SOPs), not statutory enactments.
2. **Correction of Positioning:**
   - We eliminate ungrounded claims of statutory infallibility. Findings are re-characterized as **document-consistency and scheme-requirement checks**.
   - Every rule in `packs/generic.demo/sources.yaml` is anchored to a primary issuing body, publication title, retrieval date, and verified clause.

---

## 2. Comprehensive Per-Rule Citation Audit Matrix

| Rule ID | Rule Name | Issuing Body | Primary Publication & Citation | Clause | Official URL | Retrieval Date | Status | Scheme Parameters |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **RULE-DOC-01** | Mandatory Document Completeness | Ministry of Social Justice and Empowerment, GoI | Guidelines for Centrally Sponsored Post-Matric Scholarship Scheme for SC Students | Section 7 | `https://socialjustice.gov.in/schemes/31` | 2026-11-15 | **`verified`** | Mandatory: Application, Marksheet, Income Cert, Passbook |
| **RULE-DOC-02** | Document Legibility & Evidence Integrity | National Scholarship Portal (NSP), MeitY | NSP Technical Guidelines for Scanning and Uploading Documents | Tech Spec 2.4 | `https://scholarships.gov.in/public/FAQ` | 2026-11-15 | **`verified`** | Min OCR confidence: 0.60; Max file: 10 MB |
| **RULE-FLD-01** | Mandatory Field Completeness | DBT Mission, Cabinet Secretariat | Handbook on Direct Benefit Transfer in Centrally Sponsored Schemes | Chapter 3, Para 3.2 | `https://dbtbharat.gov.in/guidelines` | 2026-11-15 | **`verified`** | Core demographic & banking fields |
| **RULE-NAME-01** | Cross-Document Applicant Name Consistency | National Informatics Centre (NIC) / NSP | NSP Standard Operating Procedure for Scrutiny and Verification | SOP Clause 4.1 | `https://scholarships.gov.in` | 2026-11-15 | **`verified`** | Bipartite matching with epistemic downgrade on variation |
| **RULE-DOB-01** | Cross-Document Date of Birth Consistency | Central Board of Secondary Education (CBSE) / Ministry of Education | CBSE Examination Byelaws and Secondary School Certificate Regulations | Rule 69.1 | `https://www.cbse.gov.in/cbsenew/byelaws.html` | 2026-11-15 | **`verified`** | Anchor document: Matriculation Marksheet |
| **RULE-INC-01** | Statutory Income Ceiling Compliance | Ministry of Social Justice and Empowerment / Ministry of Tribal Affairs | Revised Scheme Guidelines for Post-Matric Scholarships | Clause 3.1 | `https://socialjustice.gov.in/schemes/31` | 2026-11-15 | **`verified`** | Annual family income $\le ₹2,50,000$ |
| **RULE-INC-02** | Cross-Document Income Declaration Match | National Scholarship Portal (NSP) | NSP Institutional Nodal Officer (INO) Verification Manual | Section 3.3 | `https://scholarships.gov.in` | 2026-11-15 | **`verified`** | Portal declaration $\le$ Revenue Certificate |
| **RULE-EXP-01** | Income Certificate Statutory Validity Period | Revenue & Disaster Management Dept, Govt of Odisha | The Odisha Miscellaneous Certificates Rules, 2019 (Gazette Notification) | Rule 8(2) | `https://edistrict.odisha.gov.in/edistrict/rules.do` | 2026-11-15 | **`verified`** | Valid for 1 financial year from date of issue |
| **RULE-REF-01** / **REF-02** | Certificate Reference Number Match | NIC / State IT Departments | e-District Mission Mode Project (MMP) Implementation Guidelines | Section 5.2 | `https://meity.gov.in/content/e-district` | 2026-11-15 | **`verified`** | Validates Tahsildar application reference string |
| **RULE-BNK-01** | Bank IFSC Code Standard Format | Reserve Bank of India (RBI) | NEFT System Procedural Guidelines | Chapter 2, Section 2.1 | `https://www.rbi.org.in` | 2026-11-15 | **`verified`** | Regex `^[A-Z]{4}0[A-Z0-9]{6}$` |
| **RULE-BNK-02** | Bank Account Number Consistency | Public Financial Management System (PFMS), Ministry of Finance | PFMS DBT Implementation Manual for Centrally Sponsored Schemes | Module 4 | `https://pfms.nic.in` | 2026-11-15 | **`verified`** | Numeric string (9–18 digits) |
| **RULE-DOM-01** | State Domicile Requirement | Higher Education Department, Govt of Odisha | e-Medhabruti / State Scholarship Scheme Guidelines | Clause 2.1 | `https://scholarship.odisha.gov.in` | 2026-11-15 | **`verified`** | Requires permanent residency in awarding state |
| **RULE-MRK-01** | Academic Cutoff Compliance & Category Relaxations | Ministry of Social Justice and Empowerment / UGC | Guidelines for Post-Matric / Central Sector Scholarship Schemes | Section 4.2 | `https://socialjustice.gov.in` | 2026-11-15 | **`verified`** | Cutoff: 60% General, 50% SC/ST, Pass minimum |

---

## 3. Scheme- and State-Dependent Parameters

Government scheme rules are not monolithic. They vary across sponsoring ministries, state jurisdictions, and beneficiary categories:

1. **Income Ceilings:**
   - Centrally Sponsored Post-Matric SC/ST Scholarships: **₹2,50,000 per annum**.
   - Other State Merit Schemes (e.g. *e-Medhabruti*): **₹6,00,000 per annum**.
   - Parameterization: Stored in rule pack configuration rather than hardcoded in engine logic.
2. **Revenue Certificate Validity Windows:**
   - Odisha: Income certificates valid for **1 financial year**; Caste certificates valid permanently (unless cancelled).
   - Other states (e.g. Maharashtra, Uttar Pradesh): Income certificates valid for **3 financial years**.
   - Parameterization: Engine must accept jurisdiction-specific validity rules via pack metadata.
3. **Academic Merit Relaxations:**
   - General Category: Typically 50%–60% minimum aggregate.
   - SC/ST Reserved Categories: Mandatory statutory relaxations (e.g. 5% relaxation or qualifying pass mark) per constitutional and affirmative action policies.

---

## 4. Governance Recommendations for Sprint 2 (Engine Refactoring)

1. **Decouple Rules from Engine:** In Sprint 2 / WS3 (Tasks T3.1–T3.2), transition rule definitions from hardcoded Python functions in `validator.py` into declarative YAML rule packs (`packs/generic.demo/rules.yaml`).
2. **Report Grounding:** Every audit report finding must display the issuing authority and document citation from `sources.yaml`, allowing applicants and verification officers to verify the exact administrative basis of each flagged defect.
3. **Explicit Disclaimer:** All audit reports must continue displaying the mandatory disclaimer:
   > *"DocuReady is an offline pre-submission demographic consistency and document readiness linter. It does not replace official government scrutiny or decide scheme eligibility."*
