# Loop 21 Independent Reproduction Instructions

This guide provides step-by-step instructions to reproduce the complete Loop 21 benchmark, verify test suites, and audit frozen release binaries.

---

## 1. Environment & Prerequisites

- **Operating System**: Windows x64
- **Python**: Python 3.12+ (standard library + `pytesseract`, `Pillow`, `numpy`, `pytest`)
- **Node.js**: Node v20+ (for Electron desktop test suite)
- **OCR Engine**: Tesseract OCR installed locally (e.g. `C:\Program Files\Tesseract-OCR\tesseract.exe` or discovered in PATH)
- **Repository Branch**: `loop-21-header-fusion-and-decimal-integrity`

---

## 2. Step 1: Verify Git Branch & Frozen Binaries

Check out the active Loop 21 branch:
```powershell
git checkout loop-21-header-fusion-and-decimal-integrity
```

Verify SHA-256 hashes of the frozen Loop 10 competition release binaries:
```powershell
powershell -Command "
Get-FileHash apps/desktop/out/DocuReady-win32-x64/DocuReady.exe, apps/desktop/out/DocuReady-win32-x64/resources/app.asar, apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar/docuready_sidecar.exe | Format-List
"
```
Expected Hashes:
- `DocuReady.exe`: `86339BA01C1E0E73B1A8E3CF799880C957F24E3691B0B4EE0717A861FCC5DCD2`
- `app.asar`: `D72882945989E468C76CE43840C16457AA94E59584DC6F953689A28A0014F27E`
- `docuready_sidecar.exe`: `5CF296943A640F41784B27786B59EE679C59DAA6BDA59CA2ACBEAE7621770B4C`

---

## 3. Step 2: Run Unit & Integration Test Suites

Execute the Loop 21 unit tests:
```powershell
pytest tests/test_loop21_header_and_decimal.py
```
Expected output:
```
6 passed in ~1.7s
```

Execute non-regression suites from Loops 19 and 20:
```powershell
pytest tests/test_loop19_table_association.py tests/test_loop20_blind_generalization.py
```
Expected output:
```
16 passed in ~10s
```

Execute the Desktop Electron test suite:
```powershell
npm test --prefix apps/desktop
```
Expected output:
```
pass 25, fail 0
```

---

## 4. Step 3: Execute the Full 40-Document Benchmark

Run the comprehensive benchmark runner across all 40 documents:
```powershell
python research/loop21/benchmark/run_loop21_benchmark.py
```

Expected Summary Output:
```
Total Documents: 40
Total Fields:    83
SEM Matches:     62 (74.70%)
Verified Claims: 73
  - Exact Match: 59
  - False Verif: 14
Abstentions:     10
Critical Field Precision: 80.82%
False Verification Rate:  19.18%
Mean Overhead:   2.15 ms - 3.71 ms
Mean Latency:    ~450 ms - 800 ms
```

Verify that results are written to `research/loop21/results/benchmark_results.json`.
