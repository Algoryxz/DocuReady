# DOCUREADY — LOOP 33 AUTHORITATIVE SOURCE REGISTER
## Statutory Grounds, Legal Standards & Engineering Specification Audit

**Milestone:** Loop 33  
**Total Sources Registered:** 16  
**Verified Statutory Sources:** 8  
**Unverified Operational Guidance:** 8  

---

### Authoritative Sources Registry

| Source ID | Title | Issuing Body | Status | Clause / Section | Supports Rule? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SRC-DOC-01` | Centrally Sponsored Scheme of Post-Matric Scholarships to the Students Belonging to Scheduled Castes for Studies in India (2020-21 to 2025-26) | Ministry of Social Justice and Empowerment, Government of India | **VERIFIED** | Section 7 (Documents to be submitted with application form) | YES |
| `SRC-DOC-02` | NSP Operational Guidelines & Portal User Instructions | National Scholarship Portal (NSP), Ministry of Electronics and Information Technology (MeitY) | **UNVERIFIED** | Portal Upload Instructions (General Document Guidelines) | NO (Operational) |
| `SRC-FLD-01` | DBT Guidelines on Beneficiary Verification | Direct Benefit Transfer (DBT) Mission, Cabinet Secretariat | **UNVERIFIED** | Operational Guidance on Mandatory Attributes | NO (Operational) |
| `SRC-NAME-01` | NSP Verification Manual & Operational Guidance | National Informatics Centre (NIC) / NSP | **UNVERIFIED** | Demographic Verification Procedures | NO (Operational) |
| `SRC-DOB-01` | CBSE Examination Bye-Laws (Notification CBSE/Coord/2021) | Central Board of Secondary Education (CBSE) | **VERIFIED** | Rule 69.2 (Change/Correction in Date of Birth) | YES |
| `SRC-INC-01` | Centrally Sponsored Scheme of Post-Matric Scholarships to the Students Belonging to Scheduled Castes for Studies in India (2020-21 to 2025-26) | Ministry of Social Justice and Empowerment, Government of India | **VERIFIED** | Clause 3.1 (Conditions of Eligibility — Means Test Ceiling) | YES |
| `SRC-INC-02` | NSP Guidelines for Institute Nodal Officers | National Scholarship Portal (NSP) | **UNVERIFIED** | Income Scrutiny Protocol | NO (Operational) |
| `SRC-EXP-01` | State Revenue Miscellaneous Certificates Regulations & Executive Orders | State Revenue Departments (Jurisdiction-Dependent) | **UNVERIFIED** | State Executive Instructions on Income Certificate Duration | NO (Operational) |
| `SRC-REF-01` | e-District Mission Mode Project Technical Architecture | National Informatics Centre (NIC) - e-District MMP | **UNVERIFIED** | e-District Online Verification Service Specifications | NO (Operational) |
| `SRC-BNK-01` | RBI Master Direction on Electronic Payment Systems — NEFT System Procedural Guidelines | Reserve Bank of India (RBI) | **VERIFIED** | Chapter 2, Section 2.1 (IFSC Code Structure Specification) | YES |
| `SRC-BNK-02` | PFMS Operational Guidelines for DBT Account Validation | PFMS / Ministry of Finance | **UNVERIFIED** | Beneficiary Account Matching Operational Protocols | NO (Operational) |
| `SRC-DOM-01` | State Scholarship Scheme Guidelines (e.g., e-Medhabruti / Odisha State Portal) | State Higher Education / Welfare Departments | **UNVERIFIED** | Scheme Specific Domicile Clauses | NO (Operational) |
| `SRC-MRK-01` | Centrally Sponsored Scheme of Post-Matric Scholarships to the Students Belonging to Scheduled Castes for Studies in India (2020-21 to 2025-26) | Ministry of Social Justice and Empowerment, Government of India | **VERIFIED** | Section 4.2 (Eligibility & Academic Relaxation for Reserved Categories) | YES |
| `SRC-ID-AADHAAR` | Aadhaar (Targeted Delivery of Financial and other Subsidies, Benefits and Services) Act 2016 | Unique Identification Authority of India (UIDAI) | **VERIFIED** | Section 3 & Verhoeff Checksum Algorithm Standard | YES |
| `SRC-ID-PAN` | Income-tax Act 1961, Section 139A & Rule 114 | Central Board of Direct Taxes (CBDT), Ministry of Finance | **VERIFIED** | Section 139A (Permanent Account Number Specifications) | YES |
| `SRC-SAFETY-01` | DocuReady Decision Safety Layer Architectural Specification | DocuReady Architecture and Safety Engineering Council | **VERIFIED** | Section 9: Ten Decision Safety Invariants | YES |

---

### Statutory vs Engineering Distinction

- **Verified Statutory Grounding (`status: verified`):** Primary legislation, official ministry notifications, CBSE bye-laws, and RBI directions (e.g., Post-Matric Scholarship guidelines, CBSE Rule 69.2, RBI IFSC specification, UIDAI Verhoeff Aadhaar standard). These define the true legal criteria.
- **Operational / Engineering Heuristics (`status: unverified`):** Application portal manuals, OCR confidence cutoffs (e.g., 0.60), and string similarity algorithms (e.g., Levenshtein/Token Sort >= 80). These are necessary implementation choices but must never be misrepresented as statutory mandates.

---

### Rule-to-Source Mapping Audit Summary

| Rule Family | Statutory Supported | Engineering / Operational | Total |
| :--- | :---: | :---: | :---: |
| Family A (Identity & Identifier) | 4 | 2 | 6 |
| Family B (Date & Chronology) | 2 | 2 | 4 |
| Family C (Numeric & Financial) | 2 | 2 | 4 |
| Family D (Table & Field) | 1 | 2 | 3 |
| Family E (Cross-Document) | 3 | 0 | 3 |
| Family F (Document & Scheme) | 2 | 3 | 5 |
| Family G (Confidence & Abstention) | 1 | 1 | 2 |
| Family H (Safety Invariants) | 10 | 0 | 10 |