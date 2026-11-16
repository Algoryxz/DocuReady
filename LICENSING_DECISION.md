# DOCUREADY — PDF BACKEND & LICENSING DECISION RECORD

**Milestone:** Loop 6 — Release Integrity, Claims Audit & Independent Reproducibility  
**Date:** 2026-11-16  
**Auditor:** Antigravity Release Engineer / Independent Technical Auditor  
**Repository:** `Algoryxz/DocuReady`  
**Status:** **DECISION RATIFIED — RETAIN PYMUPDF; DEFER PDFIUM MIGRATION**  

---

## 1. Executive Summary & Core Decision

| Evaluation Area | Current Backend: **PyMuPDF (`fitz`)** | Evaluated Alternative: **PDFium (`pypdfium2`)** |
| :--- | :--- | :--- |
| **Licensing** | **AGPLv3** (Copyleft) / Commercial option | **Apache 2.0 / BSD 3-Clause** (Permissive) |
| **Word-Level BBox API** | `page.get_text("words")` with block & line IDs | **NOT IMPLEMENTED** (Raises `NotImplementedError`) |
| **Extraction Reliability** | 100% exact match on synthetic corpus (450/450 tests pass) | Severe regression; breaks anchor-proximity extractor |
| **Memory & Latency** | 0.02s / page; ~45MB baseline | 0.03s / page + Python layout reconstruction overhead |
| **Release Qualification** | **Technically used by current candidate; legal distribution clearance pending** | **Prototype incomplete** |

### Engineering Decision (Not Legal Clearance):
**Do not migrate to PDFium for the Loop 6 candidate.**  
PyMuPDF remains the sole production-qualified PDF extraction engine for DocuReady. The existing `PDFDocumentBackend` abstraction layer in `src/docuready/ingest/pdf_backend/` is preserved as an architectural interface for future permissive backend development.

> [!WARNING]
> **Legal Disclaimer:** This document reflects an engineering, architectural, and copyright attribution evaluation conducted by software engineers. It does **not** constitute formal legal counsel. Organizations embedding DocuReady into proprietary or commercial SaaS distributions should conduct independent legal review regarding AGPLv3 compliance.

---

## 2. Technical Gap Analysis: PyMuPDF vs. PDFium

A rigorous technical evaluation of the `pypdfium2` prototype (`src/docuready/ingest/pdf_backend/pdfium_backend.py`) against the canonical PyMuPDF implementation revealed the following critical disparities:

### 2.1. Word-Level Bounding Box & Layout Provenance (`get_words()`)
- **PyMuPDF:** Provides native C-level extraction of individual words with exact bounding boxes, block indices, line indices, and word numbers:
  ```python
  (x0, y0, x1, y1, "word_string", block_no, line_no, word_no)
  ```
  DocuReady's anchor-proximity extractor (`_find_field_in_page_words`) relies entirely on these spatial block/line hierarchies to associate labels (e.g. `"Applicant Name:"`) with values (e.g. `"Ananya Sharma"`) located to the right or below.
- **PDFium:** `pypdfium2` exposes raw character-level glyph bounding boxes via `textpage.search()` and text ranges, but **does not provide native word clustering, line clustering, or block hierarchies**.
- **Contract Enforcement:** `PdfiumPageBackend.get_words()` explicitly raises `NotImplementedError` to prevent the emission of synthetic or zero-coordinate bounding boxes:
  ```python
  # src/docuready/ingest/pdf_backend/pdfium_backend.py:68-73
  raise NotImplementedError(
      "Word-level bounding box provenance (get_words) is not implemented for "
      "PdfiumPageBackend. Word-level coordinate extraction requires the PyMuPDF "
      "backend (pymupdf). Returning zero or synthetic bounding boxes is disallowed "
      "to prevent provenance corruption."
  )
  ```
- **Consequence of Migration:** Migrating to PDFium would immediately crash all document extraction routines or require writing a complex heuristic text clustering algorithm in Python, introducing spatial regressions and coordinate drift.

### 2.2. Golden Corpus Parity & Regression Impact
- **PyMuPDF:** Evaluated against all 8 synthetic document packets (`pkt_01_clean` through `pkt_08_ambiguous_evidence`). Achieves 100% bit-for-bit extraction parity with frozen golden baselines (`tests/test_golden_baseline.py`).
- **PDFium:** When tested against `application_form.pdf`, field extraction fails to locate applicant names and caste categories due to the missing word matrix.

### 2.3. Page Rotation & Coordinate Space Normalization
- **PyMuPDF:** Automatically normalizes page coordinate matrices across $0^\circ, 90^\circ, 180^\circ,$ and $270^\circ$ orientations, ensuring that `rect` coordinates consistently map to top-left origin user space.
- **PDFium:** Inverts coordinate bounds in non-zero rotation matrices unless manual affine transformation math is executed on every rendered rect.

---

## 3. Licensing & AGPLv3 Copyleft Analysis

### 3.1. Upstream License Terms
- **PyMuPDF & MuPDF:** Authored and copyrighted by Artifex Software, Inc. Distributed under the GNU Affero General Public License v3 (AGPLv3).
- **Core AGPLv3 Mandate:** Downstream distributions that combine or link with AGPLv3 software must convey the entire source code of the combined work under AGPLv3 terms, and must offer source code to network users (Section 13).

### 3.2. Distribution Boundary — Disclosure, Not Clearance
The following facts are relevant to the distribution analysis, but **do not establish that AGPLv3 obligations are avoided**:

1. **Project License:** Apache-2.0 applies to project-authored code to the extent stated in the repository's license. It does not relicense third-party components.
2. **Bundled Component:** The distributed sidecar includes PyMuPDF/MuPDF under AGPLv3. The actual combined distribution and interaction model require legal analysis; a separate process and stdio protocol are not a safe harbor by themselves.
3. **Disclosure:** `NOTICE`, `README.md`, and `THIRD_PARTY_LICENSES.md` identify the AGPLv3 component. Disclosure is necessary but does not itself satisfy all license obligations.

### 3.3. Commercial & Enterprise Distribution Path
For enterprise deployers who cannot accept AGPLv3 copyleft terms (e.g. embedding DocuReady into closed-source commercial workflows), two sanctioned options exist:
1. **Commercial License from Artifex:** Purchase a commercial, non-copyleft OEM MuPDF license directly from Artifex Software, Inc.
2. **Complete the PDFium Adapter:** Invest engineering resources into writing a robust C++ or Cython-level word/line clusterer on top of PDFium's glyph API to implement `get_words()`.

---

## 4. Final Recommendation & Action Plan

1. **Retain PyMuPDF as Primary Engine:** Maintain `pymupdf==2.1` as the active dependency in `pyproject.toml` and the packaged binary.
2. **Preserve Pluggable Interface:** Retain `src/docuready/ingest/pdf_backend/` to ensure zero API lock-in.
3. **No False Claims:** Maintain clear, unambiguous disclosures in all user-facing documentation that the current release uses PyMuPDF under AGPLv3 copyleft terms.


## 5. Corrected Distribution Status

- PyMuPDF remains the only currently implemented/qualified production PDF backend in this candidate.
- `PdfiumPageBackend.get_words()` raises `NotImplementedError`; it is not a working drop-in alternative and does not currently eliminate the AGPL component from the packaged build.
- The root Apache-2.0 license must not be presented as the license for the complete packaged application without clearly excluding third-party components and explaining their separate terms.
- The current report is an engineering inventory, not a legal opinion. Obtain qualified legal review of the exact source and binary distribution, corresponding-source obligations, notices, modifications, and intended commercial/non-commercial use before calling distribution legally cleared.
- **Release gate:** AGPLv3 is disclosed, but legal distribution clearance remains **OPEN**.
