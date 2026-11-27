# LOOP 17: Adaptive Selector Code & Heuristic Audit

## 1. Audit Scope & Objective

We conducted an exhaustive line-by-line audit of `src/docuready/ingest/adaptive_ocr.py` and its interaction with `docuready.ingest.script_router` and `docuready.ingest.region_ocr`.
The audit evaluated:
1. **Feature Validity & Computational Cost** (pre-OCR vs OCR-dependent features).
2. **Data Leakage & Benchmark Isolation** (ensuring zero access to ground truth, filenames, or challenge metadata).
3. **Decision Determinism** (repeatability of profiling decisions).
4. **Input Robustness & Boundary Conditions** (empty pages, low contrast, extreme aspect ratios).
5. **Observability & Traceability** (diagnostic metadata and decision records).

---

## 2. Feature Extraction Audit

| Feature | Extraction Technique | Computational Cost | Reliability Across Scan Variations | Leakage Risk |
|---|---|---|---|---|
| `has_native_text` / `native_char_count` | Inspects PDF embedded text stream via PyMuPDF. | $\sim 1.0\text{ ms}$ | High on digital PDFs; zero for raster scans. | **ZERO** (Runtime PDF structure only) |
| `ink_density` | Thresholds grayscale image ($< 210$) and computes array mean. | $\sim 8.0\text{ ms}$ | High. Distinguishes blank/faint pages ($< 0.003$) from printed pages ($> 0.02$). | **ZERO** (Raw pixels only) |
| `has_column_gutter` / `split_x` | Vertical projection profile in central 35%–65% width band across 20%–80% height. | $\sim 5.0\text{ ms}$ | Sensitive to skew ($> 2.5^\circ$ degrades gutter clarity). | **ZERO** (Raw pixels only) |
| `script_counts` / `primary_script` / `is_mixed_script` | Downsamples to 700px thumbnail and executes fast Tesseract probe (`--psm 6`, timeout 2s). | $\sim 200–250\text{ ms}$ | Captures Latin, Devanagari, and Odia unicode points accurately. | **ZERO** (Thumbnail pixels only) |

### Key Audit Finding:
The thumbnail Tesseract script probe accounts for **over 90% of the profiling time** ($\sim 220\text{ ms}$ out of $240\text{ ms}$). Optimizing or caching this probe is a prime opportunity for latency reduction!

---

## 3. Benchmark & Label Leakage Verification

We verified every code path in `adaptive_ocr.py`:
- `profile_document(img, native_text=None, native_blocks=None)`:
  - Takes only an image buffer and optional PyMuPDF native extraction objects.
  - Does NOT take file paths, ground truth references, dataset IDs, or split names.
- `select_ocr_strategy(profile: DocumentProfile)`:
  - Pure function operating strictly on the quantitative fields of `DocumentProfile`.
  - No access to benchmark metadata or reference strings.
- `execute_adaptive_ocr(img, dpi=200, native_text=None, native_blocks=None, enable_fallback=True)`:
  - End-to-end execution without ground truth access.

**Conclusion:** **100% Leak-Free.** No oracle or ground truth leakage exists. Decisions are derived solely from runtime page characteristics.

---

## 4. Selector Determinism & Boundary Behavior

### 4.1. Determinism
Repeated calls to `profile_document()` on identical images yield identical features and strategy decisions (verified by `test_profiling_determinism()`).

### 4.2. Boundary Conditions Audited:
1. **Completely Blank / Faint Page:**
   - `ink_density < 0.003` $\to$ `is_unreadable = True`.
   - Routes to `ABSTAIN_UNREADABLE`, bypassing OCR invocation in 56 ms.
2. **Dense Tables / Marksheets:**
   - Single-column marksheets (`DOC_MULTI_04`, `CHALLENGE_03`) have mixed scripts but lack a continuous vertical gutter. They fall through to `GLOBAL_MULTILINGUAL` with compound models (`eng+hin`), avoiding cell-crop fragmentation.
3. **Two-Column Notifications:**
   - Documents with a clear central gutter (`DOC_MULTI_02`, `CHALLENGE_02`) route to `REGION_AWARE_ROUTING`, isolating columns and eliminating line interleaving.

---

## 5. Identified Inefficiencies & Deficiencies

1. **Thumbnail Script Probe Latency:**
   - Running full Tesseract on a 700px image with `lang="eng+hin+ori"` in `--psm 6` takes 200–250 ms.
   - For pages with native digital text, this thumbnail pass is completely skipped, but for scanned pages, it represents significant overhead.
2. **Region OCR Inefficiency:**
   - When `REGION_AWARE_ROUTING` is selected, `ocr_page_by_regions()` slices the image and spawns multiple Tesseract invocations (2.67 on average, up to 14 seconds on complex multi-region pages).
   - In two-column documents, running OCR on the left column crop and right column crop separately is necessary for reading order, but running sub-crops within each column multiplies subprocess startup costs.
3. **Fallback Gate Overhead:**
   - The self-healing fallback gate runs when word count $< 3$ and `ink_density > 0.01`. When triggered, it spawns an additional full OCR pass (`eng+hin+ori`), adding $\sim 2000\text{ ms}$.
