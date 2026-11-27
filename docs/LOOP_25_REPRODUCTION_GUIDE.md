# Loop 25 - Reproduction Guide

## Environment Setup

```bash
# Verify Python environment
python --version  # Python 3.12+

# Run Unit and Integration Tests
python -m pytest tests/test_loop25_row_label_recovery.py -v

# Run Full Regression Suite
python -m pytest -q

# Run Desktop Test Suite
npm test --prefix apps/desktop
```

## Running Benchmark & Calibration

```bash
# 1. Regenerate Corpus J (Optional, already persisted in research/loop25/tables)
python research/loop25/corpus_builder.py

# 2. Run Threshold Calibration Sweep
python research/loop25/benchmark/calibrate_thresholds.py

# 3. Execute Comprehensive Double-Run Benchmark
python research/loop25/benchmark/run_loop25_benchmark.py

# 4. Run Ablation Suite
python research/loop25/benchmark/run_ablations.py
```
