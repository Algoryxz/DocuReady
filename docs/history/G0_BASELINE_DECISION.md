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

1. **PyMuPDF Version Conflict under Python 3.10:** `PyMuPDF 2.1` declares `Requires-Python: >=3.11` on PyPI, forcing Python 3.10 onto `PyMuPDF 1.28.2`, which produces different text search rect geometry and fails all 8 golden baseline packets.
2. **Tesseract OCR Discrepancy on Packet 7:**
   - **Observed fact:** The historical baseline snapshot (`GOLDEN_BASELINE.json`) records empty OCR fields (`raw_text = ""` and `mean_ocr_confidence = 0.0`) for `pkt_07_unreadable_doc/income_cert.pdf`.
   - **Observed fact:** Current Linux CI with Tesseract 5.5.0 installed extracts non-empty OCR lines (`raw_text = "[ZO ALITWNOD HOO - NVOS GALdNYHO"`) and a confidence value of `0.502`.
   - **Source behavior:** `_ocr_page` in `src/docuready/ingest/extractor.py` handles OCR exceptions by substituting an empty data structure when execution fails.
   - **Unknown:** Whether Tesseract was actually installed on the historical capture host (commit `9a0d00c8c9e02b2697d52589aa04ca211ffaf441`), as environment manifests exist only in untracked session scratch storage outside Git.
   - **Conclusion:** The historical cause of the empty values in the golden snapshot remains **UNVERIFIED**. What is established is that running with Tesseract 5.5.0 on Linux extracts non-empty text, triggering a golden comparison failure because non-path values cannot be normalized under the canonicalization contract.

This document presents three concrete architectural options to resolve these discrepancies, freeze the baseline, and unblock Gate G0.

---

## 2. Verified CI Matrix Reality

In main CI run `43601998227` (executed on commit `7b55bf829cfba21ee7d277c9b3c933b702f92671` with `fail-fast: false`), all three matrix jobs completed and failed:

| Matrix Job | Test Results | Root Cause |
|---|---|---|
| **Python 3.10** (`job/132468320580`) | **70 passed, 8 failed** | `pip` resolved `pymupdf>=1.23.0` to `PyMuPDF 1.28.2`. Rect geometry and bounding-box float rounding differ from 2.1, causing bounding-box coordinate mismatches across all 8 golden baseline packets. |
| **Python 3.11** (`job/132468320304`) | **77 passed, 1 failed** | Installed `pymupdf==2.1`. All 7 native vector packets passed bit-for-bit. Single failure was `PKT_07_UNREADABLE_DOC` due to Tesseract 5.5.0 OCR output vs snapshot empty values. |
| **Python 3.12** (`job/132468320466`) | **77 passed, 1 failed** | Installed `pymupdf==2.1`. All 7 native vector packets passed bit-for-bit. Single failure was `PKT_07_UNREADABLE_DOC` due to Tesseract 5.5.0 OCR output vs snapshot empty values. |

### Historical Baseline Environment & Extractor Exception Architecture
- **Provenance:** `ENVIRONMENT_MANIFEST.md` and `T0.2.1_DEPENDENCY_AUDIT.md` were session scratch artifacts outside Git. In canonical Git history at commit `9a0d00c8c9e02b2697d52589aa04ca211ffaf441` (where the baseline was committed), the capture host's Tesseract binary state and the historical cause of the empty values remain **UNVERIFIED in tracked Git history**.
- **Actual Source Behavior in `_ocr_page`:** In `src/docuready/ingest/extractor.py` (lines 151–180):
  ```python
  def _ocr_page(page: pymupdf.Page, dpi: int = 200) -> PageOCRData:
      # ... [pixmap rendering and image preparation] ...
      try:
          osd = pytesseract.image_to_osd(img, timeout=OCR_TIMEOUT_SECONDS)
          rot_match = [line for line in osd.split("\n") if "Rotate:" in line]
          if rot_match:
              rot = int(rot_match[0].split(":")[1].strip())
              if rot in [90, 180, 270]:
                  img = img.rotate(360 - rot, expand=True)
                  rot_applied = rot
      except Exception:
          pass

      try:
          data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, timeout=OCR_TIMEOUT_SECONDS)
      except Exception:
          data = {"text": [], "conf": [], "left": [], "top": [], "width": [], "height": []}

      return PageOCRData(data, dpi=dpi, rotation_applied=rot_applied)
  ```
  Lines 164–173 catch OSD exceptions and `pass`. Lines 175–179 catch data extraction exceptions and substitute an empty data dictionary. When OCR execution fails (e.g., if Tesseract is missing, times out, or encounters an internal fault), empty OCR data is returned. While this explains how empty values can arise programmatically, it does not prove what was installed on the historical capture host. In current Linux CI with Tesseract 5.5.0 installed, OCR extraction produces non-empty output, causing a mismatch with the baseline snapshot.

---

## 3. Architectural Options for Gate G0

### Option A: Retire Python 3.10, Validate Python 3.11–3.14, Select Compatible & Licensed PDF Backend (Recommended)

- **Description:**
  1. Retire Python 3.10 support. Note that Python 3.10 reached upstream End-Of-Life (EOL) on **1 October 2026**.
  2. Update `pyproject.toml` to `requires-python = ">=3.11,<3.15"`.
  3. Validate matrix compatibility across Python 3.11, 3.12, 3.13, and 3.14. (Evidence currently demonstrates parity on Python 3.11 and 3.12; Python 3.13 and 3.14 remain to be validated).
  4. Standardize on `pymupdf==2.1` as a provisional technical baseline candidate across supported environments to maintain geometric reproducibility, while explicitly recognizing that its licensing acceptability remains unsettled and pending review under Task T1.3.
  5. Propose partitioning Golden Baseline Parity testing from OCR Integration testing (as detailed in §4).
- **Pros:**
  - Preserves exact bit-for-bit bounding-box parity with `GOLDEN_BASELINE.json` across 7 of 8 packets on Python 3.11 and 3.12 immediately without invalidating historical records.
  - Eliminates the `cp311-abi3` wheel resolution dilemma on older Python runtimes.
  - Aligns DocuReady with active Python release lifecycles.
- **Cons & Qualifications:**
  - Drops backwards compatibility for host environments running Python 3.10.
  - Python 3.13 and 3.14 runtime compatibility remains to be verified once added to the matrix.
  - **Provisional Status:** PyMuPDF 2.1 serves strictly as a provisional technical baseline candidate to freeze reproducible geometry. The final PDF backend and licensing decision is NOT settled; it remains subject to the formal Task T1.3 evaluation and ADR. Option A remains a recommendation pending Deeptiman's formal acceptance.

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

## 4. Test Partitioning: Golden Parity vs OCR Integration (Proposed T0.2 Scope Extension)

To maintain strict deterministic regression guarantees while handling non-deterministic OCR engine output across platforms:

1. **Preserve Packet 7 in Deterministic Regression Coverage:**
   - `PKT_07_UNREADABLE_DOC` must remain part of the golden baseline dataset inventory.
   - Do **NOT** normalize OCR text, confidence scores, or bounding boxes.
2. **Proposed Partitioning Strategy for Task T0.2 (Subject to Team Acceptance):**
   - **Current T0.2 Baseline Requirements:** Task T0.2's core scope remains verifying and adding Odia (`ori`) and Hindi (`hin`) language pack support to CI alongside English (`eng`), and proving OCR tests run in automated workflows.
   - **Proposed Scope Extension:** Partition test responsibilities so that:
     - **Golden Baseline Parity (`tests/test_golden_baseline.py`):** Focuses on deterministic vector PDF extraction (Packets 1–6 and 8). Validates 100% bit-for-bit parity of text tokens, bounding boxes, and rule findings under the standardized PDF engine.
     - **OCR Integration Test Suite (`tests/test_ocr_integration.py`):** Proposed as part of T0.2 to test Tesseract OCR execution, multi-lingual language packs (`eng`, `ori`, `hin`), and degraded image handling on `PKT_07_UNREADABLE_DOC`. Uses semantic property assertions (e.g. verifying extraction state degrades gracefully to `UNREADABLE` or triggers uncertainty handling) rather than brittle bit-for-bit string matches across disparate Tesseract engine versions.
3. **Artifact Integrity:**
   - `tests/golden/legacy_v0/GOLDEN_BASELINE.json` SHA-256 remains verified and unchanged: `E8FB1A6B842A47089937777133DE79E1E7F704BEE591D5B4471A1A90BC8C5FA9`.

---

## 5. PyMuPDF Licensing Notice (Requirement for Task T1.3)

- **License Context:** `PyMuPDF` is dual-licensed under GNU AGPLv3 and commercial terms from Artifex Software, Inc. DocuReady declares `Apache-2.0` in `pyproject.toml`.
- **Provisional Technical Baseline Candidate:** PyMuPDF 2.1 is proposed strictly as a provisional technical baseline candidate to resolve geometry reproducibility in Gate G0. Adopting it as a provisional baseline does **not** constitute an accepted or settled licensing decision.
- **Architectural Risk:** AGPLv3 contains strong copyleft requirements that apply when the software is operated as a network service. While DocuReady currently operates as a local-first offline CLI and desktop UI, public distribution or SaaS deployment could trigger copyleft obligations.
- **Scope Notice:** This statement constitutes an architectural risk identification, not a definitive legal opinion.
- **Next Steps:** Neither the final PDF backend nor its licensing acceptability is settled. A formal licensing audit, ADR (Architecture Decision Record), and technical evaluation of permissive alternative PDF backends (e.g. `pypdf`, `pdfplumber`, `pdfminer.six`) is scheduled under Gate **G1 / Task T1.3** (`docs/STATUS.md`).

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

Akriti and Susmita recommend **Option A** as a technical recommendation to freeze the baseline environment and unblock Gate G0.

This recommendation is explicitly submitted to Deeptiman for formal product and architecture decision:

> **Decision Status:** `PENDING_DEEPTIMAN_DECISION`
> *Option A is a recommendation only, not an accepted decision. No support-policy changes, packaging modifications, or final backend/licensing decisions have been implemented or settled. Execution awaits Deeptiman's explicit architectural decision.*
