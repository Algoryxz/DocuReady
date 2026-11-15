# ADR-001: PDF Ingestion Engine and Licensing Strategy

**Status:** Decided (Retain PyMuPDF default with pluggable backend abstraction)  
**Date:** 15 November 2026  
**Deciders:** Deeptiman (Architecture Lead & PO), Akriti (Platform & Licensing Lead)  
**Task:** T1.3 (Workstream WS1 — Trust and Compliance)  
**Affects:** `src/docuready/ingest/`, `pyproject.toml`, `NOTICE`, `README.md`, `scripts/evaluate_pdf_backends.py`

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

## 3. Detailed Licensing Matrix & Candidate Backends

The table below delineates the exact licensing boundaries between Python wrapper packages and underlying native rendering engines:

| Component | Layer | Author / Vendor | License | Copyleft Obligations |
| :--- | :--- | :--- | :--- | :--- |
| **DocuReady** | Application Core | HackNation DocuReady Authors | **Apache-2.0** | Permissive |
| **PyMuPDF** | Python Bindings | Artifex Software, Inc. | **GNU AGPLv3** | Strong copyleft for networked/redistributed derivatives |
| **MuPDF** | C Rendering Engine | Artifex Software, Inc. | **GNU AGPLv3** / Commercial | Dual-licensed; AGPLv3 applies unless commercial license purchased |
| **pypdfium2** | Python Bindings | pypdfium2 Team | **Apache-2.0 / BSD-3-Clause** | Permissive dual-license |
| **PDFium** | Native C++ Engine | Google LLC / Foxit | **3-Clause BSD / Apache-2.0** | Permissive open-source license |

### Option A: PyMuPDF (`pymupdf==2.1`)
- **Underlying Engine:** MuPDF C library (Artifex).
- **License:** GNU AGPLv3 (or commercial from Artifex).
- **Strengths:** 
  - Extremely fast C-native rendering and vector extraction.
  - Native word bounding box extraction (`page.get_text("words")`) with exact layout coordinates.
  - Proven 100% compatibility with all 8 canonical packets and established golden baselines.
- **Trade-offs:** AGPLv3 copyleft implications for downstream commercial redistributors if deployed without isolation.

### Option B: `pypdfium2`
- **Underlying Engine:** Google PDFium C++ library (BSD-3-Clause / Apache 2.0).
- **License:** Apache 2.0 / BSD-3-Clause (permissive).
- **Strengths:** Fully permissive licensing with no copyleft viral obligations.
- **Trade-offs:** 
  - Lacks native word-level bounding box search out-of-the-box (requires manual character-box aggregation or external layout engine).
  - Font matrix and rendering differences produce sub-pixel bounding box coordinate variations ($0.2\text{pt}$ to $1.5\text{pt}$) relative to MuPDF.
  - To maintain provenance integrity, `PdfiumPageBackend.get_words()` explicitly raises `NotImplementedError` rather than fabricating synthetic or zero-coordinate bounding boxes.

---

## 4. Empirical Evaluation Across Corpora & Reproducible Benchmark

All evaluations were executed on reference test corpora available in the canonical repository using the reproducible evaluation script `scripts/evaluate_pdf_backends.py`:

```bash
# Evaluate across canonical packets:
python scripts/evaluate_pdf_backends.py --corpus synthetic_data/pkt_01_clean

# Evaluate across 60-document degradation corpus:
python scripts/evaluate_pdf_backends.py --corpus synthetic_data/realistic_corpus_60

# Evaluate across 100-document held-out corpus:
python scripts/evaluate_pdf_backends.py --corpus synthetic_data/held_out_100

# JSON output mode:
python scripts/evaluate_pdf_backends.py --corpus synthetic_data --json
```

### Empirical Results Summary:

Detailed evaluation methodology, exact versions, and breakdown are recorded in [eval/reports/backend_comparison.md](../../eval/reports/backend_comparison.md):

| Corpus | Size & Nature | PyMuPDF Exact Accuracy | PyMuPDF False Passes | Mean Latency / Doc | PDFium Prototype Status |
|:---|:---|:---|:---|:---|:---|
| **Canonical Packets** | 8 packets (48 docs) in `synthetic_data/pkt_01`–`pkt_08` | **100.0%** (48/48) | **0** | ~6.9 ms | **UNVERIFIED**: `get_words()` raises `NotImplementedError`; sub-pixel coordinate offsets break golden baseline. |
| **Realistic Degradation Corpus** | 60 documents in `synthetic_data/realistic_corpus_60` | **91.7%** (55/60) | **0** | ~11.5 ms | **UNVERIFIED**: Requires layout segmenter for rotated stamps. |
| **Held-Out Evaluation Suite** | 100 documents in `synthetic_data/held_out_100` | **93.0%** (93/100) | **0** | ~11.2 ms | **UNVERIFIED**: End-to-end vector extraction requires word provenance. |

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

## 6. Commercial Migration Path (Non-AGPL Distribution)

For enterprise deployers or commercial distributors who cannot accept AGPLv3 copyleft terms, DocuReady supports two compliant deployment architectures:

1. **Dual-License Commercial MuPDF License:** Procure a commercial proprietary MuPDF redistribution license directly from Artifex Software, Inc. (exempts deployment from AGPLv3 provisions).
2. **Permissive Backend Switch (`DOCUREADY_PDF_BACKEND=pdfium`):**
   - Install `pypdfium2` in the host environment.
   - Set environment variable `DOCUREADY_PDF_BACKEND=pdfium`.
   - The ingestion subsystem routes PDF rendering and text range search through PDFium, completely eliminating AGPLv3 native libraries from the runtime environment.
   - Note: In this mode, word bounding box provenance (`get_words()`) raises `NotImplementedError` until a permissive layout segmenter is integrated.

---

## 7. Action Items
- [x] Implement abstract backend interface in `src/docuready/ingest/pdf_backend/base.py`.
- [x] Implement production PyMuPDF backend in `src/docuready/ingest/pdf_backend/pymupdf_backend.py`.
- [x] Implement prototype PDFium backend in `src/docuready/ingest/pdf_backend/pdfium_backend.py`.
- [x] Eliminate dummy zero coordinates in `PdfiumPageBackend.get_words()`.
- [x] Add factory entrypoint in `src/docuready/ingest/pdf_backend/__init__.py`.
- [x] Refactor `extractor.py` to utilize `get_pdf_backend()` with full backward compatibility.
- [x] Provide reproducible benchmark script `scripts/evaluate_pdf_backends.py`.
- [x] Commit empirical comparative evaluation report `eval/reports/backend_comparison.md`.
- [x] Add comprehensive backend unit tests in `tests/test_pdf_backend.py`.
- [x] Update authoritative `NOTICE` file documenting Apache 2.0, BSD-3, and AGPLv3 boundaries.
