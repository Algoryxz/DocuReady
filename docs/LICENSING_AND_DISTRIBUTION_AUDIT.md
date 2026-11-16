# DocuReady Desktop — Licensing and Distribution Audit

**Document version:** 1.0.0  
**Audit date:** 16 November 2026  
**Audited branch:** `feat/electron-desktop-foundation`  
**Classification:** Release-Critical Legal and Technical Assessment  

---

## 1. Executive Summary

This document provides a comprehensive dependency licensing audit, distribution risk analysis, and backend architectural evaluation for the DocuReady desktop application.

DocuReady combines an Electron/React front-end with a local Python statutory audit engine and local Tesseract OCR runtime. Before binaries can be distributed to end users (as `.exe`, `.dmg`, `.AppImage`, or installers), all direct and transitive licensing obligations must be satisfied.

### The Release-Critical Gate: PyMuPDF Licensing
The primary release blocker is **PyMuPDF** (`pymupdf==2.1`), which wraps Artifex Software's **MuPDF** C library.
- MuPDF and PyMuPDF are **dual-licensed under GNU AGPL-3.0 and commercial terms**.
- Distributing a packaged desktop application containing PyMuPDF under proprietary or non-AGPL terms without a commercial license from Artifex is a copyright infringement risk.
- **Project Owner Decision Gate:** The project owner must select between **Option A (Commercial License)**, **Option B (AGPL-3.0 Distribution)**, or **Option C (PDFium Parity Migration)**.
- **Current Technical Reality:** The alternative backend (`pypdfium2` / PDFium) does not yet implement word-level bounding-box extraction with reading order and block/line structure (`get_words()` raises `NotImplementedError`). Replacing PyMuPDF today would corrupt evidence provenance and break golden baselines. Therefore, PyMuPDF must remain the default engine backend until parity is proven.

---

## 2. Complete Dependency License Inventory

### 2.1 Python Engine Dependencies

| Component | Version | License | Upstream Author / Copyright | Distribution Obligations | Bundling / Proprietary Implications |
|---|---|---|---|---|---|
| **PyMuPDF (`fitz`)** | 2.1 | **GNU AGPL-3.0** (or Commercial) | Artifex Software, Inc. | If distributed under AGPL, full source code of the entire combined work must be provided under AGPL-3.0. | **CRITICAL BLOCKER** for proprietary distribution. Requires commercial license or AGPL copyleft release. |
| **MuPDF (embedded C lib)** | 1.24+ | **GNU AGPL-3.0** (or Commercial) | Artifex Software, Inc. | Bundled inside PyMuPDF binary wheels. | Governed by Artifex dual-licensing policy. |
| **pypdfium2** | 4.30.0+ | **Apache-2.0** OR **BSD-3-Clause** | Mara-D / pypdfium2 contributors | Include copyright notice and license text. | Permissive. Freely distributable in commercial/proprietary binaries. |
| **PDFium** | Chrome V8 baseline | **Apache-2.0** / **BSD-3-Clause** | Google LLC & PDFium Authors | Include BSD license and attribution notices. | Permissive. |
| **Pydantic** | 2.x | **MIT** | Samuel Colvin & Pydantic Contributors | Include MIT copyright notice. | Permissive. |
| **Pillow** | 10.x | **HPND** (Historical Permission Notice and Disclaimer) | Alex Clark & Pillow Contributors | Include HPND license text and copyright notice. | Permissive. |
| **NumPy** | 1.24+ | **BSD-3-Clause** | NumPy Developers | Include BSD-3 copyright notice and disclaimer. | Permissive. |
| **pytesseract** | 0.3.10+ | **Apache-2.0** | Samuel Hoffstaetter | Include Apache-2.0 license notice. | Permissive. |
| **PyInstaller** | 6.22+ | **GPL-2.0 with Special Exception** | PyInstaller Development Team | The output executable created by PyInstaller is explicitly exempt from GPL copyleft. | Safe for bundling. The packaged binary does not inherit GPL. |
| **Python Standard Library** | 3.11–3.14 | **PSF License** | Python Software Foundation | Include PSF license text in documentation / NOTICE. | Permissive. |

### 2.2 System & Native Dependencies

| Component | Version | License | Upstream Author | Distribution Obligations | Bundling Implications |
|---|---|---|---|---|---|
| **Tesseract OCR** | 5.4.0+ | **Apache-2.0** | Ray Smith / Google LLC / Tesseract OCR | Include Apache-2.0 license and NOTICE file. | Permissive. May be bundled or distributed as external runtime. |
| **Leptonica** | 1.84.1+ | **BSD-2-Clause** | Dan Bloomberg | Include BSD-2 license text. | Permissive. |
| **tessdata (`eng`, etc.)** | Fast / Best | **Apache-2.0** | Google LLC / Tesseract Contributors | Include Apache-2.0 license. | Permissive trained-data model. |

### 2.3 Desktop (Electron & Renderer) Dependencies

| Component | Version | License | Upstream Author | Distribution Obligations | Bundling Implications |
|---|---|---|---|---|---|
| **Electron** | 45.3.2 | **MIT** | OpenJS Foundation / Electron Authors | Include Electron MIT copyright notice. | Permissive. Standard desktop runtime. |
| **Chromium** | 134.x (embedded) | **BSD-3 / Various** | Google LLC & Chromium Contributors | Include `LICENSES.chromium.html` in distribution root. | Permissive (Forge automatically generates `LICENSES.chromium.html`). |
| **Node.js** | 24.x (embedded) | **MIT / Various** | OpenJS Foundation | Include Node.js license notice. | Permissive. |
| **pdfjs-dist** | 6.5.438 | **Apache-2.0** | Mozilla Foundation | Include Apache-2.0 license text and NOTICE. | Permissive. High security version (GHSA-hq66-cqwq-w95j audited). |
| **React & React-DOM** | 19.2.0 | **MIT** | Meta Platforms, Inc. | Include MIT copyright notice. | Permissive. |
| **Vite** | 8.0.0 | **MIT** | Evan You & Vite Contributors | Build-time dev dependency. | Permissive. |
| **Electron Forge** | 8.0.1 | **MIT** | Electron Forge Contributors | Build-time dev dependency. | Permissive. |
| **TypeScript** | 5.9.3 | **Apache-2.0** | Microsoft Corporation | Build-time dev dependency. | Permissive. |

---

## 3. PDF Backend Strategy: Three Evaluated Options

The project owner must formally select one of the following strategic paths prior to public distribution:

### Option A: Commercial PyMuPDF / MuPDF License
- **Mechanics:** Enter into a commercial OEM distribution agreement with Artifex Software, Inc. for PyMuPDF and the underlying MuPDF library.
- **Advantages:**
  - 100% preservation of all existing extraction code, word-level coordinates, confidence scores, and golden baselines.
  - Zero code changes required in `src/docuready/ingest/`.
  - Full right to distribute proprietary closed-source binaries without AGPL copyleft obligations.
- **Disadvantages:**
  - Requires commercial licensing fees / royalties paid to Artifex Software.
- **Recommendation:** Necessary if DocuReady is to be distributed as a proprietary, closed-source commercial product without sharing the front-end or proprietary integrations.

### Option B: AGPL-3.0 Compliant Distribution
- **Mechanics:** License the entire DocuReady application (including the Electron desktop wrapper, sidecar protocol, and any proprietary frontend extensions) under the GNU Affero General Public License v3.0 (AGPL-3.0).
- **Advantages:**
  - Zero license acquisition fees.
  - Complete compliance with PyMuPDF's upstream open-source license.
  - Preserves 100% of existing extraction behavior, provenance coordinates, and golden tests.
  - Aligns with civic-tech / digital public infrastructure mission.
- **Disadvantages:**
  - Any entity modifying or distributing DocuReady must make their full source code available under AGPL-3.0.
  - Cannot include proprietary closed-source plugins or locked enterprise modules in the same distributed binary.
- **Recommendation:** Ideal if DocuReady is distributed as pure open-source or civic-tech software.

### Option C: PDFium-Based Parity Migration (Permissive Apache-2.0 / BSD)
- **Mechanics:** Complete the `pypdfium2` backend implementation by engineering a robust word-level extraction and reading-order clustering layer that achieves identical output to PyMuPDF.
- **Advantages:**
  - Permissive licensing throughout (Apache-2.0 / BSD).
  - Can be distributed under any license (open source, proprietary, commercial) without royalty payments.
- **Disadvantages:**
  - Requires significant algorithmic engineering (see Section 4).
  - High risk of coordinate drift, invalidating existing golden test snapshots if not 100% pixel-parity compliant.
- **Current Status:** **BLOCKED** from production adoption in Loop 3 due to missing word bounding box extraction.

---

## 4. Technical Blocker Report: PDFium Backend Parity

The existing codebase contains a pluggable PDF backend abstraction (`docuready.ingest.pdf_backend`), with `PyMuPDFDocumentBackend` as the default and a prototype `PdfiumDocumentBackend` in `src/docuready/ingest/pdf_backend/pdfium_backend.py`.

A rigorous technical inspection reveals four hard blockers preventing immediate cutover to PDFium:

### Blocker 1: Missing Word-Level Coordinate Extraction (`get_words()`)
- **PyMuPDF Contract:** `page.get_text("words")` yields 8-tuples: `(x0, y0, x1, y1, word_str, block_no, line_no, word_no)`.
- **PDFium Reality:** `pypdfium2` exposes character-level bounding boxes (`textpage.get_charbox(i)`), but has no native word, line, or block clustering. `PdfiumPageBackend.get_words()` explicitly raises `NotImplementedError`.
- **Provenance Hazard:** Returning synthetic, zero, or page-wide bounding boxes is strictly forbidden because it corrupts the evidence coordinate contract.

### Blocker 2: Inverted Coordinate System
- **PyMuPDF:** Uses top-left origin $(0, 0)$ with coordinates in PDF points ($1/72$ inch), $y$ increasing downwards.
- **PDFium:** Uses standard PDF coordinate space with bottom-left origin $(0, 0)$, $y$ increasing upwards.
- **Parity Requirement:** Character boxes extracted via PDFium must be mathematically inverted:
  $$y_{top} = \text{page\_height} - y_{pdf\_top}$$
  $$y_{bottom} = \text{page\_height} - y_{pdf\_bottom}$$

### Blocker 3: Reading Order & Complex Typography
- Text extraction in multi-column, certificate, or tabular PDFs (common in Indian state certificates and marksheets) depends on MuPDF's spatial line and paragraph segmentation.
- PDFium text streams follow the raw content stream order, which in many generated government PDFs is out of visual reading order. Without a 2D spatial clustering algorithm, regular expression anchors (e.g. `r"ANNUAL INCOME[:\s]+(\d+)"`) fail to match adjacent text.

### Blocker 4: Extractor Module Coupling
- `src/docuready/ingest/extractor.py` directly references `pymupdf.Document` and `pymupdf.Page` type annotations and accesses `backend_doc.raw_doc`.
- `_find_field_in_page_vector` expects `page.search_for()` to return objects with `.x0, .y0, .x1, .y1` attributes, whereas `pypdfium2` returns raw tuples or rect lists.

### PDFium Parity Migration Plan (Required for Future Loop)
1. Implement a spatial character clustering algorithm in `pdfium_backend.py` that groups character boxes into words, lines, and blocks.
2. Invert PDFium coordinates to match the top-left point contract.
3. Build a comparative parity test suite running both backends across the synthetic packet corpus (`pkt_01` through `pkt_08`).
4. Assert $100\%$ match on extracted strings, line counts, and bounding-box overlap (Intersection-over-Union $\ge 0.98$).
5. Only switch default backend when golden baseline tests pass with zero checksum drift.

---

## 5. Required Decision from Project Owner

| Decision Point | Owner Action Required | Release Gate Impact |
|---|---|---|
| **Distribution License Model** | Select **Option A (Commercial PyMuPDF)** or **Option B (AGPL-3.0)** | **Gated:** Proprietary distribution cannot proceed without a commercial license. AGPL distribution requires publishing full project source. |
| **Backend Parity Investment** | Decide whether to commission **Option C (PDFium Parity)** for Loop 4+ | Determines whether engineering resources are allocated to eliminate the PyMuPDF dependency. |
| **Attribution & Third-Party Notices** | Approve the inclusion of `docs/THIRD_PARTY_NOTICES.md` in all packaged installer bundles | Mandatory compliance action prior to release. |

---

## 6. Distribution Checklist

- [x] Full dependency license audit completed.
- [x] PyMuPDF AGPL dual-licensing implications documented.
- [x] PDFium technical blockers and parity roadmap detailed.
- [x] Transitive dependencies (Leptonica, Tesseract, Electron, Chromium) audited.
- [ ] Project owner formal sign-off on Option A, B, or C.
- [ ] Third-party attribution file packaged into final installers.
