# DOCUREADY — LOOP 16 DOCUMENT PROFILING SPECIFICATION
## Low-Cost Pre-OCR Feature Extraction, Spatial Geometry & Layout Classification

**Component:** Ingestion Profiler Subsystem  
**Module:** `src/docuready/ingest/document_profiler.py`  
**Loop:** 16  
**Date:** November 2026  
**Status:** SPECIFICATION & COMPUTATIONAL AUDIT  

---

## 1. Objective & Design Philosophy

The purpose of document profiling in Loop 16 is to extract decisive structural and linguistic characteristics of a document at **minimal computational cost**—before committing to an expensive OCR execution path.

**Core Principle:** *The profiler must never spend more computational resources inspecting a document than it saves by choosing the optimal OCR strategy.*

---

## 2. Profiling Feature Taxonomy

Features are strictly categorized by their availability before vs after OCR execution:

### 2.1 Pre-OCR Features (Cost: 0 ms to 30 ms)

| Feature Name | Type | Extraction Technique | Computational Cost | Decision Value |
| :--- | :--- | :--- | :--- | :--- |
| `has_native_text` | bool | PyMuPDF `page.get_text()` | **1–2 ms** | Distinguishes digital PDFs from scans |
| `native_char_count` | int | Length of extracted string | **< 0.1 ms** | Filters blank vs text-bearing pages |
| `native_script_counts` | dict | Unicode regex (`RE_LATIN`, `RE_DEV`, `RE_ORI`) | **0.5 ms** | Direct script distribution without OCR |
| `page_dimensions` | tuple | Image `(width, height)` | **0 ms** | Geometry & aspect ratio calculation |
| `aspect_ratio` | float | `width / height` | **0 ms** | Flags non-standard aspect ratios |
| `ink_density` | float | Downsampled array mean black pixels | **4–6 ms** | Detects blank pages or solid dark borders |
| `horizontal_variance` | float | Variance of row projection sums | **5–8 ms** | Differentiates line structure from noise |
| `has_column_gutter` | bool | Quiet whitespace zone in body band | **5–8 ms** | **Primary trigger for multi-column region routing** |
| `estimated_skew` | float | Horizontal projection peak sharpness | **10–15 ms** | Flags rotated/skewed documents |

### 2.2 Low-Cost Probing Features (Cost: 150 ms to 250 ms)
Used exclusively when a scanned document lacks native text and script distribution cannot be determined from metadata:
- **`thumbnail_script_probe`:** Scales page image to a 450px thumbnail and executes a fast single-line sampling pass with `eng+hin+ori` (`--psm 6`, timeout: 2.0s). Inspects Unicode codepoint ratios of the recognized sample.

### 2.3 Post-OCR Quality Signals (Available After OCR)
- `mean_confidence`: Average word confidence (0.0 to 100.0).
- `valid_word_count`: Number of non-whitespace tokens with confidence $\ge 0$.
- `anchor_completeness`: Presence of mandatory domain keywords (e.g. `CERTIFICATE`, `NAME`, `INCOME`, `DATE`).

---

## 3. Computational Cost Budget

```
+-----------------------------------------------------------------------------------------+
| DOCUMENT PROFILING LATENCY BUDGET (Per Page)                                            |
+-----------------------------------------------------------------------------------------+
| [1] Digital PDF Layer Check:                        1.5 ms  (Native fast path)          |
| [2] Grayscale Downsample (0.25x):                   4.8 ms                              |
| [3] Horizontal & Vertical Projection Profiles:      7.2 ms                              |
| [4] Column Gutter & Symmetry Analysis:              5.1 ms                              |
| [5] Thumbnail Script Probe (Only if no native text): 185.0 ms                           |
+-----------------------------------------------------------------------------------------+
| TOTAL PROFILER OVERHEAD (Worst Case Scanned):     ~203.6 ms                             |
| TOTAL PROFILER OVERHEAD (Native PDF):               ~2.1 ms                             |
+-----------------------------------------------------------------------------------------+
```

A 200 ms investment allows DocuReady to bypass an unnecessary 2500–7500 ms multi-region pipeline on single-column or monolingual pages, yielding a net latency reduction of over **2000 ms to 5000 ms per page**!
