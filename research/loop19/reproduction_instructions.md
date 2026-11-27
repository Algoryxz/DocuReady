# Loop 19 Reproduction Instructions

This document provides step-by-step commands to independently reproduce all evaluations, table benchmarks, and test suites conducted during Loop 19.

---

## 1. Environment & Release Integrity Verification

Ensure Python 3.12+ and Tesseract OCR 5.5.0 are accessible on Windows x64.

```powershell
# 1. Verify current branch is loop-19
git status
# Branch should be: loop-19-table-aware-evidence-and-field-association

# 2. Verify frozen Loop 10 release binary SHA-256 integrity
Get-FileHash apps/desktop/out/DocuReady-win32-x64/DocuReady.exe -Algorithm SHA256
# Expected: 86339BA01C1E0E73B1A8E3CF799880C957F24E3691B0B4EE0717A861FCC5DCD2

Get-FileHash apps/desktop/out/DocuReady-win32-x64/resources/app.asar -Algorithm SHA256
# Expected: D72882945989E468C76CE43840C16457AA94E59584DC6F953689A28A0014F27E

Get-FileHash apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar/docuready_sidecar.exe -Algorithm SHA256
# Expected: 5CF296943A640F41784B27786B59EE679C59DAA6BDA59CA2ACBEAE7621770B4C
```

---

## 2. Table Fixture Generation

Build the 10 controlled table fixtures across categories A through J:

```powershell
python research/loop19/corpus_builder.py
```
*Outputs: `research/loop19/tables/` and `research/loop19/dataset_manifest.json`.*

---

## 3. Table Association Benchmark

Executes the Table-Aware Spatial Evidence Association benchmark across all 10 categories:

```powershell
python research/loop19/benchmark/run_table_benchmark.py
```
*Outputs: `research/loop19/results/table_benchmark_results.json`.*

---

## 4. Adversarial Stress Benchmark

Re-runs the adversarial stress suite to verify that `STRESS_03` multi-column extraction reaches 100%:

```powershell
python research/loop18/benchmark/run_stress_benchmark.py
```
*Outputs: `research/loop18/results/stress_benchmark_results.json`.*

---

## 5. Comprehensive Test Execution

Execute all validation test suites:

```powershell
# 1. Loop 19 Table Association Tests
pytest tests/test_loop19_table_association.py -v

# 2. Previous Loop Tests (Loops 16 - 18)
pytest tests/test_loop18_accuracy_and_critical_fields.py -v
pytest tests/test_loop17_adaptive_efficiency.py -v
pytest tests/test_loop16_adaptive_ocr.py -v

# 3. Golden Baselines
pytest tests/test_golden_baseline.py tests/test_pack_golden_baseline.py -v

# 4. Electron Desktop Tests
npm test --prefix apps/desktop
```
