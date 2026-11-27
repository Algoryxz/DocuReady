# DOCUREADY — LOOP 34 DATASET PROVENANCE & LICENSE AUDIT

**Milestone:** Loop 34  
**Date:** 2026-11-26  
**Total Documents Audited:** 60  

---

## 1. Source-Level Provenance & Licensing Register

| Dataset / Source | Issuing Entity | Authoritative Source / URL | License Type | Commercial Use? | Redistribution? | Sample Count |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **FUNSD** | Guillaume Jaume / IIT-CDIP | https://guillaumejaume.github.io/FUNSD/ | Public Domain (IIT-CDIP) / Research Evaluation | Restricted | Permitted (Research) | 20 |
| **CORD** | NAVER Clova AI | https://github.com/clovaai/cord | CC-BY-SA 4.0 | Permitted (ShareAlike) | Permitted (Attribution) | 16 |
| **SROIE** | ICDAR 2019 / IEEE | https://rrc.cvc.uab.es/?ch=13 | Academic Competition License | Prohibited | Prohibited (Redistribution) | 12 |
| **Indian Gazette** | Government of Odisha / India | https://egazette.gov.in | Government Open Data License (GODL-India) / Sec 52(1)(q) | Permitted | Permitted | 8 |
| **Land Revenue (Khatauni)**| Revenue & Disaster Mgmt Dept | https://bhulekh.ori.nic.in | Public Record / Government Open Format | Permitted | Permitted | 4 |

---

## 2. In-Depth Licensing Scrutiny & Legal Grounding

1. **FUNSD (IIT-CDIP Subset):**
   - The underlying documents belong to the public domain pursuant to the 1998 Master Settlement Agreement (MSA) public disclosure archives. 
   - DocuReady uses FUNSD solely as a static benchmark reference corpus. Zero commercial redistribution of derived commercial datasets is attempted.
2. **CORD (Consortium for Open Receipt Data):**
   - Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA 4.0).
   - Commercial use is permitted provided modifications and annotations are shared under the same license terms with attribution.
3. **SROIE (ICDAR 2019):**
   - Provided strictly for competitive and scientific benchmarking.
   - SROIE image samples are kept purely as local evaluation fixtures; they are **never bundled** into the production installer (`DocuReady-0.1.0-Setup.exe`).
4. **Government Gazettes & Administrative Records:**
   - Under Section 52(1)(q) of the Indian Copyright Act 1957, the reproduction or publication of any matter published in any Official Gazette is expressly non-infringing.
   - Fully compliant with GODL-India and National Data Sharing and Accessibility Policy (NDSAP).

---

## 3. Sensitive Data & Privacy Scrutiny

- All documents in the Loop 34 corpus were audited for Personal Identifiable Information (PII).
- Public records with historical non-PII or synthetically anonymized names (`ROHIT VERMA`, `SUNIL KUMAR`) are utilized.
- Real personal financial or biometric data is strictly prohibited and absent from the evaluation corpus.
