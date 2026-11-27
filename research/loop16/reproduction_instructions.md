# Reproducing Loop 16 Benchmark & Experimental Results

This document provides exact, step-by-step instructions to independently reproduce the Loop 16 corpus generation, strategy matrix benchmark, and verification test suite on Windows x64.

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

## 2. Step 1: Re-Generate the 15-Document Corpus

To build the 15-document evaluation corpus (11 primary validation + 4 sealed challenge):

```powershell
python research/loop16/corpus_builder.py
```

**Expected Output:**
- 15 document files placed in `research/loop16/corpus/`
- 15 ground truth text files placed in `research/loop16/ground_truth/`
- Dataset manifest generated at `research/loop16/dataset_manifest.json`

---

## 3. Step 2: Run the 10-Strategy Matrix Benchmark

To execute all 150 benchmark evaluations across the 10 strategies:

```powershell
python research/loop16/benchmark/run_strategy_benchmark.py
```

**Expected Artifacts Generated:**
- `research/loop16/results/loop16_strategy_benchmark_results.json`
- `research/loop16/strategy_results.json`
- `research/loop16/failure_records.json`

---

## 4. Step 3: Run the Automated Test Suite

Execute the unit and integration tests covering the Loop 16 Adaptive Strategy Selector:

```powershell
pytest tests/test_loop16_adaptive_ocr.py -v
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
