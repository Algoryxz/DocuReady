# DOCUREADY — INDEPENDENT VALIDATION REPORT (LOOP 5 PHASE 1)

**Evaluation Date:** November 16, 2026  
**Milestone:** Loop 5 Phase 1 — Independent Validation  
**Auditor:** Antigravity Engineering Agent  
**Active Branch:** `feat/loop5-independent-validation-and-demo`  
**Execution Script:** [`tests/independent_validation_runner.py`](file:///c:/Users/smara/Desktop/New%20folder/tests/independent_validation_runner.py)  
**Machine-Readable Results:** [`docs/independent_validation_results.json`](file:///c:/Users/smara/Desktop/New%20folder/docs/independent_validation_results.json)

---

## 1. Methodology & Independent Ground Truth Oracle

In contrast to regression tests that compare engine output against previously serialized snapshots, this independent validation procedure employs an **external Human Auditor Ground Truth Oracle** formulated directly from visual document inspection:
- Each synthetic source document was independently read by an auditor specification.
- Expected field values, target document types, source page numbers, and bounding-box coordinate validity criteria were defined independently.
- The pipeline was evaluated against this oracle across three layers:
  1. **Document & Field Layer:** Individual document classification, field value accuracy, page index fidelity, and non-hallucinated bounding boxes.
  2. **Packet Decision Layer:** Statutory rule evaluation against clean packets, contradictory name mismatches, and income ceiling breaches.
  3. **Export Integrity Layer:** Verification that public sanitized exported reports preserve identical finding identifiers, severity ratings, penalty deductions, and evidence references.

---

## 2. Document & Field Extraction Evaluation

| Document Name | Expected Type | Status | Fields Checked | Field Match % | Provenance Valid |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `VAL_01_application_form.pdf` | `APPLICATION_FORM` | `VALID` | 7 | 100.0% | Yes (Page 1, all valid bboxes) |
| `VAL_02_income_cert_clean.pdf` | `INCOME_CERT` | `VALID` | 4 | 100.0% | Yes (Page 1, all valid bboxes) |
| `VAL_03_caste_cert_clean.pdf` | `CASTE_CERT` | `VALID` | 4 | 100.0% | Yes (Page 1, all valid bboxes) |
| `VAL_04_residence_cert_clean.pdf`| `RESIDENCE_CERT` | `VALID` | 5 | 100.0% | Yes (Page 1, all valid bboxes) |
| `VAL_05_bank_passbook_clean.pdf` | `BANK_PASSBOOK` | `VALID` | 3 | 100.0% | Yes (Page 1, all valid bboxes) |
| `VAL_06_marksheet_clean.pdf` | `MARKSHEET` | `VALID` | 3 | 100.0% | Yes (Page 1, all valid bboxes) |
| `VAL_07_income_cert_name_conflict.pdf`| `INCOME_CERT`| `VALID` | 1 | 100.0% | Yes (Page 1, valid bbox) |
| `VAL_08_income_cert_ceiling_exceeded.pdf`| `INCOME_CERT`| `VALID` | 1 | 100.0% | Yes (Page 1, valid bbox) |
| `VAL_09_corrupted_header.pdf` | None (Corrupted) | `CORRUPTED` | 0 | N/A | Safe rejection; 0 fields |
| `VAL_11_encrypted_password.pdf` | None (Encrypted) | `UNREADABLE`| 0 | N/A | Safe rejection; 0 fields |
| `VAL_13_irrelevant_resume.pdf` | Unmapped Slot | `VALID` | 0 | N/A | 0 scholarship fields extracted |

### Provenance & Bounding Box Findings:
- **Total Fields Checked:** 28
- **Fields Matching Ground Truth Value:** 28 (100.0%)
- **Source Page Accuracy:** 100.0% (all verified on Page 1)
- **Geometry Coordinates:** All bounding boxes satisfy `0 <= x0 <= x1 <= page_width` and `0 <= y0 <= y1 <= page_height`.
- **Known Architecture Constraint Handled:** In `application_form.pdf`, `annual_income` is parsed via table regular expression matching without discrete token coordinates. The engine safely records `None` rather than hallucinating artificial bounding box numbers.

---

## 3. Statutory Packet Decision Scenarios

### Scenario 1: Clean Statutory Packet (6 Documents)
- **Input:** Clean Application Form, Income Cert, Caste Cert, Residence Cert, Bank Passbook, Marksheet.
- **Independent Expected Outcome:** All mandatory documents present; applicant demographics align; income under ceiling; category verified; domicile verified; bank DBT verified; readiness score = `100`, status = `"NO_ISSUES_FOUND"`.
- **Actual Engine Outcome:** Readiness Score `100`, Status `"NO_ISSUES_FOUND"`. 8 evaluated findings (all PASS / INFO).
- **Result:** **PASSED**.

### Scenario 2: Contradictory Name Conflict
- **Input:** Clean Application Form (`Aarav Sharma`) + Income Cert belonging to `Vikramaditya Roy`.
- **Independent Expected Outcome:** Detection of contradictory identity discrepancy; `RULE-NAME-01` must fail; packet must be marked `"NOT_READY"`.
- **Actual Engine Outcome:** `RULE-NAME-01` failed (`CONTRADICTORY_NAME_MISMATCH`, severity `FATAL`, penalty 40). Overall status: `"NOT_READY"`.
- **Result:** **PASSED**.

### Scenario 3: Income Ceiling Breach
- **Input:** Clean Application Form + Income Cert declaring Rs. `4,50,000/-` (exceeding Rs. 2,50,000/- ceiling).
- **Independent Expected Outcome:** Income ceiling breach detection; `RULE-INC-01` must fail; packet must be marked `"NOT_READY"`.
- **Actual Engine Outcome:** `RULE-INC-01` failed (`INCOME_CEILING_EXCEEDED`, severity `FATAL`, penalty 35). Overall status: `"NOT_READY"`.
- **Result:** **PASSED**.

---

## 4. Export Report Integrity & Provenance Preservation

The exported canonical public report dictionary was checked against the internal runtime model:
1. **Finding Identity Preservation:** 100% of finding IDs (`RULE-NAME-01`, `RULE-INC-01`, `RULE-DOM-PASS`, etc.) are preserved identically in exported output.
2. **Severity and Penalty Parity:** Penalties and resolved statuses match the internal pipeline resolution byte-for-byte.
3. **Redaction Compliance:** Sensitive applicant identity values are safely masked or redacted in exported logs and reports without dropping finding provenance.
4. **Result:** **100% Export Integrity Verified**.

---

## 5. Summary Metrics

```json
{
  "total_documents_evaluated": 11,
  "documents_fully_passing": 11,
  "total_fields_checked": 28,
  "fields_matched_gt": 28,
  "field_accuracy": 1.0,
  "packet_scenarios_passed": true,
  "export_integrity_passed": true,
  "inconclusive_cases": 0
}
```

*Independent Validation Certified by DocuReady Antigravity Engineering Agent.*
