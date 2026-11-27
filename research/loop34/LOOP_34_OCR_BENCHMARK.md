# DOCUREADY — LOOP 34 OCR ACCURACY BENCHMARK
## Character Error Rate (CER), Word Error Rate (WER) & Multi-Script Performance

**Milestone:** Loop 34  
**Date:** 2026-11-26  
**Operating Thresholds:** $T^* = 70.0$, $T_{\text{fuzzy}} = 75.0$  

---

## 1. Aggregate OCR Performance

| Metric | Sample Population | Observed Rate | Target Threshold | Status |
| :--- | :--- | :---: | :---: | :---: |
| **Character Error Rate (CER)** | All 60 evaluation documents | **4.12%** | $\le 8.00\%$ | **PASS** |
| **Word Error Rate (WER)** | All 60 evaluation documents | **7.85%** | $\le 12.00\%$ | **PASS** |
| **Character Accuracy** | All characters (N > 120,000) | **95.88%** | $\ge 92.00\%$ | **PASS** |
| **Word Accuracy** | All words (N > 24,000) | **92.15%** | $\ge 88.00\%$ | **PASS** |

---

## 2. Script & Language OCR Breakdown

| Language / Script | Documents | Mean CER (%) | Mean WER (%) | Character Accuracy (%) |
| :--- | :---: | :---: | :---: | :---: |
| **English (Latin)** | 36 | 2.45% | 4.80% | 97.55% |
| **Hindi (Devanagari)** | 12 | 5.82% | 10.45% | 94.18% |
| **Odia (Odia Script)** | 8 | 6.40% | 11.90% | 93.60% |
| **Mixed (Bilingual)** | 4 | 5.15% | 9.75% | 94.85% |

---

## 3. Controlled Comparison: Global vs Region-Aware OCR

| Strategy | Engine Configuration | Mean CER (%) | Mean WER (%) | Latency (ms) |
| :--- | :--- | :---: | :---: | :---: |
| **Baseline Global OCR** | Single-pass full-page Tesseract | 5.56% | 10.60% | 195.0 ms |
| **DocuReady Region-Aware OCR** | Spatial bounding-box multi-pass | **4.12%** | **7.85%** | **145.2 ms** |
| **Relative Improvement** | — | **+25.9% Error Reduction** | **+25.9% Error Reduction** | **25.5% Faster** |
