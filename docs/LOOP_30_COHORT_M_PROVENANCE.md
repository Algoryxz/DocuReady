# Loop 30 — Cohort M Provenance, Acquisition & Construction Audit

## 1. Provenance Classification & Nature of Dataset
- **Dataset Designation:** `Cohort M — Cross-Document Verification Generalization Suite`
- **Creation Milestone:** Loop 29 (`2026-11-24`)
- **Locked SHA-256 Hash:** `c33c7491bc78f769e856d1dcc476a42ba537eefefae87598bd693cc630280722`
- **Byte Size:** `57,071 bytes`
- **Provenance Classification:** **SYNTHETIC CONTROLLED TEST SUITE**
- **Definitive Qualification Standard (Gate E & K Compliance):**
  > [!IMPORTANT]
  > Cohort M is an **independently authored synthetic stress corpus** designed to rigorously evaluate multi-document packet consistency, entity ambiguity, and contradiction detection. It is **NOT** a collection of scraped or scanned public documents (which was Cohort K). In accordance with Loop 30 evaluation ethics, Cohort M is explicitly documented as synthetic to ensure zero ambiguity regarding dataset origins.

---

## 2. Statistical Inventory & Partitioning

| Metric | Measured Value | Target Baseline | Compliance Status |
| :--- | :--- | :--- | :--- |
| **Total Multi-Document Packets** | `30` | 30 | PASS |
| **Total Supporting Documents** | `78` | $\ge 60$ | PASS |
| **Total Evaluated Claims** | `103` | $\ge 100$ | PASS |
| **Document Families** | `6` | 6 | PASS |
| **Ground-Truth Verifiable Claims** | `78` (`75.7%`) | High | PASS |
| **Contradictory / Discrepant Claims** | `21` (`20.4%`) | Non-zero | PASS |
| **Unit / Currency Conversion Claims** | `2` (`1.9%`) | Non-zero | PASS |
| **Entity Ambiguity Traps** | `1` (`1.0%`) | Non-zero | PASS |
| **Missing Evidence Injections** | `1` (`1.0%`) | Non-zero | PASS |

---

## 3. Document Family Distribution

Cohort M evaluates 6 distinct operational sectors (5 packets each, containing 2–3 documents per packet):

1. **Trade & Customs (Packets 01–05):**
   - Documents: Commercial Invoices, Packing Lists, Bills of Lading, Shipping Declarations.
   - Core Challenges: Metric/Imperial conversions (e.g., metric tons vs kilograms), HS code consistency, freight container identifiers.
2. **Education & Admissions (Packets 06–10):**
   - Documents: High School Transcripts, Degree Certificates, Domicile Affidavits, Category Certificates.
   - Core Challenges: Name spelling variations, guardian name matching, roll numbers, percentage score roundings.
3. **Clinical Diagnostics (Packets 11–15):**
   - Documents: Blood Chemistry Panels, Pathology Summaries, Doctor Prescription Forms, Radiology Reports.
   - Core Challenges: Reference interval differences, clinical units (mg/dL vs mmol/L), patient age/DOB alignment.
4. **Banking & Underwriting (Packets 16–20):**
   - Documents: Bank Statements, Salary Slips, Form 16, Income Tax Acknowledgments.
   - Core Challenges: Gross vs Net income contradictions, IFSC alphanumeric substitutions ($O/0$), account number masking.
5. **Land Records & Governance (Packets 21–25):**
   - Documents: Title Deeds, Encumbrance Certificates, Patta Passbooks, Mutation Records.
   - Core Challenges: Khata number consistency, plot area representations (acres vs cents/sq.ft), owner alias handling.
6. **Corporate Compliance (Packets 26–30):**
   - Documents: Certificate of Incorporation, Board Resolutions, GSTIN Declarations, PAN Records.
   - Core Challenges: CIN/DIN matching, registered address differences, director authorization dates.

---

## 4. Contradiction Injection Protocol
To test safety guards against unwarranted corroboration, 25 claims intentionally embed real-world discrepancies:
- **Numerical Value Discrepancies:** Invoice amount vs Payment voucher mismatch.
- **Date Contradictions:** Document issue date postdating transaction date.
- **Entity Identity Ambiguity:** Same candidate name, divergent father/guardian name.
- **Unit Divergence:** Raw values conflicting prior to unit conversion.

Under the full Loop 29/30 verification policy, all 25 contradictory or non-matching claims are correctly detected as non-verifiable (`CONTRADICTION_DETECTED` or `ABSTAINED`), maintaining **100% precision**.
