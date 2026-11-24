# Loop 28 Reproduction & Verification Guide

## 1. Environment Setup
```bash
git checkout loop-28-cross-document-verification-reliability
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
```

## 2. Reproduce Benchmark
```bash
python research/loop28/benchmark/run_loop28_benchmark.py
```

## 3. Reproduce Ablations
```bash
python research/loop28/ablations/run_ablations.py
```

## 4. Run Test Suites
```bash
pytest tests/test_loop28_cross_document.py tests/test_loop27_identifier_integrity.py tests/test_loop09_release_integrity.py -q
npm test --prefix apps/desktop
```
