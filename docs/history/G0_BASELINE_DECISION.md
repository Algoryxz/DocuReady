# DocuReady — Gate G0 Baseline Environment Decision Proposal

**Decision Status:** `PENDING_DEEPTIMAN_DECISION`  
**Author:** Akriti (Platform & Baseline Delivery) with Susmita (Rules & Evaluation) & Deeptiman (Architecture Coordination)  
**Date:** 14 November 2026  
**Target Gate:** Gate G0 — Baseline Frozen  
**Repository:** `Algoryxz/DocuReady`  
**Base Commit:** `7b55bf829cfba21ee7d277c9b3c933b702f92671`  

---

## 1. Executive Summary & Context

Task **T0.1** characterised the baseline behaviour of DocuReady and resolved cross-platform path-separator discrepancies in the test harness (`tests/test_golden_baseline.py`). However, full test matrix execution on GitHub Actions CI across the declared supported runtimes (`>=3.10,<3.13`) has uncovered two fundamental environment discrepancies:

1. **PyMuPDF Version Conflict under Python 3.10:** `PyMuPDF 2.1` requires Python 3.11+ (`Requires-Python: >=3.11`), forcing Python 3.10 onto `PyMuPDF 1.28.2`, which produces different text search rect geometry and fails all 8 golden baseline packets.
2. **Tesseract OCR Noise Extraction on Packet 7:** The original golden snapshot recorded empty OCR fields (`raw_text = ""` and `mean_ocr_confidence = 0.0`) because the capture host's Tesseract state was unverified and `_ocr_page` silently swallowed `TesseractNotFoundError`. In Linux CI with Tesseract 5.5.0 installed, OCR extraction produces noisy text and non-zero confidence, failing `PKT_07_UNREADABLE_DOC`.

This document presents three concrete architectural options to resolve these discrepancies, freeze the baseline, and unblock Gate G0.

---

## 2. Verified CI Matrix Reality

In main CI run `43601998227` (executed on commit `7b55bf829cfba21ee7d277c9b3c933b702f92671` with `fail-fast: false`), all three matrix jobs completed and failed:

| Matrix Job | Test Results | Root Cause |
|---|---|---|
| **Python 3.10** (`job/132468320580`) | **70 passed, 8 failed** | `pip` resolved `pymupdf>=1.23.0` to `PyMuPDF 1.28.2`. Rect geometry and bounding-box float rounding differ from 2.1, causing bounding-box coordinate mismatches across all 8 golden baseline packets. |
| **Python 3.11** (`job/132468320304`) | **77 passed, 1 failed** | Installed `pymupdf==2.1`. All 7 native vector packets passed bit-for-bit. Single failure was `PKT_07_UNREADABLE_DOC` due to Tesseract 5.5.0 OCR output vs snapshot empty values. |
| **Python 3.12** (`job/132468320466`) | **77 passed, 1 failed** | Installed `pymupdf==2.1`. All 7 native vector packets passed bit-for-bit. Single failure was `PKT_07_UNREADABLE_DOC` due to Tesseract 5.5.0 OCR output vs snapshot empty values. |

### Historical Baseline Environment Status
- **Provenance:** `ENVIRONMENT_MANIFEST.md` and `T0.2.1_DEPENDENCY_AUDIT.md` were session scratch artifacts outside Git. In canonical Git history at commit `9a0d00c8c9e02b2697d52589aa04ca211ffaf441` (where the baseline was committed), the capture host's Tesseract binary state was **UNVERIFIED in tracked Git history**.
- **Silent Exception Handling:** In `src/docuready/ingest/extractor.py` lines 427–442:
  ```python
  try:
      ocr_data = pytesseract.image_to_data(
          img, output_type=pytesseract.Output.DICT
      )
  except Exception:
      pass
  ```
  This broad `except Exception: pass` silently swallowed `TesseractNotFoundError`, producing `raw_text = ""` and `mean_ocr_confidence = 0.0`. When Linux CI ran with Tesseract 5.5.0 installed, OCR lines were extracted (`raw_text = "[ZO ALITWNOD HOO - NVOS GALdNYHO"`, `mean_ocr_confidence = 0.502`). Because non-path OCR values cannot be normalized under the canonicalization contract, `PKT_07_UNREADABLE_DOC` failed comparison.

---

## 3. Architectural Options for Gate G0

### Option A: Retire Python 3.10, Validate Python 3.11–3.14, Select Compatible & Licensed PDF Backend (Recommended)

- **Description:**
  1. Retire Python 3.10 support. Note that Python 3.10 reached upstream End-Of-Life (EOL) on **1 October 2026**.
  2. Update `pyproject.toml` to `requires-python = ">=3.11,<3.15"`.
  3. Validate matrix compatibility across Python 3.11, 3.12, 3.13, and 3.14.
  4. Standardize on `pymupdf==2.1` (or its successor evaluated under T1.3) across all supported environments.
  5. Partition Golden Baseline Parity testing from OCR Integration testing (as detailed in §4).
- **Pros:**
  - Preserves exact bit-for-bit bounding-box parity with `GOLDEN_BASELINE.json` across 7 of 8 packets immediately without invalidating historical records.
  - Eliminates the `cp311-abi3` wheel resolution dilemma on older Python runtimes.
  - Aligns DocuReady with active Python release lifecycles.
- **Cons:**
  - Drops backwards compatibility for host environments running Python 3.10.

### Option B: Retain Python 3.10 Support via Older PyMuPDF

- **Description:**
  1. Retain `requires-python = ">=3.10,<3.13"` in `pyproject.toml`.
  2. Pin `pymupdf==1.28.2` across all Python environments (3.10, 3.11, 3.12).
  3. Invalidate and re-capture `GOLDEN_BASELINE.json` under PyMuPDF 1.28.2 bounding box coordinates.
- **Pros:**
  - Maintains compatibility with legacy Python 3.10 deployments.
- **Cons:**
  - Invalidates the frozen golden baseline snapshot and requires re-capturing all 8 packet hashes.
  - Forces the project onto an older PyMuPDF release branch despite Python 3.10 being upstream EOL.
  - Does not resolve the Tesseract OCR variance on packet 7.

### Option C: Fuzzy Geometry Comparison (Rejected)

- **Description:** Add coordinate rounding or bounding-box tolerance into `tests/test_golden_baseline.py` to reconcile PyMuPDF 1.28.2 and 2.1 differences.
- **Why Rejected:**
  - Violates the golden canonicalization contract (`tests/golden/legacy_v0/CANONICALIZATION_CONTRACT.md`), which strictly limits normalization to path separators (`\` -> `/`).
  - Loosening coordinate assertions conceals genuine PDF layout parsing defects and weakens regression guarantees.

---

## 4. Test Partitioning: Golden Parity vs OCR Integration (Task T0.2)

To maintain strict deterministic regression guarantees while handling non-deterministic OCR engine output:

1. **Preserve Packet 7 in Deterministic Regression Coverage:**
   - `PKT_07_UNREADABLE_DOC` must remain part of the golden baseline dataset inventory.
   - Do **NOT** normalize OCR text, confidence scores, or bounding boxes.
2. **Partitioning Strategy for Task T0.2:**
   - **Golden Baseline Parity (`tests/test_golden_baseline.py`):** Focuses on deterministic vector PDF extraction (Packets 1–6 and 8). Validates 100% bit-for-bit parity of text tokens, bounding boxes, and rule findings under the standardized PDF engine.
   - **OCR Integration Test Suite (`tests/test_ocr_integration.py`):** Formally assigned to Task **T0.2**. Exercises Tesseract OCR execution, multi-lingual language packs (`eng`, `ori`, `hin`), and degraded image handling on `PKT_07_UNREADABLE_DOC`. Uses semantic property assertions (e.g. verifying extraction state degrades gracefully to `UNREADABLE` or triggers uncertainty handling) rather than brittle bit-for-bit string matches across disparate Tesseract engine versions.
3. **Artifact Integrity:**
   - `tests/golden/legacy_v0/GOLDEN_BASELINE.json` SHA-256 remains verified and unchanged: `E8FB1A6B842A47089937777133DE79E1E7F704BEE591D5B4471A1A90BC8C5FA9`.

---

## 5. PyMuPDF Licensing Notice (Requirement for Task T1.3)

- **License Context:** `PyMuPDF` is dual-licensed under GNU AGPLv3 and commercial terms from Artifex Software, Inc. DocuReady declares `Apache-2.0` in `pyproject.toml`.
- **Architectural Risk:** AGPLv3 contains strong copyleft requirements that apply when the software is operated as a network service. While DocuReady currently operates as a local-first offline CLI and desktop UI, public distribution or SaaS deployment could trigger copyleft obligations.
- **Scope Notice:** This statement constitutes an architectural risk identification, not a definitive legal opinion.
- **Next Steps:** A formal licensing audit and technical evaluation of permissive alternative PDF backends (e.g. `pypdf`, `pdfplumber`, `pdfminer.six`) is scheduled under Gate **G1 / Task T1.3** (`docs/STATUS.md`).

---

## 6. Repository Governance & Branch Protection Recommendation

- **Observed Workflow State:** PR #5 was merged into `main` at commit `7b55bf829cfba21ee7d277c9b3c933b702f92671` while all three CI matrix jobs (`test (3.10)`, `test (3.11)`, `test (3.12)`) were failing.
- **Finding:** The `main` branch currently has no branch protection rules or required status checks configured in GitHub repository settings.
- **Recommendation:** Once Gate G0 is unblocked and green CI is achieved:
  1. Enable GitHub branch protection on `main`.
  2. Require linear history or pull request reviews before merging.
  3. Require CI matrix jobs (`test (...)`) to pass before merge authorization.

---

## 7. Recommendation & Handoff

Akriti and Susmita recommend **Option A** as the technically sound path to freeze the baseline environment and unblock Gate G0.

This proposal is submitted to Deeptiman for formal product and architecture review:

> **Decision Status:** `PENDING_DEEPTIMAN_DECISION`  
> *No support-policy changes or packaging modifications have been applied. Execution awaits Deeptiman's formal decision.*
