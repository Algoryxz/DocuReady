# DocuReady — Problem Statement

## 1. The Citizen Welfare Application Bottleneck

In India and across developing digital economies, governments deliver hundreds of welfare schemes via online portals (e.g., National Scholarship Portal, Odisha State Scholarship Portal, PM-YASASVI, Medhabruti). These programs disburse billions of rupees in educational stipends, tuition subsidies, and affirmative-action grants to millions of low-income, Scheduled Caste (SC), Scheduled Tribe (ST), and Other Backward Class (OBC) citizens.

However, the application process requires submitting a **heterogeneous multi-document packet**:
1. Income Certificate (issued by Revenue Authority / Tahsildar)
2. Caste / Community Certificate (issued by Sub-Divisional Magistrate / Revenue Officer)
3. Resident / Domicile Certificate
4. Academic High School Marksheet / Certificate (issued by Board of Secondary Education)
5. Bank Account Passbook (for Direct Benefit Transfer / DBT payments)
6. Online Scheme Application Form

---

## 2. Root Causes of Application Rejection

Administrative audits from state welfare departments reveal that over **30% of citizen applications fail verification** due to preventable clerical discrepancies:

### A. Demographic Discrepancies
- **Name Inconsistencies**: The application form may read `"Smruti Ranjan Nayak"`, the bank passbook `"Smruti R. Nayak"`, and the high school marksheet `"SMRUTI RANJAN NAYAK"`. Discrepancies as minor as initials or phonetic spelling variations cause automated portal rejections or manual hold-ups.
- **Date of Birth Contradictions**: High school marksheets state birth dates in `DD/MM/YYYY`, while portal date-pickers or translated certificates may use `MM/DD/YYYY`.

### B. Statutory & Financial Breaches
- **Statutory Income Ceiling Violations**: Schemes like the Post-Matric Scholarship enforce a strict household annual income ceiling of ₹2,50,000. Applicants frequently submit outdated certificates or declare gross earnings that exceed the ceiling without realizing they are in eligible brackets.
- **Certificate Expiration**: Under state rules (e.g. *Odisha Miscellaneous Certificates Rules 2019*, Rule 8(2)), income certificates are valid for 3 financial years. Many applicants submit certificates issued 4 or 5 years ago, resulting in summary administrative rejection.

### C. Direct Benefit Transfer (DBT) Failure
- The Government of India mandates Aadhaar-seeded bank accounts for DBT scholarship disbursement. Passbooks without active NPCI Aadhaar mapping or with transposed account numbers result in failed payment batches after admission.

### D. Poor Scan Quality & Unreadable Files
- Low-resolution smartphone photos, shadow gradients, optical blur, and rotated certificate scans lead verification clerks to tag applications as "Unreadable Document" without specifying how to remediate.

---

## 3. The Asymmetric Cost of Rejection

When an application is rejected post-submission:
- The applicant receives an opaque notification weeks or months later.
- Re-application windows are typically closed for that academic year.
- Needy students are forced to discontinue schooling or take high-interest private debt to pay tuition fees.
- Verification clerks waste thousands of human hours reviewing defective files that could have been resolved before submission.

DocuReady was created to solve this specific structural problem: **catch and fix document packet discrepancies before the citizen clicks "Submit".**
