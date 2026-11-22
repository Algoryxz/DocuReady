# DOCUREADY — LOOP 11 PRIORITIZED OPTIMIZATION BACKLOG
## Post-Competition Engineering Roadmap & Architectural Enhancements

**Project:** DocuReady  
**Phase:** Phase 9 & 12 — Optimization Backlog & Prioritization  
**Status:** **FUTURE ROADMAP — RELEASE REMAINS SEALED FOR COMPETITION**  
**Date:** 2026-11-22  

---

## 1. BACKLOG GOVERNANCE & GATING PRINCIPLES

All proposed enhancements in this backlog are strictly derived from reproducible empirical evidence collected during Loop 11's independent benchmark.

**Acceptance Gate:** No item in this backlog may be merged into production without:
1. Zero regressions in the 714-test Pytest suite.
2. 100% bit-exact parity across the 22 golden baseline tests.
3. Measurable improvement on the corresponding independent benchmark suite (FUNSD, SROIE, Indic OCR, or DIBCO).

---

## 2. PRIORITIZED BACKLOG MATRIX

| Priority | Item ID | Title | Subsystem | Evidence Grounding | Target Metric |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **P0** | **OPT-01** | Noise-Induced Character Corruption Filter | Ingest / Safety | 6 noise samples generated corrupted numeric tokens with medium confidence | Reduce false-clearance risk on noisy documents to 0.0% |
| **P1** | **OPT-02** | Script-Zoned Multilingual OCR (`hin` & `ori`) | Ingest / OCR | 40/40 Indic benchmark samples suffered complete Devanagari/Odia deletion | Achieve $> 85\%$ character recognition on Hindi & Odia sections |
| **P1** | **OPT-03** | 2D Spatial Column-Aware Line Grouping | Ingest / Layout | 50 FUNSD form samples suffered reading-order line mergers (CER 55.9%) | Reduce FUNSD Form CER from 0.5589 to $< 0.1500$ |
| **P2** | **OPT-04** | Adaptive Bilateral Preprocessing Filter | Ingest / Preprocess | Speckle noise $\sigma \ge 25$ degrades OCR token confidence | Recover readable text on noisy scans without blurring stroke edges |
| **P2** | **OPT-05** | Extended Hough Angle Accumulation ($15^\circ–30^\circ$) | Ingest / Deskew | 10 samples with skews $> 15^\circ$ failed angle estimation | Recover text on severe skews up to $30^\circ$ |
| **P3** | **OPT-06** | Multi-Page Concurrent ThreadPool Rasterization | Pipeline / Perf | OCR accounts for 73.0% of runtime; multi-page PDFs process serially | Reduce 4-page bundle latency from 3.0s to $< 1.4s$ |
| **P3** | **OPT-07** | Shared Binarization Buffer for Skew Estimation | Ingest / Perf | Skew estimation consumes 98.12 ms (13.1% of runtime) | Cut skew estimation latency by ~40% (down to $\approx 55$ ms) |
| **P4** | **OPT-08** | Degraded Scan Quality Real-Time Warning Badge | Desktop UX | Operator lacks real-time signal when input scan quality is marginal | Provide immediate visual advisory before audit dispatch |

---

## 3. DETAILED SPECIFICATION FOR KEY INITIATIVES

### OPT-01: Noise-Induced Character Corruption Filter (P0)
- **Problem:** Tesseract produces alphanumeric hallucinations when presented with salt-and-pepper noise at $\sigma \ge 35$. If these tokens have confidence $> 45\%$, they bypass the upright gate.
- **Remediation Specification:**
  - Introduce an entropy-based stroke-to-noise ratio check in `_is_demonstrably_upright`.
  - If token dictionary valid-word ratio drops below 30% while token count $> 10$, mark the page as `UNREADABLE_DEGRADED` and trigger conservative abstention (`NEEDS_CHECKS`, `bbox: None`).
- **Validation Test:** Synthetic noise suite with paired clean controls.

### OPT-02: Script-Zoned Multilingual OCR (P1)
- **Problem:** Invoking Tesseract with `lang="hin"` across English headers causes false Devanagari transliteration. Invoking with `lang="eng"` deletes all Hindi/Odia text.
- **Remediation Specification:**
  - Implement a fast script identification (SID) pre-pass using PyMuPDF font metadata or connected-component script classification.
  - Slice bounding regions into Latin zones (`lang="eng"`) and Indic zones (`lang="hin"` or `lang="ori"`).
  - Merge the resulting OCR data dictionaries into a single coordinate-aligned `PageOCRData`.
- **Validation Test:** Indic Multilingual Suite (40 samples).

### OPT-03: 2D Spatial Column-Aware Line Grouping (P1)
- **Problem:** `PageOCRData._build_lines` uses pure vertical distance clustering, merging Column 1 questions and Column 2 answers into interleaved lines.
- **Remediation Specification:**
  - Implement recursive XY-Cut or Voronoi tessellation to identify column gutters before vertical grouping.
  - Restrict line aggregation to within column boundaries.
- **Validation Test:** FUNSD Suite (50 samples).
