# DocuReady Loop 32 Failure Mode & Risk Analysis

**Programme:** DocuReady Product Excellence  
**Milestone:** Loop 32  
**Focus:** Boundary Conditions, Edge-Cases, and Failure Risk Register  
**Date:** 2026-11-25  

---

## 1. Subsystem Failure Mode Matrix

| Failure Mode ID | Subsystem | Trigger Condition | Consequence | Mitigation Status |
| :--- | :--- | :--- | :--- | :--- |
| **FAIL-01** | PDF Ingest | Non-standard PDF page object returning tuple rects | `AttributeError` crashing ingestion | **Mitigated in L32** (`hasattr` check) |
| **FAIL-02** | Cross-Doc Normalization | ISO `YYYY-MM-DD` vs `DD/MM/YYYY` comparison | Spurious contradiction | **Mitigated in L32** (ISO regex canonicalizer) |
| **FAIL-03** | Identifier Validation | Verhoeff check in `normalizer.py` | False rejection of valid Aadhaar | **Mitigated in L32** (Table parity restored) |
| **FAIL-04** | Desktop Workspace | Uploading multiple files named `invoice.pdf` | Silent overwrite in packet directory | **Mitigated in L32** (`seenNames` disambiguation) |
| **FAIL-05** | Region OCR | Landscape PDF orientation (width > height) | Bounding box spatial shift | **Documented Debt** (Dynamic width pending) |
| **FAIL-06** | Table Extraction | Narrow-gutter columns (< 35px) | Merged multi-column text | **Documented Debt** (Adaptive gutter pending) |

---

## 2. Risk Level Evaluation
- All discovered high-severity crashing or data-corruption risks have been eliminated.
- The remaining items are non-crashing spatial layout edge cases documented in the technical debt ledger.
