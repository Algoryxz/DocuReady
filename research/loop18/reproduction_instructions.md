# Loop 18 Reproduction Instructions

This document provides step-by-step commands to independently reproduce all evaluations, stress benchmarks, and test suites conducted during Loop 18.

---

## 1. Prerequisites & Environment Verification

Ensure Python 3.12+ and Tesseract OCR 5.5.0 are installed and accessible on Windows x64.

```powershell
# 1. Verify current branch is loop-18
git status
# Branch should be: loop-18-independent-accuracy-and-critical-field-validation

# 2. Verify frozen Loop 10 release binary SHA-256 integrity
Get-FileHash apps/desktop/out/DocuReady-win32-x64/DocuReady.exe -Algorithm SHA256
# Expected: 86339BA01C1E0E73B1A8E3CF799880C957F24E3691B0B4EE0717A861FCC5DCD2

Get-FileHash apps/desktop/out/DocuReady-win32-x64/resources/app.asar -Algorithm SHA256
# Expected: D72882945989E468C76CE43840C16457AA94E59584DC6F953689A28A0014F27E

Get-FileHash apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar/docuready_sidecar.exe -Algorithm SHA256
# Expected: 5CF296943A640F41784B27786B59EE679C59DAA6BDA59CA2ACBEAE7621770B4C
```

---

## 2. Dataset & Fixture Generation

Build the 25-document expanded corpus and 4 controlled adversarial stress fixtures:

```powershell
python research/loop18/corpus_builder.py
```
*Outputs: `research/loop18/corpus/`, `ground_truth/`, `critical_fields/`, `stress_fixtures/`, and `dataset_manifest.json`.*

---

## 3. Comprehensive Strategy Benchmark (25 Documents)

Executes the four-strategy matrix across all 25 documents with spatial line reconstruction and dual-metric scoring:

```powershell
python research/loop18/benchmark/run_strategy_benchmark.py
```
*Outputs: `research/loop18/strategy_results.json`.*

---

## 4. Adversarial Critical-Field Stress Benchmark

Tests the four severe stress cases (similar digits, rubber stamp overlay, multi-column amounts, skew/contrast):

```powershell
python research/loop18/benchmark/run_stress_benchmark.py
```
*Outputs: `research/loop18/results/stress_benchmark_results.json`.*

---

## 5. Same-Corpus Comparative Verification (Loop 16 vs Loop 17)

Runs an apples-to-apples comparison on the exact 15 documents from Loop 16:

```powershell
python research/loop18/benchmark/run_same_corpus_comparison.py
```
*Outputs: `research/loop18/results/same_corpus_comparison.json`.*

---

## 6. Comprehensive Test Suite

Execute all verification test suites:

```powershell
# 1. Loop 18 Test Suite
pytest tests/test_loop18_accuracy_and_critical_fields.py -v

# 2. Previous Loop Tests (Loops 14 - 17)
pytest tests/test_loop14_corpus_and_routing.py -v
pytest tests/test_loop15_region_ocr.py -v
pytest tests/test_loop16_adaptive_selector.py -v
pytest tests/test_loop17_adaptive_efficiency.py -v

# 3. Golden Baselines
pytest tests/test_golden_baselines.py -v
```
