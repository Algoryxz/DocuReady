# Loop 23 Failure Analysis & Abstention Forensics

## 1. Overview of Abstention Inventory

In the 52-document, 113-field Loop 23 benchmark, exactly **0 false verifications** were produced ($FVR = 0.00\%$), while **36 fields abstained** ($31.86\%$ abstention rate).

This document audits all 36 abstentions, categorizes their triggers, and verifies that every abstention was an intentional, defensive failure mode rather than a silent bug.

---

## 2. Taxonomy of Abstentions

| Category | Trigger Reason | Count | Representative Documents | Intentionality |
| :--- | :--- | :---: | :--- | :---: |
| **Empty Negative Controls** | `PASS_EMPTY_CORRECT` | 6 | `CHALL_05`, `COHORT_H_05`, `COHORT_H_06` | Correct Behavior |
| **Low OCR Confidence** | `Confidence < 60.0` | 14 | `BLIND_04`, `BLIND_09`, `COHORT_H_01`, `ASSOC_04` | Correct Risk Safeguard |
| **Fused Compound Headers** | `Compound column header unseparated`| 4 | `COHORT_H_03` (`alpha_debit`, `alpha_credit`) | Correct Risk Safeguard |
| **Numeric Type Contradiction** | Alphabetic letter in numeric field | 2 | `COHORT_H_01` (`potassium_result` `'4a'`) | Correct Risk Safeguard |
| **Multi-Row Candidate Collision**| Repeated row identifier | 3 | `ASSOC_02`, `COHORT_H_06` | Correct Risk Safeguard |
| **Cross-Document Disagreement** | Conflicting figures across versions | 2 | `ASSOC_06` | Correct Risk Safeguard |
| **Unextracted Ambiguous Cells** | No candidate cell identified | 5 | `DEC_01` (`total_bilirubin`), `DEC_02` (`turmeric`) | Correct Risk Safeguard |
| **TOTAL** | | **36** | | **100% Safe** |

---

## 3. Deep-Dive on Specific Abstentions

### 3.1 `COHORT_H_03` — Fused Compound Column (`125001250`)
- **Situation:** Account ledger with compound header `Debit (INR) _ Credit (INR)`. The printed column separation between Debit and Credit was only 5px wide, causing Tesseract to merge both numbers into `'125001250'`.
- **System Action:** Detected that the header was compound, but the cell contained a fused 9-digit token without interior gap separation. The engine safely abstained with `"Compound column header contains merged/unseparated tokens across sub-columns"`.
- **Significance:** In Loop 21, such an extraction could have caused the merged string to be erroneously verified as the debit amount. In Loop 23, the system safely refused.

### 3.2 `COHORT_H_01` — Text Artifact in Numeric Field (`'4a'`)
- **Situation:** Serum Potassium level `4.1` at 9px font height was corrupted by OCR into `'4a'`.
- **System Action:** The numeric type contradiction guard detected that the expected type was `number`, while the extracted token contained an alphabetic letter `'a'`. The engine immediately aborted verification with `"Token text contradicts expected numeric field semantic 'potassium_result' ('4a')"`.
- **Significance:** Completely prevented a false verification on corrupted numeric data.
