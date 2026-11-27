# DOCUREADY — LOOP 14
## Independent Reproduction Instructions

**Protocol:** Verification and Reproduction Protocol  
**Audience:** Competition Judges, External Auditors, and Independent Researchers  
**Active Branch:** `loop-14-india-document-corpus-and-multilingual-ocr`  
**Starting Commit:** `e601d11` (Loop 13)  

---

### 1. Prerequisites & Environment Setup

Verify the environment matches standard competition specifications:

- **OS:** Windows 10/11 x64 (or Linux x64 with Wine / Python 3.12)
- **Python:** Python 3.12+
- **Packages:** `pytest`, `pytest-asyncio`, `pyyaml`, `pillow`, `pytesseract`, `pymupdf`
- **Node.js:** Node.js v20+

```powershell
# Verify active branch
git status
# Expected branch: loop-14-india-document-corpus-and-multilingual-ocr
```

---

### 2. Verify Freeze of Sealed Loop 10 Production Binaries

Confirm that protected Loop 10 production release artifacts have not been altered:

```powershell
Get-FileHash apps/desktop/out/DocuReady-win32-x64/DocuReady.exe -Algorithm SHA256
# Expected: 86339ba...

Get-FileHash apps/desktop/out/DocuReady-win32-x64/resources/app.asar -Algorithm SHA256
# Expected: d728829...

Get-FileHash apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar/docuready_sidecar.exe -Algorithm SHA256
# Expected: 5cf2969...
```

---

### 3. Run the Mandatory Four-Portal Deep Survey

Execute the automated network probe across all four Indian portals:

```powershell
python research/loop14/portal_research.py
```

**Expected Result:**
- `data.gov.in` $\to$ HTTP 200 OK
- `ndap.niti.gov.in` $\to$ HTTP 200 OK (Base) / 404 (Client-side SPA)
- `microdata.gov.in/nada` $\to$ HTTP 200 OK
- `indiadataportal.com` $\to$ HTTP 200 OK
- Results stored in `research/loop14/portal_survey_results.json`.

---

### 4. Build Corpus & Verify Dataset Manifest

Generate the multilingual corpus and verify checksums:

```powershell
python research/loop14/corpus_builder.py
```

**Expected Result:**
- Verified external document `DOC_EXT_01_MOSPI_NADA_GUIDE.pdf` downloaded and cataloged.
- 15 samples tracked with SHA-256 and provenance in `research/loop14/dataset_manifest.json`.

---

### 5. Run the Multilingual OCR & Layout Benchmark

Execute the quantitative benchmark comparing baseline English-only OCR vs Loop 14 Script-Aware Multilingual OCR:

```powershell
python research/loop14/benchmark/run_multilingual_benchmark.py
```

**Expected Result:**
- Hindi Word Error Rate drops from 100.08% to **44.80%** (55.27% reduction).
- Odia Word Error Rate drops from 100.86% to **39.86%** (61.00% reduction).
- English accuracy and single-column baselines are 100% preserved.
- Output artifact written to `research/loop14/results/loop14_benchmark_results.json`.

---

### 6. Run Multilingual Performance Profiler

Profile sub-stage latencies and memory allocation:

```powershell
python research/loop14/benchmark/perf_profiler_multilingual.py
```

**Expected Result:**
- Unicode Script Detection $\le 10\text{ }\mu\text{s}$.
- Hindi/Odia OCR $\approx 240\text{–}270\text{ ms}$ / page.
- Peak memory overhead $\le 1.5\text{ MB}$.
- Output written to `research/loop14/results/loop14_profiling_results.json`.

---

### 7. Run Comprehensive Test Suites

#### A. Loop 14 Multilingual Suite (10 tests)
```powershell
pytest tests/test_loop14_multilingual_ocr.py -v
# Result: 10 passed in ~2.3s
```

#### B. Golden Baseline & Checksum Parity (22 tests)
```powershell
pytest tests/test_golden_baseline.py tests/test_pack_golden_baseline.py -v
# Result: 22 passed in ~9.2s (Bit-exact parity)
```

#### C. Cross-Loop Regression Suite (127 tests)
```powershell
pytest tests/test_loop02_orientation_assurance.py tests/test_loop03_skew_recovery.py tests/test_loop04_deskew_reliability.py tests/test_loop05_extraction_normalization.py tests/test_loop06_decision_engine.py tests/test_loop07_adversarial_generalization.py tests/test_loop08_desktop_workflow_integrity.py tests/test_loop09_release_integrity.py tests/test_loop10_demo_reliability.py tests/test_loop11_independent_benchmark.py tests/test_loop12_benchmark_integrity.py tests/test_loop13_column_aware_reading_order.py tests/test_loop14_multilingual_ocr.py -v
# Result: 127 passed in ~2m 45s
```

#### D. Electron Desktop & Sidecar Test Suite (25 tests)
```powershell
npm test --prefix apps/desktop
# Result: 25 passed in ~19s
```
