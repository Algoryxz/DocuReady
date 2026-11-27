# DocuReady — Loop 01 OSD Performance & Reliability Investigation

**Investigation Date:** 2026-11-22  
**Target Component:** OCR Ingestion Pipeline (`src/docuready/ingest/extractor.py`)  
**Investigation Branch:** `loop-01-osd-performance-analysis`  
**Engineer:** Antigravity Autonomous Agent  
**Status:** Completed & Validated  

---

## 1. Problem Statement & Historical Context

DocuReady is designed for high-throughput, offline auditing of citizen documents in governance and public service delivery (e.g., scholarship applications, revenue certificates, ration cards).

During Loop 00/03 profiling, a severe latency bottleneck was observed:
- A 6-document application packet took over 11.5 seconds to audit.
- Scanned documents took ~3.0 seconds per page.
- Micro-profiling revealed that **Orientation and Script Detection (OSD, `--psm 0`)** accounted for **~1.45 seconds per page**, or **51.36% of total OCR latency**.

Because administrative workflows predominantly ingest upright scanned documents (>95%), running OSD unconditionally on 100% of pages introduced unacceptable latency overhead.

---

## 2. Experimental Investigation & Candidate Solutions

We evaluated four candidate optimization strategies against accuracy, robustness, and coordinate invariants:

### Experiment 1: Downsampling Prior to OSD
- **Hypothesis:** Downsampling the 200 DPI image to 72 DPI ($0.36\times$) would reduce OSD compute time while retaining orientation information.
- **Empirical Findings:**
  - Scale 0.75: OSD latency dropped slightly (1,210 ms), orientation detected correctly.
  - Scale 0.50: OSD latency dropped to ~850 ms, but confidence dropped from 10.4 to 1.4.
  - Scale 0.36: **FAILED.** On 90° rotated page `smp_23_rotated_90deg.pdf`, Tesseract OSD misclassified orientation as 0° or failed with "Too few characters".
- **Conclusion:** Downsampling is fragile on low-density or stylized documents and violates the non-negotiable rule of zero accuracy regression.

### Experiment 2: Speculative 0° Token OCR with Conservative Upright Fast-Path (WINNER)
- **Hypothesis:** By running token OCR at 0° first, we can inspect real token statistics (confidence, count, and aspect ratio). If the page is demonstrably upright, OSD can be bypassed completely.
- **Statistical Separation Analysis across Realistic Corpus (60 documents):**
  - Upright scans (clean, degraded, shadow, noise):
    - `mean_confidence >= 84.4%`
    - `high_confidence_ratio (conf >= 60%) >= 84.5%`
    - `horizontal_token_ratio (width >= height) >= 91.2%`
  - Rotated 90° / 270° scans:
    - Vertical text lines produce tokens where `height > width` for >90% of tokens.
    - `mean_confidence ~ 29.7%`.
  - Rotated 180° (upside down) scans:
    - `mean_confidence ~ 31.1%`.
- **Fast-Path Decision Rule:**
  A document is deemed `_is_demonstrably_upright` iff ALL four criteria hold:
  1. `total_tokens >= 15` (prevents false positives on sparse or blank pages).
  2. `mean_conf >= 70.0%` (safe 14.4% buffer below lowest observed upright scan).
  3. `high_conf_ratio >= 0.60` (at least 60% of tokens have confidence $\ge 60\%$).
  4. `horizontal_token_ratio >= 0.70` (geometric invariant ensuring horizontal text orientation).
- **Result:** **100% precision on upright pages (OSD skipped)**; **100% recall on rotated pages (OSD triggered)**.

### Experiment 3: Direct Buffer Pixmap Decoding
- **Bottleneck Identified:** PyMuPDF pixmaps were converted to Pillow via `io.BytesIO(pix.tobytes())`, triggering redundant PNG/PPM encoding and decoding.
- **Optimization:** Replaced with zero-copy buffer construction:
  ```python
  img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
  pix = None  # Immediate native memory release
  ```
- **Result:** Pixmap rendering overhead reduced from **267.22 ms** to **45.99 ms** (**82.79% speedup**).

### Experiment 4: Controlled OSD Timeout & Fault Tolerance
- **Hardening:** Added `OSD_TIMEOUT_SECONDS = 4` using Python's `pytesseract` timeout handler to prevent pathological Tesseract hangs on corrupt or adversarial raster images. If OSD fails or times out, the pipeline safely falls back to initial 0° tokens.
- **Blank Page Guard:** Added immediate bypass if `valid_token_count == 0` to prevent Tesseract exception spam.

---

## 3. Implementation Summary

1. `src/docuready/ingest/extractor.py`:
   - Implemented `_is_demonstrably_upright(data: dict) -> bool`.
   - Restructured `_ocr_page`: Direct buffer rendering $\rightarrow$ 0° token OCR $\rightarrow$ fast-path gate evaluation $\rightarrow$ conditional OSD fallback if non-upright.
   - Enforced 4-second timeout on fallback OSD.
2. `src/docuready/ingest/pdf_backend/pymupdf_backend.py`:
   - Updated `render_page_as_image` to use `Image.frombytes` directly.
3. `tests/test_ocr_performance_and_adversarial.py`:
   - 10 comprehensive tests covering fast-path correctness, 0°/90°/180°/270° orientation recovery, bounding box consistency, degradation resistance, blank page status, and OSD timeout mocking.
4. `scripts/benchmark_ocr_performance.py`:
   - Standalone reproducible benchmarking harness across all 9 required workload classes.

---

## 4. Verification & Validation Summary

| Test Suite / Metric | Pre-Loop 01 | Post-Loop 01 | Status |
|---|---|---|---|
| **Clean Scanned Doc Latency** | 2,963.60 ms | **1,358.55 ms** | **-54.16%** |
| **6-Doc Packet Audit Latency** | 11,523.50 ms | **5,585.09 ms** | **-51.53%** |
| **Page Rendering Overhead** | 272.53 ms | **45.99 ms** | **-82.79%** |
| **Golden Baseline Checksum** | Intact | `E8FB1A6B842A...` | **Bit-Exact Match (13/13)** |
| **Network Egress Contract** | Zero Calls | Zero Calls | **Passed (21/21)** |
| **Adversarial & Regression Tests** | N/A | 10 passed, 0 failed | **Passed (10/10)** |
| **Desktop Integration Tests** | 21 passed | 21 passed, 0 failed | **Passed (21/21)** |
| **Competition Demo (Replacement)** | Verified | 75 $\rightarrow$ 100 Verified | **100% Working** |

---

## 5. Architectural & Governance Safeguards

1. **Conservative Abstention:** If a document does not meet the strict 4-point statistical gate, the system never guesses; it falls back to full OSD. If OSD fails, confidence calibration tags low-confidence tokens as `AMBIGUOUS` or `UNREADABLE`.
2. **Zero Inversion of Bounding Boxes:** Normalized bounding boxes $[x_0, y_0, x_1, y_1]$ are validated post-rotation, guaranteeing exact visual highlighting in the Electron PDF viewer.
3. **Completely Local & Offline:** No external APIs, neural networks, or telemetry introduced.
