# DOCUREADY — LOOP 13
## Independent Reproduction Instructions

**Document:** Verification and Reproduction Protocol  
**Target Audience:** Competition Judges, External Auditors, and Independent Researchers  
**Branch:** `loop-13-column-aware-reading-order`  
**Starting Qualified Baseline Commit:** `756062b`  

---

### 1. Prerequisites & Environment Setup

Verify the environment matches standard competition specifications:

- **OS:** Windows 10/11 x64 (or Linux x64 with Wine / Python 3.12)
- **Python:** Python 3.12+ with virtual environment activated
- **Dependencies:** `pytest`, `pytest-asyncio`, `pyyaml`, `pillow`, `pytesseract`
- **Node.js:** Node.js v20+ (for Electron desktop tests)

```powershell
# Ensure working tree is on the isolated Loop 13 research branch
git status
# Confirm branch: loop-13-column-aware-reading-order
```

---

### 2. Verify Freeze & Immobility of Loop 10 Production Binaries

Confirm that protected Loop 10 production release artifacts have not been modified:

```powershell
# Calculate SHA-256 of packaged desktop binaries
Get-FileHash apps/desktop/out/DocuReady-win32-x64/DocuReady.exe -Algorithm SHA256
# Expected: 86339ba...

Get-FileHash apps/desktop/out/DocuReady-win32-x64/resources/app.asar -Algorithm SHA256
# Expected: d728829...

Get-FileHash apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar/docuready_sidecar.exe -Algorithm SHA256
# Expected: 5cf2969...
```

---

### 3. Reproduce the Baseline Multi-Column Defect

Execute the reproduction script to observe the raw scanline interleaving defect:

```powershell
python research/loop13/reproduce_defect.py
```

**Expected Output:**
The script demonstrates that baseline 1D scanline clustering interleaves words from Column 1 and Column 2:
> *Baseline Interleaved Line 1: The post-matric scholarship State verification offices*  
> *Baseline Interleaved Line 2: scheme guidelines require shall inspect educational*

---

### 4. Execute the Indian Data Portals Survey

Run the network inspection script across all four Indian government and research portals:

```powershell
python research/loop13/portal_survey.py
```

**Expected Output:**
- `data.gov.in` $\to$ HTTP 200 OK
- `ndap.niti.gov.in` $\to$ HTTP 200 OK (Client-side SPA)
- `microdata.gov.in/nada` $\to$ HTTP 200 OK
- `indiadataportal.com` $\to$ HTTP 200 OK
- Results stored in `research/loop13/portal_survey_results.json` and `research/loop13/india_dataset_catalog.json`.

---

### 5. Run the Spatial Reading Order Benchmark

Execute the quantitative benchmark comparing the Loop 12 baseline against Loop 13:

```powershell
python research/loop13/benchmark/run_loop13_benchmark.py
```

**Expected Output:**
- Multi-Column Text WER drops from 66.67% to 0.00%.
- Bracketed Multi-Column WER drops from 31.58% to 0.00%.
- Overall WER drops from 27.49% to 0.00%.
- Pairwise Inversion Error Rate drops from 8.74% to 0.00%.
- Average latency overhead $\approx 1.0\text{ ms}$.
- Results stored in `research/loop13/results/loop13_benchmark_results.json`.

---

### 6. Run Sub-Stage Performance & Memory Profiler

Profile the CPU latency and heap memory allocation of spatial reconstruction:

```powershell
python research/loop13/benchmark/perf_profiler_loop13.py
```

**Expected Output:**
- Two-Column reconstruction $\approx 4.9\text{ ms}$ / page.
- Single-Column bypass $\approx 2.2\text{ ms}$ / page.
- Peak memory overhead $\le 50\text{ KB}$.
- Results stored in `research/loop13/results/loop13_profiling_results.json`.

---

### 7. Run Comprehensive Test Suites

#### A. Loop 13 Unit & Integration Suite (10 tests)
```powershell
pytest tests/test_loop13_column_aware_reading_order.py -v
# Result: 10 passed in ~2.5s
```

#### B. Golden Baseline & Checksum Parity (22 tests)
```powershell
pytest tests/test_golden_baseline.py tests/test_pack_golden_baseline.py -v
# Result: 22 passed in ~8.5s (Bit-exact parity preserved)
```

#### C. Cross-Loop Regression Suite (117 tests)
```powershell
pytest tests/test_loop02_orientation_assurance.py tests/test_loop03_skew_recovery.py tests/test_loop04_deskew_reliability.py tests/test_loop05_extraction_normalization.py tests/test_loop06_decision_engine.py tests/test_loop07_adversarial_generalization.py tests/test_loop08_desktop_workflow_integrity.py tests/test_loop09_release_integrity.py tests/test_loop10_demo_reliability.py tests/test_loop11_independent_benchmark.py tests/test_loop12_benchmark_integrity.py tests/test_loop13_column_aware_reading_order.py -v
# Result: 117 passed in ~4m
```

#### D. Electron Desktop & Sidecar Test Suite (25 tests)
```powershell
npm test --prefix apps/desktop
# Result: 25 passed in ~28s
```
