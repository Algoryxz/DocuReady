# LOOP 17: Baseline Reproduction & Audit Report

## 1. Reproduction Mandate & Methodology

Before initiating any optimization experiments for Loop 17, we conducted an independent reproduction and audit of the starting qualified baseline: **Loop 16 (commit `de63549`)**.

The reproduction protocol:
1. Checked out the isolated branch `loop-17-adaptive-ocr-efficiency-and-reliability` directly from `de63549`.
2. Verified that the frozen Loop 10 competition release binaries in `apps/desktop/out/DocuReady-win32-x64/` remain 100% bit-exact to their sealed SHA-256 baseline hashes.
3. Executed automated regression suites across all prior loops (golden baselines, desktop unit tests, Loop 14, 15, and 16 tests).
4. Inspected and recalculated the strategy metrics across the 15-document evaluation corpus (150 strategy runs: 15 documents $\times$ 10 strategies).

---

## 2. Reproduced Benchmark Metrics (15-Document Corpus)

All 10 strategies from the Loop 16 benchmark were independently re-evaluated and their aggregate metrics verified:

| Strategy ID | Strategy Name | Reproduced CER (%) | Baseline CER (%) | Reproduced WER (%) | Baseline WER (%) | Inversion Rate (%) | Invocations / Page | Mean Latency (ms) | False Findings | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| `STRATEGY_A_ENG` | English Only | **46.43%** | 46.43% | **54.27%** | 54.27% | 7.85% | 1.00 | 1026.6 ms | 1 | **EXACT MATCH** |
| `STRATEGY_B_HIN` | Hindi Only | **71.94%** | 71.94% | **85.26%** | 85.26% | 8.21% | 1.00 | 1247.3 ms | 1 | **EXACT MATCH** |
| `STRATEGY_C_ORI` | Odia Only | **74.01%** | 74.01% | **93.39%** | 93.39% | 5.28% | 1.00 | 1386.9 ms | 1 | **EXACT MATCH** |
| `STRATEGY_D_ENG_HIN` | Eng + Hin Compound | **36.06%** | 36.06% | **45.60%** | 45.60% | 7.23% | 1.00 | 1479.1 ms | 1 | **EXACT MATCH** |
| `STRATEGY_E_ENG_ORI` | Eng + Ori Compound | **34.56%** | 34.56% | **45.46%** | 45.46% | 5.27% | 1.00 | 1520.0 ms | 1 | **EXACT MATCH** |
| `STRATEGY_F_GLOBAL_ALL` | Global Multilingual | **24.31%** | 24.31% | **35.79%** | 35.79% | 4.16% | 1.00 | 1960.5 ms | 1 | **EXACT MATCH** |
| `STRATEGY_G_PAGE_ROUTING` | Whole-Page Routing | **42.24%** | 42.24% | **50.53%** | 50.53% | 7.85% | 1.87 | 2301.7 ms | 1 | **EXACT MATCH** |
| `STRATEGY_H_REGION_ROUTING` | Region-Aware Routing | **29.46%** | 29.46% | **43.03%** | 43.03% | 4.86% | 2.67 | 4402.0 ms | 1 | **EXACT MATCH** |
| `STRATEGY_I_REGION_FALLBACK` | Region + Fallback | **29.46%** | 29.46% | **43.03%** | 43.03% | 4.86% | 2.67 | 4559.1 ms | 1 | **EXACT MATCH** |
| **`STRATEGY_J_ADAPTIVE`** | **Adaptive Strategy** | **21.46%** | **21.46%** | **32.45%** | **32.45%** | **4.57%** | **1.13** | **3034.9 ms** | **0** | **EXACT MATCH** |

---

## 3. Split-Level Reproduction Summary

The split-level breakdown between `PRIMARY_VALIDATION` (11 documents) and `SEALED_CHALLENGE` (4 documents) was also reproduced bit-for-bit:

### 3.1. Primary Validation Cohort (11 Documents)
- `STRATEGY_F_GLOBAL_ALL`: CER 22.58% | WER 35.61% | Invocations 1.00 | Latency 2203.4 ms
- `STRATEGY_H_REGION_ROUTING`: CER 27.39% | WER 40.66% | Invocations 2.91 | Latency 4929.6 ms
- `STRATEGY_J_ADAPTIVE`: CER 26.97% | WER 39.44% | Invocations 1.18 | Latency 3393.2 ms

### 3.2. Sealed Challenge Cohort (4 Documents)
- `STRATEGY_F_GLOBAL_ALL`: CER 29.07% | WER 36.29% | Invocations 1.00 | Latency 1292.4 ms
- `STRATEGY_H_REGION_ROUTING`: CER 35.14% | WER 49.55% | Invocations 2.00 | Latency 2951.1 ms
- `STRATEGY_J_ADAPTIVE`: CER **6.31%** | WER **13.25%** | Invocations 1.00 | Latency 2049.7 ms

---

## 4. Test Suite Baseline Reproduction

All test suites were executed on the active branch:
1. `pytest tests/test_loop16_adaptive_ocr.py -v`: **10 passed in 11.28s** (100% pass).
2. `pytest tests/test_golden_baseline.py tests/test_pack_golden_baseline.py -v`: **22 passed in 9.11s** (100% bit-exact).
3. `pytest tests/test_loop14_multilingual_ocr.py tests/test_loop15_region_aware_ocr.py tests/test_loop16_adaptive_ocr.py -v`: **27 passed in 17.79s** (100% pass).
4. `npm test --prefix apps/desktop`: **25 passed in 25.22s** (100% pass).

---

## 5. The Latency Gap: Core Problem for Loop 17

The reproduction confirms both the strengths and the primary engineering defect of Loop 16:
- **Strength:** Adaptive OCR achieved the best accuracy across the full corpus (21.46% CER vs 24.31% for Global All and 29.46% for Region Routing) with zero false findings and low invocation count (1.13).
- **Defect:** Adaptive OCR averaged **3034.9 ms** per document, which is **54.8% slower** than Global Multilingual (`STRATEGY_F` at **1960.5 ms**).

Closing this latency gap by at least **20%** (targeting $\le 2420\text{ ms}$) without degrading CER/WER is the primary experimental mission of Loop 17.
