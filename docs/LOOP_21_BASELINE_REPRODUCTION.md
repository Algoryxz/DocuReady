# LOOP 21: Baseline Reproduction & Forensic Analysis Report

## 1. Reproduction Governance & Execution

Before initiating any implementation changes for Loop 21, the Loop 20 baseline (`1dcd69d`) was independently executed and reproduced on Windows x64.

### Execution Command:
```powershell
python research/loop20/benchmark/run_loop20_benchmark.py
```

---

## 2. Baseline Reproduction Metrics

| Baseline Metric | Reported Loop 20 Value | Reproduced Loop 21 Baseline | Status |
| :--- | :---: | :---: | :---: |
| **Total Evaluated Documents** | 34 | **34** | **Exact Match** |
| **Total Critical Fields** | 65 | **65** | **Exact Match** |
| **Spatial Exact Matches (SEM)** | 54 (83.08%) | **54 (83.08%)** | **Exact Match** |
| **Cohort A (Development) SEM** | 16 / 16 (100.0%) | **16 / 16 (100.0%)** | **Exact Match** |
| **Cohort B (Validation) SEM** | 13 / 16 (81.25%) | **13 / 16 (81.25%)** | **Exact Match** |
| **Cohort C (Blind Evaluation) SEM** | 14 / 20 (70.00%) | **14 / 20 (70.00%)** | **Exact Match** |
| **Cohort D (Challenge & Traps) SEM**| 11 / 13 (84.62%) | **11 / 13 (84.62%)** | **Exact Match** |
| **False Verification Count (FVC)** | 7 | **7** | **Exact Match** |
| **False Verification Rate (FVR)** | 11.48% | **11.48%** | **Exact Match** |
| **Critical Field Precision (CFP)** | 88.52% | **88.52%** | **Exact Match** |
| **Mean Table Reconstruction Overhead** | 2.32 ms | **2.65 ms** | **Reproduced (<3ms)** |
| **Mean Page Latency** | 589.29 ms | **565.77 ms** | **Reproduced** |
| **Frozen Loop 10 Release Hashes** | Bit-exact | **Bit-exact** | **Verified** |

---

## 3. Targeted Baseline Failures Confirmed

The reproduction confirmed the two primary target failure modes for Loop 21:

1. **Multi-Tier Header Row Shift (`VAL_05_MULTI_ROW_SUMMARY`)**:
   - `drip_q2_actual`: Extracted correct string `'84500'`, but failed coordinate matching (`row_idx = 3` vs expected `row_idx = 1`) because the top super-header row was counted as row 0, shifting data row indexing.
   - `seed_q1_budget`: Extracted correct string `'40000'`, but failed coordinate matching (`row_idx = 2` vs expected `row_idx = 0`).
2. **Decimal Point Loss (`BLIND_06_CLINICAL_LAB_REPORT`)**:
   - `hba1c_result`: Expected `'5.6'`, but raw Tesseract returned `'56'` due to the small single-pixel decimal point being dropped by standard OCR binarization.
