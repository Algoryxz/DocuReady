# Reproducing Loop 17 Benchmark & Experimental Results

This document provides exact, step-by-step instructions to independently reproduce the Loop 17 corpus generation, 200-evaluation strategy matrix benchmark, and verification test suites on Windows x64.

---

## 1. Prerequisites & Environment Setup

Ensure the following tools and libraries are installed on the target machine:

1. **Python 3.12+**
2. **Tesseract OCR 5.x** installed at `C:\Program Files\Tesseract-OCR\tesseract.exe` with traineddata:
   - `eng.traineddata`
   - `hin.traineddata`
   - `ori.traineddata`
3. **Required Python Packages:**
   ```powershell
   pip install pymupdf numpy pillow pytesseract pytest
   ```

---

## 2. Step 1: Build the 20-Document Evaluation Corpus

To build the 20-document evaluation corpus (14 primary validation + 6 sealed challenge):

```powershell
python research/loop17/corpus_builder.py
```

**Expected Output:**
- 20 document files placed in `research/loop17/corpus/`
- 20 ground truth text files placed in `research/loop17/ground_truth/`
- 8 structured critical field contracts placed in `research/loop17/critical_fields/`
- Dataset manifest generated at `research/loop17/dataset_manifest.json`

---

## 3. Step 2: Run the 200-Evaluation Strategy Matrix Benchmark

To execute all 200 benchmark evaluations across the 10 strategies:

```powershell
python research/loop17/benchmark/run_strategy_benchmark.py
```

**Expected Artifacts Generated:**
- `research/loop17/results/loop17_strategy_benchmark_results.json`
- `research/loop17/strategy_results.json`
- `research/loop17/critical_field_results.json`
- `research/loop17/failure_records.json`

---

## 4. Step 3: Run the Automated Test Suites

Execute the unit and integration tests covering the Loop 17 Optimized Adaptive Selector:

```powershell
pytest tests/test_loop17_adaptive_efficiency.py -v
```

Execute the full regression suite across all prior loops:

```powershell
pytest tests/test_golden_baseline.py tests/test_pack_golden_baseline.py -v
pytest tests/test_loop14_multilingual_ocr.py tests/test_loop15_region_aware_ocr.py tests/test_loop16_adaptive_ocr.py tests/test_loop17_adaptive_efficiency.py -v
npm test --prefix apps/desktop
```

All tests should pass cleanly without regressions.

---

## 5. Step 4: Verify Baselines & Frozen Releases

Confirm that Loop 10 production release binaries remain bit-exact and untouched:

```powershell
Get-FileHash apps/desktop/out/DocuReady-win32-x64/DocuReady.exe -Algorithm SHA256
Get-FileHash apps/desktop/out/DocuReady-win32-x64/resources/app.asar -Algorithm SHA256
Get-FileHash apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar/docuready_sidecar.exe -Algorithm SHA256
```

Expected Hashes:
- `DocuReady.exe`: `86339BA01C1E0E73B1A8E3CF799880C957F24E3691B0B4EE0717A861FCC5DCD2`
- `app.asar`: `D72882945989E468C76CE43840C16457AA94E59584DC6F953689A28A0014F27E`
- `docuready_sidecar.exe`: `5CF296943A640F41784B27786B59EE679C59DAA6BDA59CA2ACBEAE7621770B4C`
