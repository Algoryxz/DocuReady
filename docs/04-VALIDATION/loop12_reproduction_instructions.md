# DOCUREADY — LOOP 12 REPRODUCTION INSTRUCTIONS
## Step-by-Step Independent Verification Guide

**Project:** DocuReady  
**Loop:** 12  
**Branch:** `loop-12-benchmark-integrity-audit`  

---

## 1. PREREQUISITES & REPOSITORY SAFETY

1. Ensure you are on the isolated audit branch:
   ```powershell
   git checkout loop-12-benchmark-integrity-audit
   ```
2. Verify that the production codebase and Loop 10 binaries remain untouched:
   ```powershell
   git status
   ```

---

## 2. REPRODUCING THE LOOP 12 INTEGRITY AUDIT

### Step 1: Run the Automated Benchmark Integrity Test Suite
Execute the 9 regression and mathematical integrity tests:
```powershell
pytest tests/test_loop12_benchmark_integrity.py -v
```
*Expected Result:* 9 passed in < 0.5 seconds.

### Step 2: Regenerate & Audit Dataset Provenance Records
Run the provenance verification script:
```powershell
python research/loop12_audit/generate_dataset_provenance.py
```
*Expected Result:* Audits 230 samples, confirms 0 duplicate IDs, 0 missing files, and writes `research/loop12_audit/loop12_dataset_provenance.json`.

### Step 3: Run the Metric Forensic Audit
Generate the mathematical audit log:
```powershell
python research/loop12_audit/generate_metric_audit.py
```
*Expected Result:* Writes `research/loop12_audit/loop12_metric_audit.json` detailing the hardcoded IoU and CER target mismatches.

### Step 4: Reconcile the 157 Loop 11 Failures
Run the failure taxonomy reconciler:
```powershell
python research/loop12_audit/reconcile_failures.py
```
*Expected Result:* Reconciles all 157 failures into 83 Metric Artifacts, 50 Production Defects, 14 Physical Limits, and 10 Font Artifacts. Writes `research/loop12_audit/loop12_failure_reconciliation.json`.

### Step 5: Reproduce the Pipeline Sub-Stage Profiling
Run the latency profiler across the 20 test documents:
```powershell
python research/loop11_benchmark/harness/perf_profiler.py
```
*Expected Result:* Mean total page latency ~834 ms (initial OCR ~72%, skew ~15%, deskew ~6%, rasterization ~6%).

### Step 6: Execute the Corrected Benchmark Evaluation
Run the corrected benchmark runner using real bipartite IoU and aligned field matching:
```powershell
python research/loop12_audit/corrected_benchmark_runner.py
```
*Expected Result:* Writes `research/loop12_audit/loop12_corrected_benchmark.json` confirming SROIE 100% Date/Amount extraction, FUNSD 100% token presence, real DocLayNet IoU 0.5186, and Degradation 84% adjusted accuracy.

### Step 7: Verify Full Repository Regression Suite
Run full golden baseline and cross-loop regression suites:
```powershell
pytest tests/test_golden_baseline.py tests/test_pack_golden_baseline.py -v
pytest tests/test_loop06_decision_engine.py tests/test_loop07_adversarial_generalization.py tests/test_loop08_desktop_workflow_integrity.py tests/test_loop09_release_integrity.py tests/test_loop10_demo_reliability.py tests/test_loop11_independent_benchmark.py tests/test_loop12_benchmark_integrity.py -v
```
*Expected Result:* All tests pass with zero regressions.
