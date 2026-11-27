# LOOP 24 — COMPREHENSIVE BENCHMARK LEDGER

## 1. Master Benchmark Execution Record

- **Timestamp**: `2026-11-24T10:02:15Z`
- **Benchmark Script**: `research/loop24/benchmark/run_loop24_benchmark.py`
- **Operating Decision Threshold**: $T^* = 70.0$
- **Total Corpus Size**: 82 Documents (Cohort I: 30 docs, Historical: 52 docs)
- **Total Evaluated Fields**: 215 Critical Fields
- **Bit-Exact Determinism**: PASS (Double-run bit-exact invariance verified)

---

## 2. Cohort-by-Cohort Ledger Breakdown

| Cohort Name | Docs | Fields | Verified Claims | Exact Matches | False Verifications | Abstentions | Precision (%) | Coverage (%) | Mean Overhead |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A_development** | 8 | 16 | 15 | 15 | 0 | 1 | 100.00% | 93.75% | 2.82 ms |
| **B_validation** | 8 | 16 | 14 | 14 | 0 | 2 | 100.00% | 87.50% | 2.37 ms |
| **C_blind_evaluation** | 10 | 20 | 14 | 14 | 0 | 6 | 100.00% | 70.00% | 2.41 ms |
| **D_challenge_adversarial** | 8 | 13 | 10 | 10 | 0 | 3 | 100.00% | 76.92% | 1.58 ms |
| **E_hierarchical_headers** | 3 | 6 | 3 | 3 | 0 | 3 | 100.00% | 50.00% | 1.90 ms |
| **F_decimal_integrity** | 3 | 12 | 5 | 5 | 0 | 7 | 100.00% | 41.67% | 1.71 ms |
| **G_evidence_association** | 6 | 12 | 4 | 4 | 0 | 8 | 100.00% | 33.33% | 2.35 ms |
| **H_microfont_narrow_gutter** | 6 | 18 | 6 | 6 | 0 | 12 | 100.00% | 33.33% | 1.74 ms |
| **I_development** | 8 | 28 | 9 | 9 | 0 | 19 | 100.00% | 32.14% | 1.59 ms |
| **I_calibration** | 8 | 27 | 3 | 3 | 0 | 24 | 100.00% | 11.11% | 2.35 ms |
| **I_blind_evaluation** | 10 | 34 | 5 | 5 | 0 | 29 | 100.00% | 14.71% | 2.00 ms |
| **I_challenge_adversarial** | 4 | 13 | 2 | 2 | 0 | 11 | 100.00% | 15.38% | 1.36 ms |
| **COHORT I AGGREGATE** | **30** | **102** | **19** | **19** | **0** | **83** | **100.00%** | **18.63%** | **1.90 ms** |
| **COMBINED GRAND TOTAL** | **82** | **215** | **90** | **90** | **0** | **125** | **100.00%** | **41.86%** | **2.08 ms** |

---

## 3. Authoritative Storage

The master benchmark JSON is persistently preserved at:
`research/loop24/results/benchmark_results.json`
Run 1 and Run 2 verification artifacts:
`research/loop24/results/benchmark_run1.json`
`research/loop24/results/benchmark_run2.json`
