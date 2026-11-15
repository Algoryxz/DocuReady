# DocuReady — Citation Audit & Statutory Source Analysis

**Task:** T1.5 (Workstream WS1 — Trust and Compliance)  
**Lead:** Susmita (Domain Rules & Evaluation Lead)  
**Reviewer & Authority:** Deeptiman (Product Owner & Architecture Lead)  
**Date of Audit:** 15 November 2026 (Corrective Audit)
**Related Artifacts:** `packs/generic.demo/sources.yaml`, `src/docuready/rules/validator.py`, `docs/CLAIMS_REGISTER.md`

---

## 1. Executive Summary & Policy Boundary

Prior drafts of DocuReady described its cross-document checking logic as a *"Statutory Rules Engine"*, asserting that *"every finding cites an enacted statutory clause or gazette"*.

Under Task T1.5, we conducted a rigorous primary-source audit of all rules implemented in `src/docuready/rules/validator.py` and mapped to `packs/generic.demo/sources.yaml`.

### Critical Corrective Findings:
1. **Odisha Miscellaneous Certificates Rules, 2019:**
   - Previous internal drafts cited *Rule 8(2)* as statutory proof of a 1-financial-year income certificate validity.
   - Primary review reveals that **Rule 8 of the Odisha Miscellaneous Certificates Rules, 2019 concerns "Cancellation of miscellaneous certificate"**, not the duration of validity.
   - Validity periods derive from separate executive notifications and departmental orders, and vary widely by state jurisdiction and scheme (from 1 financial year to 3 financial years).
   - **Corrective Action:** The income validity rule (`RULE-EXP-01`) is marked **`unverified`** with explicit notation that validity windows are scheme- and state-dependent rather than anchored in an enacted clause of the cited 2019 rules.
2. **CBSE Examination Bye-Laws:**
   - Previous drafts cited *Rule 69.1* for Date of Birth verification.
   - Primary review confirms that **Rule 69.1 concerns Name Corrections**. The provision governing Date of Birth is **Rule 69.2 (Change/Correction in Date of Birth)**.
   - Furthermore, while CBSE secondary school marksheet date-of-birth records serve as universal age proof in practice, CBSE examination bye-laws govern board examinations, not statutory scholarship entitlements.
   - **Corrective Action:** The citation for `RULE-DOB-01` is corrected to **Rule 69.2**, and qualified as a board certification standard rather than an overarching statutory scheme mandate.
3. **e-District Mission Mode Project (MMP):**
   - Previous drafts cited *§5.2* as supporting certificate verification and barcode APIs.
   - Primary review confirms that **§5.2 of the e-District MMP guidelines addresses the notification of State Designated Agencies (SDAs)**. It does not provide statutory standards for automated barcode or reference number verification.
   - **Corrective Action:** `RULE-REF-01` is marked **`unverified`** (`supports_rule: false`), documenting reference number matching as an internal cross-document reconciliation heuristic.

---

## 2. Validator Rule Groups vs. Source Registry Mapping

The DocuReady validator (`src/docuready/rules/validator.py`) organizes document validation into **10 core functional checks**, emitting distinct finding IDs for PASS, REVIEW, UNKNOWN, and FAIL states:

| Check # | Functional Area | Emitted Validator Finding IDs | `sources.yaml` Anchor ID | Grounding Status |
|:---:|:---|:---|:---|:---:|
| 1 | Document Completeness | `RULE-DOC-01`, `RULE-DOC-02` | `RULE-DOC-01`, `RULE-DOC-02` | `RULE-DOC-01`: **`verified`**<br/>`RULE-DOC-02`: **`unverified`** |
| 2 | Mandatory Field Presence | `RULE-FLD-01` | `RULE-FLD-01` | **`unverified`** |
| 3 | Applicant Name Consistency | `RULE-NAME-01`, `RULE-NAME-02`, `RULE-NAME-UNCERTAIN`, `RULE-NAME-PASS` | `RULE-NAME-01` | **`unverified`** |
| 4 | Date of Birth Consistency | `RULE-DOB-01`, `RULE-DOB-02`, `RULE-DOB-03`, `RULE-DOB-UNCERTAIN`, `RULE-DOB-PASS` | `RULE-DOB-01` | **`verified`** (CBSE Rule 69.2) |
| 5 | Income Ceiling Compliance | `RULE-INC-01`, `RULE-INC-CEIL-UNCERTAIN`, `RULE-INC-CEIL-PASS` | `RULE-INC-01` | **`verified`** (MoSJE Scheme §3.1) |
| 6 | Income Declaration Match | `RULE-INC-02`, `RULE-INC-03`, `RULE-INC-MISMATCH-UNCERTAIN`, `RULE-INC-MISMATCH-PASS` | `RULE-INC-02` | **`unverified`** |
| 7 | Certificate Validity Period | `RULE-EXP-01`, `RULE-EXP-02`, `RULE-EXP-PASS` | `RULE-EXP-01` | **`unverified`** (State-dependent) |
| 8 | Certificate Reference Match | `RULE-REF-01`, `RULE-REF-02`, `RULE-REF-INC-PASS`, `RULE-REF-CST-PASS` | `RULE-REF-01` | **`unverified`** |
| 9 | Bank Account & IFSC Code | `RULE-BNK-01`, `RULE-BNK-02`, `RULE-BNK-IFSC-PASS` | `RULE-BNK-01`, `RULE-BNK-02` | `RULE-BNK-01`: **`verified`** (RBI NEFT)<br/>`RULE-BNK-02`: **`unverified`** |
| 10 | Domicile & Academic Cutoff | `RULE-DOM-01`, `RULE-DOM-PASS`, `RULE-MRK-01`, `RULE-MRK-RELAX-PASS`, `RULE-MRK-PASS` | `RULE-DOM-01`, `RULE-MRK-01` | `RULE-DOM-01`: **`unverified`**<br/>`RULE-MRK-01`: **`verified`** (MoSJE §4.2) |

---

## 3. Comprehensive Per-Rule Citation Audit Matrix

| Rule ID | Rule Name | Issuing Body | Primary Publication Title | Specific Clause | Official URL | Retrieval Date | Status | Supports Rule? |
|:---|:---|:---|:---|:---|:---|:---|:---:|:---:|
| **RULE-DOC-01** | Mandatory Document Completeness | Ministry of Social Justice and Empowerment, GoI | Centrally Sponsored Scheme of Post-Matric Scholarships to SC Students (2020-21 to 2025-26) | Section 7 | `https://socialjustice.gov.in/schemes/31` | 2026-11-15 | **`verified`** | Yes |
| **RULE-DOC-02** | Document Legibility & Evidence Integrity | NSP / MeitY | NSP Operational Guidelines & Portal User Instructions | General Upload Instructions | `https://scholarships.gov.in` | 2026-11-15 | **`unverified`** | No (Heuristic) |
| **RULE-FLD-01** | Mandatory Field Completeness | DBT Mission, Cabinet Secretariat | DBT Guidelines on Beneficiary Verification | Operational Guidance | `https://dbtbharat.gov.in` | 2026-11-15 | **`unverified`** | No (Heuristic) |
| **RULE-NAME-01** | Cross-Document Name Consistency | NIC / NSP | NSP Verification Manual & Operational Guidance | Demographic Verification | `https://scholarships.gov.in` | 2026-11-15 | **`unverified`** | No (Heuristic) |
| **RULE-DOB-01** | Date of Birth Consistency | CBSE | CBSE Examination Bye-Laws (CBSE/Coord/2021) | Rule 69.2 | `https://www.cbse.gov.in/cbsenew/byelaws.html` | 2026-11-15 | **`verified`** | Yes (CBSE standard) |
| **RULE-INC-01** | Statutory Income Ceiling Compliance | Ministry of Social Justice and Empowerment, GoI | Centrally Sponsored Scheme of Post-Matric Scholarships to SC Students | Clause 3.1 | `https://socialjustice.gov.in/schemes/31` | 2026-11-15 | **`verified`** | Yes |
| **RULE-INC-02** | Income Declaration Match | NSP | NSP Guidelines for Institute Nodal Officers | Income Scrutiny Protocol | `https://scholarships.gov.in` | 2026-11-15 | **`unverified`** | No (Heuristic) |
| **RULE-EXP-01** | Income Certificate Validity Period | State Revenue Departments | State Revenue Miscellaneous Certificates Regulations & Executive Orders | Departmental Validity Circulars | `https://edistrict.odisha.gov.in` | 2026-11-15 | **`unverified`** | No (State-dependent) |
| **RULE-REF-01** | Certificate Reference Number Match | NIC - e-District MMP | e-District MMP Technical Architecture | Service Specifications | `https://meity.gov.in/content/e-district` | 2026-11-15 | **`unverified`** | No (Heuristic) |
| **RULE-BNK-01** | Bank IFSC Code Standard Format | Reserve Bank of India (RBI) | RBI Master Direction — NEFT System Procedural Guidelines | Chapter 2, Section 2.1 | `https://www.rbi.org.in/scripts/BS_ViewMasCirculardetails.aspx?id=12143` | 2026-11-15 | **`verified`** | Yes |
| **RULE-BNK-02** | Bank Account Number Consistency | PFMS / Ministry of Finance | PFMS Operational Guidelines for DBT Account Validation | Account Matching Protocol | `https://pfms.nic.in` | 2026-11-15 | **`unverified`** | No (Heuristic) |
| **RULE-DOM-01** | State Domicile Requirement | State Higher Education / Welfare Depts | State Scholarship Scheme Guidelines (e-Medhabruti) | Scheme Eligibility Clauses | `https://scholarship.odisha.gov.in` | 2026-11-15 | **`unverified`** | No (State-dependent) |
| **RULE-MRK-01** | Academic Cutoff Compliance & Category Relaxations | Ministry of Social Justice and Empowerment, GoI | Centrally Sponsored Scheme of Post-Matric Scholarships to SC Students | Section 4.2 | `https://socialjustice.gov.in/schemes/31` | 2026-11-15 | **`verified`** | Yes |

---

## 4. Policy Conclusions & Product Positioning

1. **Only 5 of the 13 rule pack entries are `verified` primary sources.** The remaining 8 entries represent operational portal heuristics, state-dependent variations, or clerical pre-checks.
2. DocuReady must never claim that every check represents an enacted statutory clause. Checks are properly termed **demographic consistency and scheme-requirement verifications**.
3. All audit reports continue to carry the mandatory disclaimer:
   > *"DocuReady is an applicant-side preparation aid. It checks consistency against published scheme guidelines and does not replace official government scrutiny or decide scheme eligibility."*
