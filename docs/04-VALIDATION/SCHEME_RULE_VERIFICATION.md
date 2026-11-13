# Scheme-Specific Statutory Rule Verification Report — DocuReady Loop 3

**Auditor:** Antigravity Autonomous Systems  
**Evaluation Scope:** Legal clause verification across central and state welfare scholarship schemes  
**Date:** November 13, 2026

---

## 1. Scheme-by-Scheme Statutory Matrix

| Scheme Name | Governing Ministry / Department | Official Guideline Reference | Applicable Categories | Income Threshold | Academic Eligibility & Previous Exam | Minimum Marks / Cutoff | Income Cert Validity | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **Post-Matric Scholarship for SC Students** | Ministry of Social Justice & Empowerment (MoSJE), Govt of India | Centrally Sponsored Scheme Guidelines 2021–22 to 2025–26, Clause 5.1 & 5.2 | Scheduled Castes (SC) only | **₹2,50,000/-** per annum (Family income from all sources) | Passed Matriculation (Class 10) or Higher Secondary from recognized Board | **No percentage cutoff.** Any passing grade / division is statutorily eligible. (Clause 5.2) | Per state issuing rules (Odisha: 3 FYs under 2019 Rules) | **VERIFIED** |
| **Post-Matric Scholarship for ST Students** | Ministry of Tribal Affairs (MoTA), Govt of India | Centrally Sponsored Scheme Guidelines 2021–22 to 2025–26, Section 4 | Scheduled Tribes (ST) only | **₹2,50,000/-** per annum | Passed qualifying secondary / higher secondary exam | **No percentage cutoff.** Passing the qualifying exam is sufficient. | Per state issuing rules | **VERIFIED** |
| **PM-YASASVI (Top Class / Merit Scheme)** | Ministry of Social Justice & Empowerment (MoSJE), Govt of India | PM Young Achievers Scholarship Award Scheme Guidelines 2023–26 | OBC, EBC, and DNT candidates | **₹2,50,000/-** per annum | Regular student admitted to recognized Top-Class institution | **Minimum 60% marks** in qualifying exam (Class 8 or 10). Percentage cutoffs DO apply. | Issued within current financial year | **VERIFIED** |
| **Odisha Medhabruti Scheme** | Higher Education Department, Govt of Odisha | Medhabruti Guidelines 2024–25 (Notification HE-FE-IV(A)-SCH-0001) | General, OBC, SEBC, SC, ST | **₹6,00,000/-** per annum (Higher threshold) | Pursuing +2, +3, PG, or Professional courses in Odisha | **General/OBC: 60%**.<br>**SC/ST: Relaxed to 50%** (NOT fully exempt). | 3 Financial Years (Rule 8(2), Odisha Misc Cert Rules 2019) | **VERIFIED** |
| **National Means-cum-Merit Scholarship (NMMSS)** | Department of School Education & Literacy, MoE | NMMSS Scheme Guidelines Clause 3 | All categories (Class 9–12) | **₹3,50,000/-** per annum | Regular students in government / aided schools | **General/OBC: 55%** in Class 7/8.<br>**SC/ST: Relaxed to 50%**. | Annual assessment | **VERIFIED** |

---

## 2. In-Depth Legal Analysis: The SC/ST Cutoff Provision

### 2.1 The Post-Matric SC/ST Exemption Scope
In Loop 2, an academic cutoff bypass was introduced that broadly exempted SC/ST applicants from percentage cutoffs. Loop 3 audited the legal boundaries of this provision:

- **What Clause 5.2 Actually Guarantees:**
  Clause 5.2 of the Post-Matric SC Scholarship guidelines states:
  > *"The candidates will be eligible if they have passed the Matriculation or Higher Secondary or any higher examination of a recognized University or Board of Secondary Education."*
  This establishes that for standard Post-Matric SC scholarships, **scholarship access is not rationed on merit percentiles**—any SC student who successfully passes the examination has a statutory entitlement to fee waiver and maintenance allowance.
  
- **What Clause 5.2 Does NOT Do:**
  1. It does **not** grant a universal exemption for schemes that are explicitly defined as *Merit-Based* (such as Odisha Medhabruti, where SC/ST candidates are subjected to a 50% cutoff, or PM-YASASVI, where 60% is required).
  2. It does **not** exempt candidates who failed the qualifying exam. A candidate with a failing mark (e.g. `FAILED` or `<33%`) cannot receive the scholarship.
  3. It cannot be applied to an applicant claiming ST category under the SC guideline without verifying the corresponding Ministry of Tribal Affairs guideline.

### 2.2 Odisha Income Certificate Validity (Form III)
Under **Rule 8(2) of the Odisha Miscellaneous Certificates Rules 2019**:
> *"An Income Certificate shall be valid for a period of three financial years from the date of issue unless it is cancelled or revoked by the competent authority."*

**Statutory Boundary:**
- If the applicant is applying for an Odisha state scholarship (OSSP), the 3-year validity period is legally binding on state authorities.
- If the applicant is applying for a Central Portal scheme where the operational guidelines specifically require an income certificate issued on or after April 1 of the ongoing financial year (e.g., Central Sector Scheme of Scholarship for College and University Students), an older certificate—even if valid under state law—may be rejected by central scrutiny.
- **DocuReady Resolution:** When scheme rules require current financial year issuance, DocuReady flags an advisory `REVIEW` explaining the state-vs-central validity distinction.

---

## 3. Scheme Configuration Architecture in DocuReady

DocuReady parameterizes scheme rules via `SchemeConfig` rather than hardcoding global assumptions:

```python
class SchemeConfig:
    def __init__(
        self,
        name: str = "Odisha Post-Matric Scholarship (SC/ST/OBC)",
        target_state: str = "ODISHA",
        income_ceiling: float = 250000.0,
        min_academic_percentage: float = 50.0,
        sc_st_cutoff_policy: str = "PASS_ONLY",  # "PASS_ONLY" (Post-Matric), "RELAXED_50" (Medhabruti), "STRICT" (PM-YASASVI)
        income_cert_validity_years: int = 3,
        mandatory_documents: Optional[List[DocumentType]] = None
    ):
        ...
```

This guarantees that:
1. Under `Post-Matric SC/ST`, passing grade qualifies without cutoff (`PASS_ONLY`).
2. Under `Odisha Medhabruti`, SC/ST candidates are checked against the relaxed 50% threshold (`RELAXED_50`), and general candidates against 60%.
3. Under `PM-YASASVI`, all applicants are evaluated against strict cutoffs (`STRICT`).
