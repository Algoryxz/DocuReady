# Loop 23 Reproduction Instructions & Benchmark Execution Runbook

## 1. Prerequisites

- **Operating System:** Windows x64 (Windows 10/11)
- **Python Version:** Python 3.12+ (64-bit)
- **Tesseract OCR:** Tesseract 5.x x64 with `eng`, `hin`, `ori` traineddata
- **Node.js:** Node.js v20+ with npm

---

## 2. Environment Verification

Verify that the active branch is `loop-23-microfont-numeric-and-narrow-gutter`:
```powershell
git branch --show-current
```
Confirm Python dependencies are installed:
```powershell
pip install -r sidecar/requirements.txt
```

---

## 3. Step-by-Step Reproduction Procedure

### Step 1: Verify Release Binary Integrity
Ensure that protected competition release binaries remain bit-exact:
```powershell
Get-FileHash apps/desktop/out/DocuReady-win32-x64/DocuReady.exe, apps/desktop/out/DocuReady-win32-x64/resources/app.asar, apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar/docuready_sidecar.exe | Select-Object Algorithm, Path, Hash | Format-List
```
Expected SHA-256 for `DocuReady.exe`: `86339BA01C1E0E73B1A8E3CF799880C957F24E3691B0B4EE0717A861FCC5DCD2`.

### Step 2: Run Authoritative Metric Ledger Reconciliation
Run the reconciliation script to verify the Loop 22 historical breakdown:
```powershell
python research/loop23/reconcile_authoritative_ledger.py
```

### Step 3: Run Integer Safety Suite
Verify that morphology analysis preserves 100% invariance on integers:
```powershell
python research/loop23/test_integer_safety.py
```

### Step 4: Execute Full Loop 23 Benchmark
Run the comprehensive 52-document benchmark:
```powershell
python research/loop23/benchmark/run_loop23_benchmark.py
```
Output results will be printed to stdout and saved to `research/loop23/results/benchmark_results.json`.

### Step 5: Run Full Test Regressions
Run the core Python test suite:
```powershell
pytest tests/ -v
```
Run the Electron desktop test suite:
```powershell
npm test --prefix apps/desktop
```
All tests must pass with zero failures.
