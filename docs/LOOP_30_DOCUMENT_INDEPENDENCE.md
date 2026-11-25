# Loop 30 — Document Independence & Anti-Collusion Audit

## 1. Context & Architectural Challenge
In multi-document verification, treating a single re-scanned document as an independent second source introduces unwarranted corroboration, artificially inflating confidence scores. Conversely, misclassifying distinct real-world documents as duplicates (e.g. standard government forms sharing identical template text, or unrelated uploads sharing default scanner names like `invoice.pdf`) inappropriately suppresses legitimate corroboration.

`detect_document_independence` implements a multi-tier physical and semantic independence audit.

---

## 2. Hardened Detection Invariants

1. **Byte & Normalized Text Hash Integrity:**
   - If two documents share identical SHA-256 hashes or identical raw text token sequences, they are classified as `DUPLICATE`.
2. **Filename Disambiguation Guard:**
   - Generic filename collisions (such as `doc.pdf`, `scan001.pdf`, `invoice.pdf`) are explicitly disregarded if content hashes differ. Two distinct receipts with the default filename `receipt.pdf` are correctly recognized as `INDEPENDENT`.
3. **Template Boilerplate Protection:**
   - Standardized statutory forms (such as Odisha e-District caste certificates, Form 16, or Indian Income Tax returns) often exhibit $>95\%$ identical boilerplate header and legal footer text.
   - The detector isolates dynamic variable payload zones from boilerplate scaffolding, ensuring that two distinct applicants using the same government form are never falsely flagged as duplicate files.

---

## 3. Verification Test Suite Status
All independence audit cases execute with 100% accuracy:
- Renamed duplicates detected: `PASS`
- Re-scanned reflowed duplicates detected: `PASS`
- Generic filename collisions kept independent: `PASS`
- Standard template forms kept independent: `PASS`
