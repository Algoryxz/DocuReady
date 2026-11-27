# LOOP 20: Step-by-Step Reproduction Instructions

## 1. Prerequisites

- Platform: Windows x64
- Python: Version 3.12+
- Dependencies: `pytesseract`, `Pillow`, `numpy`, `pytest`
- System OCR: Tesseract 5.x installed in standard system paths or discoverable via `docuready.ingest.tesseract_discovery`.

---

## 2. Reproduction Commands

### Step 1: Verify Release Protection & Clean Environment
```powershell
# Verify frozen Loop 10 binaries are bit-exact
Get-FileHash apps/desktop/out/DocuReady-win32-x64/DocuReady.exe, apps/desktop/out/DocuReady-win32-x64/resources/app.asar, apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar/docuready_sidecar.exe -Algorithm SHA256 | Format-Table -AutoSize
```

### Step 2: Generate the 34-Document Evaluation Corpus
```powershell
python research/loop20/corpus_builder.py
```

### Step 3: Execute the Multi-Cohort Generalization Benchmark
```powershell
python research/loop20/benchmark/run_loop20_benchmark.py
```
Expected output:
- Total Evaluated Fields: 65
- Spatial Exact Matches: 54 / 65 (83.08%)
- False Verification Rate: 11.48%
- Critical Field Precision: 88.52%
- Mean Table Overhead: ~2.32 ms

### Step 4: Run the Dedicated Test Suite
```powershell
python -m pytest tests/test_loop20_blind_generalization.py -v
```
Expected output: 8 passed, 0 failed.

### Step 5: Execute Regression Verification Across All Loops
```powershell
python -m pytest tests/test_loop19_table_association.py tests/test_loop18_accuracy_and_critical_fields.py tests/test_loop17_adaptive_efficiency.py tests/test_loop16_adaptive_ocr.py tests/test_golden_baseline.py tests/test_pack_golden_baseline.py -v
```
Expected output: 56 passed, 0 failed.

### Step 6: Execute Desktop Electron Tests
```powershell
npm test --prefix apps/desktop
```
Expected output: 25 passed, 0 failed.
