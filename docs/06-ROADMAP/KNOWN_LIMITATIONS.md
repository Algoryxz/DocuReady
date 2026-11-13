# Known Limitations and Constraints

DocuReady is designed for rigorous pre-submission verification, but practical boundary conditions and technical constraints apply to the current version.

---

## 1. Document Quality and OCR Boundaries

- **Extremely Degraded Documents**: Documents with severe physical damage, water stains obscuring key numerals, resolution below 100 DPI, or motion blur exceeding 20 pixels cannot be reliably parsed.
  - *Mitigation*: The Calibration Engine detects low confidence and classifies the field as `UNCERTAIN`. The Safety Layer downgrades any potential rejection to `MANUAL REVIEW` rather than issuing an erroneous rejection.
- **Purely Handwritten Unstructured Documents**: Current OCR is optimized for printed, stamped, and hybrid form certificates. Fully cursive handwritten affidavits without tabular anchors will experience reduced extraction accuracy.
- **Language Scope**: Default extraction rules are tailored for English and bilingual English-Hindi certificates. Regional vernacular scripts (e.g. Malayalam, Odia, Gujarati) require additional Tesseract language packs not bundled in the base distribution.

---

## 2. Statutory Scope and Authority Boundaries

- **No Official Government Endorsement**: DocuReady is an independent pre-submission advisory tool. It does not replace the official scrutiny officer, and a `READY_TO_SUBMIT` outcome does not constitute a legal guarantee of scheme award.
- **State Rule Variations**: While core income ceilings (₹2.5 Lakhs) and matriculation age rules follow national standards, minor state-level scholarship rules may vary. Rule definitions should be reviewed against specific local state notifications.
- **Non-Standard Certificate Layouts**: Unofficial private notary affidavits or non-standard local templates may deviate from e-District anchor terminology, requiring manual operator review.

---

## 3. Computational and Platform Boundaries

- **Tesseract Binary Requirement**: When processing raster image PDFs, local Tesseract binaries (`tesseract.exe` or Unix `/usr/bin/tesseract`) must be installed and accessible in the system PATH.
- **Single-Node Execution**: The current reference implementation executes synchronously or as a local Streamlit application. Multi-worker queue backends (Celery / Redis) must be configured for high-concurrency enterprise deployments.
