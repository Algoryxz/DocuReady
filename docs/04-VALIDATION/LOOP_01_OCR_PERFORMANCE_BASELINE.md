# DocuReady Loop 01 — OCR & OSD Performance Baseline Report
**Measurement Date:** 2026-11-22  
**Branch:** `loop-01-osd-performance-analysis`  
**Execution Environment:**
- **Operating System:** Microsoft Windows 11 Enterprise (AMD64)
- **CPU:** 12 Logical Cores
- **System Memory:** 15.73 GB RAM
- **Runtime:** Python 3.12.10 (64-bit)
- **Local OCR Engine:** Tesseract OCR v5.4.0.20240606 (`leptonica-1.84.1`)
- **PDF Engine:** PyMuPDF 2.1 (MuPDF core engine)
- **Imaging Toolkit:** Pillow 12.3.0
- **DPI Configuration:** Standard 200 DPI OCR extraction resolution

---

## 1. Executive Summary & Root Cause Reproduction

Granular micro-benchmarks and end-to-end extraction runs confirm the historical bottleneck:
- **Tesseract Orientation and Script Detection (OSD)** is executed on the full 200-DPI raster image on **every single page**, consuming **1,447.91 ms (51.36% of the per-page OCR runtime)**.
- **Token OCR (`image_to_data`)** consumes **1,097.97 ms (38.95%)**.
- **Pixmap Rendering** consumes **272.53 ms (9.67%)**.
- **Spatial clustering, line building, field extraction, and confidence calibration** combined consume only **0.81 ms (<0.03%)**.

On upright documents (which constitute >95% of real-world administrative packets), running OSD unconditionally imposes an unnecessary 1.45-second latency tax per page. On a 6-document applicant packet containing 4 scanned raster documents, **~5.8 seconds (over 50% of the 11.52-second audit latency)** is spent on redundant OSD passes.

---

## 2. Granular Per-Stage Baseline Micro-Benchmark

Measured on standard scanned A4 document (`smp_11_raster_scan.pdf`, 200 DPI, $1654 \times 2339$ pixels) across 5 repeated runs:

| Pipeline Stage | Implementation Detail | Median Latency (ms) | Mean Latency (ms) | Share of OCR Stage |
|---|---|---:|---:|---:|
| **1. Page Rendering** | PyMuPDF `page.get_pixmap(dpi=200)` + BytesIO decode | 272.53 ms | 261.04 ms | 9.67% |
| **2. Tesseract OSD** | `pytesseract.image_to_osd(img)` (Full 200 DPI) | 1,447.91 ms | 1,473.26 ms | **51.36%** |
| **3. Tesseract Token OCR** | `pytesseract.image_to_data(img)` (LSTM Engine) | 1,097.97 ms | 1,118.40 ms | 38.95% |
| **4. Spatial Y-Clustering** | `PageOCRData._build_lines` (12pt band clustering) | 0.72 ms | 0.70 ms | 0.02% |
| **5. Field Search & Calibration** | Proximity search + `ConfidenceCalibrator` | 0.09 ms | 0.28 ms | <0.01% |
| **Total Per-Page OCR** | Unoptimized pipeline | **2,819.22 ms** | **2,853.68 ms** | **100.00%** |

---

## 3. Workload Matrix Baseline Measurements

All workloads measured across 5 repeated iterations using `time.perf_counter()`. Peak memory (RSS) recorded via `psutil`.

| Workload Category | Test Fixture | Pages | Method | Median (ms) | Mean (ms) | Min (ms) | Max (ms) | Peak RSS | Status |
|---|---|---:|---|---:|---:|---:|---:|---:|---|
| **1. Native-text PDF** | `smp_01_income_cert_clean.pdf` | 1 | NATIVE_VECTOR | 38.19 ms | 39.84 ms | 36.42 ms | 46.12 ms | 129.19 MB | `VALID` |
| **2. Clean Scanned PDF** | `smp_11_raster_scan.pdf` | 1 | LOCAL_OCR | 2,963.60 ms | 2,987.41 ms | 2,912.15 ms | 3,110.82 ms | 186.37 MB | `VALID` |
| **3. Rotated Page (90°)** | `smp_23_rotated_90deg.pdf` | 1 | LOCAL_OCR | 3,118.15 ms | 3,142.06 ms | 3,088.10 ms | 3,220.45 ms | 243.18 MB | `VALID` |
| **4. Rotated Page (180°)** | `smp_24_rotated_180deg.pdf` | 1 | LOCAL_OCR | 3,089.27 ms | 3,112.54 ms | 3,045.22 ms | 3,195.80 ms | 299.55 MB | `VALID` |
| **5. Rotated Page (270°)** | `smp_61_rotated_270deg.pdf` | 1 | LOCAL_OCR | 3,169.71 ms | 3,188.90 ms | 3,120.40 ms | 3,265.12 ms | 355.73 MB | `VALID` |
| **6. Low-DPI Scan** | `smp_25_low_dpi.pdf` | 1 | LOCAL_OCR | 3,062.46 ms | 3,085.12 ms | 3,010.55 ms | 3,190.20 ms | 378.44 MB | `VALID` |
| **7. Shadow Gradient** | `smp_37_shadow_gradient.pdf` | 1 | LOCAL_OCR | 2,650.34 ms | 2,674.88 ms | 2,598.11 ms | 2,780.40 ms | 378.45 MB | `VALID` |
| **8. Multi-page Native** | `smp_55_multipage_layout_1.pdf` | 4 | NATIVE_VECTOR | 30.51 ms | 31.85 ms | 28.90 ms | 35.40 ms | 378.58 MB | `VALID` |
| **9. Mixed 6-Doc Packet** | `pkt_loop3_demo` (2 vector, 4 scan) | 6 | HYBRID | 11,523.50 ms | 11,580.12 ms | 11,350.20 ms | 11,890.45 ms | 379.14 MB | `NEEDS_CHECKS` |

---

## 4. Key Findings & Optimization Constraints

1. **Native Vector Path is Already Blazing Fast:** Native PDF text streams are extracted in **~38 ms** with 100% precision. Optimization efforts must focus exclusively on the OCR/raster path.
2. **OSD is the Dominant Bottleneck:** Consumes >51% of OCR runtime on every page.
3. **Downsampling Caution:** Empirical testing shows that downsampling beyond $0.5\times$ (such as $0.36\times$ / 72 DPI) causes Tesseract OSD to misclassify 90° rotated documents as 0°, breaking extraction accuracy.
4. **Upright Confidence Separation:** Token confidence on upright documents is **>84.4%** across all degraded and clean scans, whereas rotated documents yield **~30%**. This strong mathematical margin enables a safe, conservative upright fast path.
