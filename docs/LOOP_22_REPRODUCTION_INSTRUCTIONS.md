# Loop 22 — Exact Reproduction Instructions

**Repository:** `Algoryxz/DocuReady`  
**Branch:** `loop-22-evidence-association-reliability`  
**Base Commit:** `4a6a46e`

---

## 1. Prerequisites & Environment Setup

Ensure the following system tools are available:
- Windows x64 Desktop
- Python 3.12+ with virtual environment activated
- Tesseract OCR v5.5.0+ installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Node.js v20+ with npm

Install dependencies:
```bash
pip install -e .
pip install pytest pytest-asyncio numpy pillow pytesseract
```

---

## 2. Step-by-Step Reproduction

### Step 1: Verify Competition Release Integrity
Verify that Loop 10 binaries remain untouched and bit-exact:
```powershell
Get-FileHash apps/desktop/out/DocuReady-win32-x64/DocuReady.exe, `
             apps/desktop/out/DocuReady-win32-x64/resources/app.asar, `
             apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar/docuready_sidecar.exe
```
Expected SHA-256 for `DocuReady.exe`: `86339BA01C1E0E73B1A8E3CF799880C957F24E3691B0B4EE0717A861FCC5DCD2`

### Step 2: Run Unit & Regression Tests
```bash
pytest tests/test_loop22_evidence_association.py tests/test_loop21_header_and_decimal.py tests/test_loop20_blind_generalization.py tests/test_loop19_table_association.py
```
Expected: 27 passed in ~11 seconds.

### Step 3: Run Electron Desktop Workflow Tests
```bash
npm test --prefix apps/desktop
```
Expected: 25 passed in ~33 seconds.

### Step 4: Run the Full 46-Document Benchmark
```bash
python research/loop22/benchmark/run_loop22_benchmark.py
```

Expected Output Summary:
- Total Documents: 46
- Total Fields: 95
- Verified Claims: 70 (73.68% coverage)
- Verified Exact Matches: 67
- False Verifications: 3 (4.29% FVR)
- Abstentions: 25 (26.32% abstention rate)
- Critical Field Precision (CFP): 95.71%
- Mean Table Grid Overhead: ~2.03 ms
- Output JSON: `research/loop22/results/benchmark_results.json`
