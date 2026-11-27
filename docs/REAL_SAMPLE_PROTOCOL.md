# DocuReady Real-Sample Evaluation Protocol (T4.4)

**Owner:** Susmita — Domain Rules, Evidence & Evaluation Lead
**Status:** Baseline Protocol (Documentation-Only)
**Gate Context:** Gate G5 (WS4 — Real-World Readiness)

---

## 1. Purpose

DocuReady's current evaluation metrics (`eval/EVAL_CARD.md`, `eval/baseline.json`) are measured exclusively on **synthetic** documents. This protocol defines the mandatory privacy, consent, redaction, storage, and reporting controls required before any real-world documents may be evaluated.

---

## 2. Two-Stage Real-Sample Acquisition Path

1. **Stage A — Official Specimen / Format Certificates:**
   - Begin exclusively with blank or sample specimen formats published on official Government of Odisha / Central Government portals (e.g., e-District specimen forms, W&CD SOP Annexures).
   - Zero personal data is present in specimen formats.
2. **Stage B — Voluntary, Informed, Consented & Redacted Donations:**
   - Real applicant documents may only be evaluated if **explicitly donated** by an informed adult volunteer using a signed consent record.
   - Consent text must explain:
     - Purpose: offline OCR and validation-engine accuracy benchmarking only.
     - Right to withdraw and request immediate deletion at any time.
     - Non-effect on any government benefit application.

---

## 3. Mandatory Redaction Requirements

Before a donated document enters the local evaluation store:
- Mask or redact full Aadhaar numbers (retain at most last 4 digits if testing ID format).
- Mask or redact full bank account numbers (retain at most last 4 digits).
- Mask or redact personal phone numbers and street-level residential addresses.
- Retain only the synthetic/masked test identifier and the minimum visual tokens needed for layout/OCR evaluation.

---

## 4. Storage, Access Controls, Retention & Deletion

- **Never commit real documents to Git:** Real or donated documents must **never** be committed to the public `Algoryxz/DocuReady` repository, test fixtures, or CI artifacts.
- **Encrypted / Restricted Local Storage:** Store donated evaluation samples exclusively in an access-controlled, encrypted local directory (`0700` permissions) outside the Git working tree.
- **No Network Calls:** All evaluation runs execute strictly offline (`no_network` contract).
- **Retention & Deletion:** Retain donated samples only for the active evaluation cycle (maximum 90 days unless renewed in writing) and securely delete upon completion or donor request.

---

## 5. Prohibited Data Practices

The following practices are strictly **forbidden**:
1. Scraping personal documents or certificates from public portals, search engines, or social media.
2. Evaluating unconsented third-party documents.
3. Committing real personal documents, unredacted Aadhaar/bank numbers, or raw PII snippets to GitHub or CI logs.
4. Using real-world donated samples for model training without explicit separate consent.

---

## 6. Reporting Methodology & Claim Boundaries

- **Separated Reporting:** Synthetic evaluation metrics and real-sample evaluation metrics must be reported in separate tables; never pool synthetic and real samples into a single unqualified accuracy number.
- **Permitted Claims Once Real Samples Are Evaluated:**
  - Observed false-pass rate, false-fail rate, abstention rate, and per-field OCR accuracy on the specific redacted real-sample cohort (with sample size $n$ and 95% confidence intervals).
- **Continuing Limitations (Remain Forbidden Even After Real-Sample Evaluation):**
  - DocuReady still cannot claim statutory eligibility determination, government database verification, or universal accuracy across all Indian states and districts.
