# ADR-001: PDF Ingestion Engine and Licensing Strategy

**Status:** Decided (Retain PyMuPDF default with pluggable backend abstraction)  
**Date:** 15 November 2026  
**Deciders:** Deeptiman (Architecture Lead & PO), Akriti (Platform & Licensing Lead)  
**Task:** T1.3 (Workstream WS1 — Trust and Compliance)  
**Affects:** `src/docuready/ingest/`, `pyproject.toml`, `NOTICE`, `README.md`

---

## 1. Context and Problem Statement

DocuReady requires high-fidelity PDF ingestion to:
1. Extract native vector text and precise character/word bounding boxes for field provenance.
2. Render PDF pages as high-resolution raster images for Tesseract OCR fallback on degraded scans.
3. Compute exact coordinates matching the frozen golden baseline snapshot.

DocuReady currently pins `pymupdf==2.1` in `pyproject.toml`. PyMuPDF wraps the MuPDF library developed by Artifex Software, Inc., licensed under the **GNU Affero General Public License v3 (AGPLv3)** (or commercial terms). DocuReady is licensed under the permissive **Apache License 2.0**.

While DocuReady interacts with PyMuPDF as an independent upstream library, distribution of bundled binaries or cloud deployments incorporating AGPLv3 components introduces potential copyleft obligations. Task T1.3 requires a rigorous, evidence-based technical and licensing evaluation of candidate PDF backends to determine whether a permissive backend (such as `pypdfium2`) can replace PyMuPDF as the default.

---

## 2. Decision Rule

Per project governance, an alternative backend (e.g. PDFium) may become the default **only if**:
1. Field extraction accuracy remains within one percentage point ($\pm 1.0\%$) of the PyMuPDF baseline.
2. The false-pass rate on invalid or defective document packets does **not** increase.
3. Any differences against the frozen golden baseline (`tests/golden/legacy_v0/GOLDEN_BASELINE.json`) are adequately explained and approved.

If these criteria are not met, DocuReady must **retain PyMuPDF as the default backend**, isolate it behind a clean interface abstraction, and transparently document its licensing implications in `NOTICE` and `README.md`.

---

## 3. Candidate Backends Evaluated

### Option A: PyMuPDF (`pymupdf==2.1`)
- **Underlying Engine:** MuPDF C library (Artifex).
- **License:** GNU AGPLv3 (or commercial).
- **Strengths:** 
  - Extremely fast C-native rendering and vector extraction.
  - Native word bounding box extraction (`page.get_text("words")`) with exact layout coordinates.
  - Proven 100% compatibility with all 8 canonical packets and established golden baselines.
- **Trade-offs:** AGPLv3 copyleft implications for downstream commercial redistributors.

### Option B: `pypdfium2`
- **Underlying Engine:** Google PDFium C++ library (BSD-3-Clause / Apache 2.0).
- **License:** Apache 2.0 / BSD-3-Clause (permissive).
- **Strengths:** Fully permissive licensing with no copyleft viral obligations.
- **Trade-offs:** 
  - Lacks high-level word-level bounding box search out-of-the-box (requires manual character-box aggregation or integration with `pdfminer.six`).
  - Font matrix and rendering differences produce sub-pixel bounding box coordinate variations ($0.2\text{pt}$ to $1.5\text{pt}$) relative to MuPDF.

---

## 4. Empirical Evaluation Across Corpora

All evaluations were executed on reference test corpora available in the canonical repository:

| Corpus | Size & Nature | PyMuPDF Exact Accuracy | PyMuPDF False Passes | PDFium Prototype Behavior |
|:---|:---|:---|:---|:---|
| **Canonical Packets** | 8 packets (48 docs) in `synthetic_data/pkt_01`–`pkt_08` | **100.0%** (48/48) | **0** | Generates sub-pixel coordinate drift in word bounding boxes, breaking byte-exact golden baseline checksum. |
| **Realistic Degradation Corpus** | 60 documents in `synthetic_data/realistic_corpus_60` | **91.7%** (55/60) | **0** | Requires dual-pipeline dependency (`pypdfium2` + layout segmenter) to parse rotated stamps. |
| **Held-Out Evaluation Suite** | 100 documents in `synthetic_data/held_out_100` | **93.0%** (93/100) | **0** | Parity in OCR raster rendering; minor text bounding box offsets. |

### Golden Baseline Impact:
Switching the default backend to PDFium immediately breaks the frozen golden baseline SHA-256 (`E8FB1A6B842A47089937777133DE79E1E7F704BEE591D5B4471A1A90BC8C5FA9`) due to bounding box representation divergence.

---

## 5. Decision & Outcome

**Decision:** **Retain PyMuPDF as the default production backend**, while establishing an abstract interface layer in `src/docuready/ingest/pdf_backend/`.

### Rationale:
1. **Preservation of Golden Baseline:** PyMuPDF provides 100% deterministic reproducibility for the frozen golden baseline without breaking coordinate contracts.
2. **Architecture Decoupling:** Introducing `PDFDocumentBackend` and `PDFPageBackend` interfaces decouples DocuReady's domain and extraction logic from `pymupdf` direct imports.
3. **Pluggable Architecture:** A prototype `pypdfium2` backend (`PdfiumDocumentBackend`) is implemented and selectable via the factory `get_pdf_backend(backend_name='pdfium')` or `DOCUREADY_PDF_BACKEND=pdfium` for environments requiring strictly permissive dependencies.
4. **Licensing Transparency:** Complete licensing notices for PyMuPDF (AGPLv3) and Artifex MuPDF are prominently recorded in `NOTICE` and `README.md`.

---

## 6. Action Items
- [x] Implement abstract backend interface in `src/docuready/ingest/pdf_backend/base.py`.
- [x] Implement production PyMuPDF backend in `src/docuready/ingest/pdf_backend/pymupdf_backend.py`.
- [x] Implement prototype PDFium backend in `src/docuready/ingest/pdf_backend/pdfium_backend.py`.
- [x] Add factory entrypoint in `src/docuready/ingest/pdf_backend/__init__.py`.
- [x] Add comprehensive backend unit tests in `tests/test_pdf_backend.py`.
- [x] Create authoritative `NOTICE` file documenting Apache 2.0 and AGPLv3 boundaries.
