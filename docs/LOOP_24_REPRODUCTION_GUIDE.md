# LOOP 24 — REPRODUCTION & VERIFICATION GUIDE

## 1. Environment Prerequisites

- **OS**: Windows x64
- **Python**: 3.12+
- **Node.js**: 20+
- **OCR Engine**: Tesseract OCR installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`
- **Git Branch**: `loop-24-independent-generalization-calibration`

---

## 2. Step-by-Step Reproduction Commands

### Step 1: Verify Research Branch & Release Baseline
```powershell
# 1. Verify git branch
git status

# 2. Verify bit-exact hash invariance on the 5 protected Loop 10 release binaries
python -c "import hashlib; p = ['apps/desktop/out/DocuReady-win32-x64/DocuReady.exe', 'apps/desktop/out/DocuReady-win32-x64/resources/app.asar', 'apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar/docuready_sidecar.exe', 'apps/desktop/out/make/squirrel.windows/x64/DocuReady-0.1.0-Setup.exe', 'apps/desktop/out/make/zip/win32/x64/DocuReady-win32-x64-0.1.0.zip']; [print(f, hashlib.sha256(open(f, 'rb').read()).hexdigest().upper()) for f in p]"
```

### Step 2: Regenerate Corpus & Metadata (Deterministic)
```powershell
python research/loop24/corpus_builder.py
```

### Step 3: Run Calibration Threshold Sweep (Cohorts A & B)
```powershell
python research/loop24/benchmark/calibrate_thresholds.py
```

### Step 4: Run Authoritative Benchmark Twice (Determinism Verification)
```powershell
python research/loop24/benchmark/run_loop24_benchmark.py
```

### Step 5: Execute Regression Test Suites
```powershell
# Python regression suite (816 tests)
pytest tests/

# Electron desktop suite (25 tests)
npm test --prefix apps/desktop
```
