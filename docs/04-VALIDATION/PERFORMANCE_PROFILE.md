# DocuReady Loop 3 — Performance Profile & Latency Breakdown

## 1. System Execution Environment

- **Operating System**: Microsoft Windows 11 Enterprise (x86_64)
- **Runtime Environment**: Python 3.12.10 (MSC v.1942 64 bit)
- **Local OCR Engine**: Tesseract OCR v5.4.0.20240606 (`leptonica-1.84.1`)
- **PDF Vector Engine**: PyMuPDF v1.25.1 (MuPDF core engine)
- **Image Processing Toolkit**: Pillow 11.1.0, OpenCV 4.11.0.86
- **Test Workload**: Mixed 6-document applicant packet (`pkt_loop3_demo`: 2 vector PDFs, 4 degraded raster scans).

---

## 2. Granular Per-Stage Micro-Benchmark

The pipeline was profiled using `src/profile_pipeline.py`. Each stage was isolated and measured across 10 repeated iterations using `time.perf_counter()` with sub-millisecond precision.

```
========================================================================================
Stage                              Operation                           Latency (ms)   Share
========================================================================================
1. Native Vector Path              PyMuPDF stream extraction               4.23 ms    0.04%
                                   Field Syntax & Calibrator Scoring       0.16 ms   <0.01%
                                   Total Native Vector Page                4.39 ms    0.04%
----------------------------------------------------------------------------------------
2. Local OCR Raster Path           PyMuPDF 200 DPI Page Render           209.17 ms    2.16%
                                   Tesseract OSD (Full 200 DPI)         1457.32 ms   15.05%
                                   Tesseract Token OCR (LSTM Engine)     994.53 ms   10.27%
                                   Spatial Y-Clustering (12pt bands)       0.32 ms   <0.01%
                                   Proximity & Candidate Search            0.45 ms   <0.01%
                                   Multi-Feature Calibrator                0.03 ms   <0.01%
                                   Total OCR Page (Unoptimized)         2661.82 ms   27.48%
                                   Total OCR Page (Downsampled OSD)     2471.06 ms   25.51%
----------------------------------------------------------------------------------------
3. Audit Engine & Safety Layer     Cross-Document Normalization            1.12 ms    0.01%
                                   Statutory Rules Engine                  0.84 ms    0.01%
                                   Decision Safety Firewall                0.41 ms   <0.01%
========================================================================================
4. Full Packet Audit (6 Docs)      End-to-End Latency                   9684.76 ms  100.00%
========================================================================================
```

---

## 3. Bottleneck Analysis

### A. The Optical Rasterization Cliff
- A native vector page takes **4.39 milliseconds**.
- An optically rasterized page takes **2,661.82 milliseconds** (~600× slower).
- **Finding**: 99.9% of wall-clock processing time is consumed by raster rendering and Tesseract inference. Python code execution (regex, string manipulation, clustering, calibrator, safety firewall) accounts for less than **3 milliseconds** combined ($0.03\%$ of pipeline time).

### B. The Tesseract OSD Penalty
- `pytesseract.image_to_osd()` performs a separate complete forward pass using Tesseract's legacy orientation and script detection model.
- On a 200 DPI scan ($1650 \times 2330$ pixels), OSD consumes **1,457.32 ms**—more than the actual character recognition pass (**994.53 ms**).
- **Optimization Implemented**: Downsampling the rendered image to a $825 \times 1165$ thumbnail for OSD reduces OSD time to **1,266.57 ms** without degrading rotation detection accuracy.
- **Future Production Recommendation**: Restrict OSD invocation exclusively to pages where PyMuPDF detects image rotation metadata or where an initial fast OCR pass yields low token density.

### C. Zero Overhead of Confidence Calibration
- The multi-feature calibration engine (`ConfidenceCalibrator`) executes in **0.03 ms** per field.
- The Spatial Y-Clustering algorithm (`PageOCRData._build_lines`) runs in **0.32 ms** for ~120 words.
- **Conclusion**: Calibrating confidence, computing candidate multiplicity, and evaluating the 8 decision safety firewall principles adds virtually zero overhead to the system.

---

## 4. End-to-End Packet Latency

For an applicant packet consisting of:
1. `application_form.pdf` (Native Vector): ~4 ms
2. `income_cert.pdf` (Native Vector): ~4 ms
3. `caste_cert.pdf` (Scanned Raster): ~2.4 s
4. `residence_cert.pdf` (Scanned Raster with Shadow): ~2.5 s
5. `marksheet.pdf` (Scanned Raster with Perspective Distortion): ~2.3 s
6. `bank_passbook.pdf` (Scanned Raster Low-Res): ~2.4 s

Total wall-clock audit time: **9.68 seconds**.
This satisfies all interactive submission requirements for student and welfare portals (sub-15 second target).
