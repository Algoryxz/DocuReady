# DOCUREADY — LOOP 11 REPRODUCTION INSTRUCTIONS
## Step-by-Step Guide to Re-Executing the Independent Benchmark & Profiler

**Project:** DocuReady  
**Phase:** Phase 12 — Reproducibility Documentation  
**Target Environment:** Windows 10/11 x64 with Python 3.12  
**Date:** 2026-11-22  

---

## 1. PREREQUISITES & REPOSITORY SETUP

1. **Verify Git Branch & Clean State:**
   Ensure you are on the isolated research branch:
   ```bash
   git checkout loop-11-independent-dataset-benchmark
   git status
   ```

2. **Verify Python Virtual Environment:**
   Ensure Python 3.12 is active and all repository dependencies are installed:
   ```bash
   python -m pip install -e .
   ```

3. **Verify Bundled Tesseract Engine:**
   Ensure the packaged Tesseract OCR binary and trained models exist:
   ```powershell
   Test-Path "apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar/tesseract/tesseract.exe"
   Get-ChildItem "apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar/tesseract/tessdata/*.traineddata"
   ```

---

## 2. SYNTHESIZING / RE-GENERATING BENCHMARK DATASETS

To re-generate all 230 independent benchmark samples across FUNSD, SROIE, Indic OCR, DocLayNet, and DIBCO:
```bash
python research/loop11_benchmark/datasets/acquire_benchmark_data.py
```
*Expected Output:*
```
=== SYNTHESIZING & VERIFYING INDEPENDENT BENCHMARK SUITES ===
Synthesized 230 total independent benchmark samples across 5 suites.
Summary saved to: .../research/loop11_benchmark/benchmark_suites_summary.json
```

---

## 3. EXECUTING THE FULL INDEPENDENT BENCHMARK

To run the full evaluation suite across all 230 samples against the sealed baseline:
```bash
python research/loop11_benchmark/harness/benchmark_runner.py
```
*Expected Output:*
```
================================================================================
DOCUREADY LOOP 11: INDEPENDENT DATASET BENCHMARK & PERFORMANCE FRONTIER
================================================================================
Running 5 Independent Suites against Sealed Baseline...
[1/5] Running FUNSD Benchmark (50 samples)...
[2/5] Running SROIE Benchmark (60 samples)...
[3/5] Running Indic Multilingual OCR Benchmark (40 samples)...
[4/5] Running DocLayNet Layout Benchmark (30 samples)...
[5/5] Running DIBCO Degradation Benchmark (50 samples)...
Saved full benchmark results to: .../results/loop11_benchmark_results.json
Saved 157 failure cases to: .../results/loop11_failure_cases.json
```

---

## 4. RUNNING THE STAGE LATENCY & MEMORY PROFILER

To profile the exact sub-stage breakdown (rasterization, initial OCR, upright gate, skew estimation, deskew rotation, line clustering) and RSS memory:
```bash
python research/loop11_benchmark/harness/perf_profiler.py
```
*Expected Output:*
```
=== STAGE PROFILING SUMMARY ===
Mean Total Page Latency: ~746 ms (P95: ~990 ms)
Peak Process RSS Memory: ~130 MB
  rasterization       :  ~48 ms (6.4%)
  initial_ocr         : ~545 ms (73.0%)
  skew_estimation     :  ~98 ms (13.1%)
  deskew_rotation     :  ~55 ms (7.3%)
```

---

## 5. RUNNING THE MULTILINGUAL GENERALIZATION EXPERIMENT

To compare Control (`eng`) vs Treatment (`eng+hin+ori`) on paired bilingual documents:
```bash
python research/loop11_benchmark/experiments/exp_multilingual_generalization.py
```

---

## 6. RUNNING THE AUTOMATED TEST SUITE

To verify all Loop 11 benchmark artifacts, ground truths, and profiling results:
```bash
pytest tests/test_loop11_independent_benchmark.py -v
```
*Expected Result:* `5 passed in ~0.20s`

To run the complete cross-loop regression suite:
```bash
pytest tests/test_loop06_decision_engine.py tests/test_loop07_adversarial_generalization.py tests/test_loop08_desktop_workflow_integrity.py tests/test_loop09_release_integrity.py tests/test_loop10_demo_reliability.py tests/test_loop11_independent_benchmark.py -v
```
*Expected Result:* `61 passed in ~70s`
