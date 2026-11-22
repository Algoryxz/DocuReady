# DOCUREADY — LOOP 15 REPRODUCTION INSTRUCTIONS
## Step-by-Step Independent Protocol for Verifying Region-Aware OCR & Multilingual Benchmarks

**Engineering Loop:** 15  
**Target Branch:** `loop-15-region-aware-multilingual-ocr`  
**Base Qualified Commit:** `ba3e306` (Loop 14)  
**Date:** November 2026  

---

## 1. Prerequisites & Environment Setup

Verify Python 3.12 environment and ensure local Tesseract OCR is configured with `eng`, `hin`, and `ori` language packs:

```powershell
# 1. Inspect current branch and clean working tree
git status
git branch --show-current

# 2. Confirm Tesseract discovery and language models
python -c "from docuready.ingest.tesseract_discovery import get_ocr_runtime_info; print(get_ocr_runtime_info())"
```

Expected output:
```json
{
  "available": true,
  "languages": ["eng", "hin", "ori"],
  ...
}
```

---

## 2. Re-Building Corpus & Dataset Manifest

To reconstruct the standardized multilingual corpus and generate `dataset_manifest.json`:

```powershell
python research/loop15/corpus_builder.py
```

Expected output:
```
[OK] Built Loop 15 corpus (11 samples). Manifest written to research/loop15/dataset_manifest.json
```

---

## 3. Executing the 9-Configuration Benchmark Suite

To run the comprehensive benchmark comparing Configurations A through I across all corpus documents:

```powershell
python research/loop15/benchmark/run_region_benchmark.py
```

Expected outputs:
- Real-time logging of CER, WER, Reading Order Inversion Rate, and Latency for all 10 documents.
- Summary table verifying Mean CER drops from 37.58% (Loop 14 page routing) to 20.13% (Loop 15 region routing).
- Output JSON: `research/loop15/results/loop15_benchmark_results.json`.

---

## 4. Running Performance & Profiling Suite

To measure stage-by-stage latency, peak memory allocation, and throughput:

```powershell
python research/loop15/benchmark/perf_profiler_region.py
```

Expected output:
- Profiling metrics logged per document.
- Summary confirming peak memory < 3.0 MB and average segmentation latency < 50 ms.
- Output JSON: `research/loop15/results/loop15_profiling_results.json`.

---

## 5. Running the Complete Regression Test Suite

Verify all unit tests, cross-loop tests, golden baselines, and Electron desktop tests:

```powershell
# 1. Loop 15 Dedicated Unit Tests
pytest tests/test_loop15_region_aware_ocr.py -v

# 2. Golden Baseline Verification (22/22 bit-exact parity)
pytest tests/test_golden_baseline.py tests/test_pack_golden_baseline.py -v

# 3. Cross-Loop Regression Suite (Loops 02 through 15)
pytest tests/ -v

# 4. Electron Desktop Verification (25/25 passed)
npm test --prefix apps/desktop
```

---

## 6. Verifying Frozen Loop 10 Production Binaries

Confirm that packaged competition binaries remain bit-exact and untouched:

```powershell
Get-FileHash apps/desktop/out/DocuReady-win32-x64/DocuReady.exe, apps/desktop/out/DocuReady-win32-x64/resources/app.asar, apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar/docuready_sidecar.exe | Format-Table -AutoSize
```

Expected SHA-256 Hashes:
- `DocuReady.exe`: `86339BA01C1E0E73B1A8E3CF799880C957F24E3691B0B4EE0717A861FCC5DCD2`
- `app.asar`: `D72882945989E468C76CE43840C16457AA94E59584DC6F953689A28A0014F27E`
- `docuready_sidecar.exe`: `5CF296943A640F41784B27786B59EE679C59DAA6BDA59CA2ACBEAE7621770B4C`
