# DocuReady — Loop 02: Orientation Gate Assurance, Recovery Optimization & OCR Accuracy

**Document Version:** 1.0.0  
**Loop:** Loop 02 — Orientation Gate Assurance, Recovery Optimization & OCR Accuracy  
**Date:** 2026-11-22  
**Branch:** `loop-02-orientation-gate-assurance`  
**Engineer:** Antigravity Autonomous Agent  
**Status:** Completed, Fully Verified & Production Qualified  

---

## 1. Executive Summary

Loop 02 was chartered to audit the reliability of Loop 01's speculative OCR fast path, assess whether rotated or unreadable documents could falsely pass the gate, optimize the slower orientation recovery path, and resolve any resource retention defects.

### Major Outcomes:
1. **0.00% Rotated False-Upright Rate:** Across 70 diverse document fixtures (60 realistic administrative scans + 10 dedicated adversarial attack fixtures), zero rotated, skewed, or inverted documents bypassed the gate.
2. **Two-Tier OSD Recovery Optimization:** Introduced a scaled (0.60x) first-tier OSD pass that drops rotated document processing time from **4,690.22 ms** to **3,296.25 ms** (**29.7% speedup**) while retaining full-resolution fallback resilience.
3. **98.8% Elimination of Document Extraction Memory Leak:** Identified and eliminated an unmanaged MuPDF pixmap cache retention leak (`fz_store`). Process RSS growth over 10 repeated extractions plummeted from **113.68 MB to 0.98 MB**, reducing peak process footprint from **378.55 MB to 119.07 MB**.
4. **Hardened Upright Gate Invariants:** Integrated alphanumeric token validation and a 40-character minimum text floor, preventing punctuation noise specks or isolated symbols from spoofing the fast-path gate.
5. **Zero Accuracy or Golden Baseline Regressions:** All 66 Python tests, 21 Electron desktop tests, golden baseline byte-for-byte checksums, and competition demo walkthroughs remain 100% green.

---

## 2. Initial State & Problem Statement

Loop 01 successfully accelerated upright document extraction by bypassing Tesseract OSD when a 4-point statistical invariant was satisfied. However, several critical engineering questions remained:
- Could an upside-down page with symmetrical letters (e.g. "now", "pod", "on", "no") produce high confidence and trick the upright gate?
- Could 10° or 15° skewed pages be misclassified as upright?
- Why did rotated documents take over 4.5 seconds in Loop 01?
- Why did peak process RSS climb to ~380 MB during batch benchmarks?
- Are bounding boxes on rotated documents geometrically valid in relation to page boundaries?

---

## 3. Root Cause Findings

### Finding 1: Recovery Path Latency Mechanism
Micro-profiling revealed that the increased runtime on rotated documents was the expected cumulative cost of speculative execution:
1. `direct_buffer_render`: 45.14 ms
2. `speculative_0_deg_ocr`: 951.59 ms (failed attempt on rotated page)
3. `gate_evaluation`: 0.07 ms
4. `osd_full_resolution`: 1,158.20 ms
5. `pil_rotation`: 21.00 ms
6. `upright_2nd_ocr_pass`: 910.66 ms
Total recovery latency: **~3,086 ms**.
Because the pipeline speculatively attempts 0° OCR before knowing if the document is rotated, rotated pages pay for both the failed 0° pass and the subsequent upright 2nd pass. Rendering and rotation overhead were negligible; the dominant cost was the sequential full-resolution OSD pass.

### Finding 2: Unmanaged PyMuPDF Pixmap Cache Leak
During repeated document extractions, process memory grew by ~11.3 MB per document, reaching 378+ MB in packet benchmarks.
- **Root Cause:** In `DocumentExtractor.extract_document`, `doc.close()` was never called on the PyMuPDF document handle. Furthermore, MuPDF's internal C-level store cache (`fz_store`) retained high-resolution 200 DPI pixmaps across document boundaries.
- **Remediation:** Added `doc.close()` and explicit `pymupdf.TOOLS.store_shrink(100)` in a `finally:` block. Memory growth over 10 repeated iterations dropped from **113.68 MB to 0.98 MB**.

### Finding 3: Vulnerability to Non-Alphanumeric Punctuation
The original gate counted any non-empty token with confidence $\ge 0$. While natural text scans performed well, synthetic adversarial pages containing repeated punctuation marks (e.g. hyphens, underscores, dots) could theoretically inflate token counts and horizontal ratios.
- **Remediation:** Enforced that valid tokens must contain at least one alphanumeric character (`any(ch.isalnum() for ch in word)`), and added a 40-character minimum text floor (`OSD_FAST_PATH_MIN_CHARS = 40`).

---

## 4. Gate Safety & Adversarial Attack Matrix

We constructed 10 targeted adversarial attack fixtures in `synthetic_data/attack_corpus/`:

| Fixture ID | Attack Vector / Characteristic | Ground Truth | Gate Decision | Classification |
|---|---|---:|---|---|
| `atk_01_skew_10deg.pdf` | 10° rotation (OCR text segmentation failure) | 10° | Rejected (11 tokens < 15) | **ROTATED_CORRECTLY_REJECTED** |
| `atk_02_skew_15deg.pdf` | 15° rotation (complete text segmentation failure) | 15° | Rejected (0 tokens < 15) | **ROTATED_CORRECTLY_REJECTED** |
| `atk_03_mixed_orientation.pdf` | Upright header (2 lines) + 90° rotated body | Mixed | Rejected (mean conf 31.7%) | **ROTATED_CORRECTLY_REJECTED** |
| `atk_04_sparse_receipt.pdf` | Sparse receipt with only 8 tokens | 0° | Rejected (8 tokens < 15) | **UPRIGHT_FALLBACK_TO_OSD** |
| `atk_05_blank_with_noise_dots.pdf` | Blank page with 60 random noise dots | 0° | Rejected (0 alnum tokens) | **UPRIGHT_FALLBACK_TO_OSD** |
| `atk_06_inverted_reversible_words.pdf` | 180° upside-down reversible Latin words | 180° | Rejected (mean conf 47.8%) | **ROTATED_CORRECTLY_REJECTED** |
| `atk_07_vertical_column_numbers.pdf` | Upright page with single-char vertical column | 0° | Rejected (horiz ratio 0.05) | **UPRIGHT_FALLBACK_TO_OSD** |
| `atk_08_landscape_table_90deg.pdf` | 90° rotated table with prominent horizontal lines | 90° | Rejected (mean conf 17.9%) | **ROTATED_CORRECTLY_REJECTED** |
| `atk_09_heavy_gaussian_blur.pdf` | Severe Gaussian blur ($\sigma=3.5$) | 0° | Rejected (mean conf 32.1%) | **UPRIGHT_FALLBACK_TO_OSD** |
| `atk_10_extreme_shadow_corner.pdf` | 85% opacity diagonal shadow gradient | 0° | Accepted (upright text intact) | **TRUE_UPRIGHT_FAST_PATH** |

### Aggregate Gate Safety Across All 70 Corpus Fixtures:
- **Total Fixtures Evaluated:** 70
- **Actual Upright Documents:** 62
  - Fast-Path Accepted: 57 (91.9%)
  - Safe Fallback to OSD / Abstention: 5 (8.1%)
- **Actual Rotated / Skewed / Adversarial Documents:** 8
  - Correctly Rejected: 8 (100.0%)
  - **Critical False-Upright Pass:** **0 (0.00%)**

---

## 5. Performance Improvements & Before/After Comparison

| Workload Category | Test Fixture | Baseline Median | Loop 01 Median | Loop 02 Median | Total Delta vs Baseline |
|---|---|---:|---:|---:|---:|
| **Clean Scanned PDF** | `smp_11_raster_scan.pdf` | 2,963.60 ms | 1,358.55 ms | **1,140.25 ms** | **-1,823.35 ms (-61.5%)** |
| **Rotated 90° Scan** | `smp_23_rotated_90deg.pdf` | 3,118.15 ms | 4,690.22 ms | **3,296.25 ms** | +178.10 ms (+5.7%) |
| **Rotated 180° Scan** | `smp_24_rotated_180deg.pdf` | 3,089.27 ms | 4,237.22 ms | **3,327.20 ms** | +237.93 ms (+7.7%) |
| **Rotated 270° Scan** | `smp_61_rotated_270deg.pdf` | 3,169.71 ms | 4,929.68 ms | **3,364.10 ms** | +194.39 ms (+6.1%) |
| **Low-DPI Scan** | `smp_25_low_dpi.pdf` | 3,062.46 ms | 1,487.79 ms | **1,113.06 ms** | **-1,949.40 ms (-63.7%)** |
| **Shadow Gradient** | `smp_37_shadow_gradient.pdf` | 2,650.34 ms | 1,301.33 ms | **1,035.38 ms** | **-1,614.96 ms (-60.9%)** |
| **Multi-page Native** | `smp_55_multipage_layout_1.pdf` | 30.51 ms | 26.50 ms | **26.76 ms** | -3.75 ms (-12.3%) |
| **6-Doc Packet Audit** | `pkt_loop3_demo` | 11,523.50 ms | 5,585.09 ms | **4,522.16 ms** | **-7,001.34 ms (-60.8%)** |
| **Peak Memory (RSS)** | Process Peak | 379.14 MB | 378.55 MB | **119.07 MB** | **-260.07 MB (-68.6%)** |

---

## 6. Code Modifications

1. `src/docuready/ingest/extractor.py`:
   - Updated `_is_demonstrably_upright` with `any(ch.isalnum() for ch in word)` and `total_chars >= OSD_FAST_PATH_MIN_CHARS`.
   - Updated `_ocr_page` with Two-Tier OSD recovery (Tier-A fast 0.60x scaled OSD with full-resolution fallback).
   - Wrapped `extract_document` in a `try ... finally:` block calling `doc.close()`, `backend_doc.close()`, and `pymupdf.TOOLS.store_shrink(100)`.
2. `tests/test_loop02_orientation_assurance.py`:
   - Permanent test suite containing 7 comprehensive tests for zero false-upright rate, sparse/noise rejection, alphanumeric spoofing prevention, two-tier recovery accuracy, coordinate bounds, and repeated-processing memory stability.
3. `scripts/build_attack_corpus.py`:
   - Generator for 10 targeted adversarial attack documents.
4. `scripts/evaluate_gate_safety.py`:
   - Evaluation harness scoring gate decisions, token metrics, bounding-box validity, and latency across 70 fixtures.

---

## 7. Verification & Sign-Off Checklist

- [x] **Gate Safety Evaluated:** Tested across 70 fixtures with 0.00% false-upright rate.
- [x] **Recovery Correctness Intact:** All 90°, 180°, and 270° documents recover 100% of target fields.
- [x] **OCR Accuracy Preserved:** Zero field extraction regressions.
- [x] **Coordinate Bounds Checked:** All bounding boxes strictly within $[0, 0, W_{\text{page}}+5, H_{\text{page}}+5]$.
- [x] **Memory Stability Verified:** Leak eliminated (growth < 1 MB over 10 runs).
- [x] **Golden Baseline Intact:** SHA-256 `E8FB1A6B842A47089937777133DE79E1E7F704BEE591D5B4471A1A90BC8C5FA9` bit-exact.
- [x] **Zero-Network Invariant:** 21/21 contract tests passed with zero socket egress.
- [x] **Desktop Electron Integration:** 21/21 tests passed.
- [x] **Competition Demo:** Validated clean packet (100) and replacement resolution ($75 \rightarrow 100$).

---

## 8. Known Limitations & Next Engineering Bottleneck

1. **Non-Orthogonal Skew (>15°):** Tesseract OSD only detects discrete 90° rotation increments ($0^\circ, 90^\circ, 180^\circ, 270^\circ$). Scans skewed at arbitrary angles between $10^\circ$ and $45^\circ$ are safely rejected by the upright gate and fall back to OSD, but OSD does not de-skew them. In Loop 03, we recommend evaluating Radon-transform or Hough-line based deskewing if non-orthogonal skew becomes a competition priority.
2. **Cold-Start Tesseract Subprocess Spawning:** Subprocess creation on Windows adds a ~25-30 ms process launch penalty per OCR pass. Exploring persistent daemonization or direct CFFI bindings could yield further millisecond-level improvements.
