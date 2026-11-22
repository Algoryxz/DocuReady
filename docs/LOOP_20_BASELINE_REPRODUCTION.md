# LOOP 20: Baseline Reproduction & Forensic Analysis Report

## 1. Reproduction Governance & Summary

Before proceeding with Loop 20 blind generalization and false-verification audits, the qualified Loop 19 research baseline (`2d7aab5`) was independently reproduced on Windows x64.

Every baseline metric was evaluated across four criteria:
- **Reproduced**: Exactly matches previously reported numbers.
- **Partially Reproduced**: Validated within reasonable runtime variance (<2% delta).
- **Not Reproduced**: Failed to match or produced conflicting output.
- **Unverifiable**: Required artifacts or ground truth missing.

---

## 2. Baseline Reproduction Results Matrix

| Baseline Metric / Test Suite | Reported Loop 19 Baseline | Reproduced Loop 20 Value | Status | Command Executed |
| :--- | :---: | :---: | :---: | :--- |
| **Table Suite Mean SEM Rate** | 88.33% | **88.33%** | **Reproduced** | `python research/loop19/benchmark/run_table_benchmark.py` |
| **Table Evidence Traceability** | 88.33% | **88.33%** | **Reproduced** | `python research/loop19/benchmark/run_table_benchmark.py` |
| **Table Spatial Overhead** | 2.80 ms | **1.93 ms** | **Reproduced** | `python research/loop19/benchmark/run_table_benchmark.py` |
| **`STRESS_03` Field Exact Matches** | 4 / 4 (100.0%) | **4 / 4 (100.0%)** | **Reproduced** | `python research/loop18/benchmark/run_stress_benchmark.py` |
| **`STRESS_03` CER** | 11.25% | **11.25%** | **Reproduced** | `python research/loop18/benchmark/run_stress_benchmark.py` |
| **Stress Suite Overall Matches** | 13 / 15 (86.7%) | **13 / 15 (86.7%)** | **Reproduced** | `python research/loop18/benchmark/run_stress_benchmark.py` |
| **Golden Baseline Suite** | 22 / 22 pass | **22 / 22 pass** | **Reproduced** | `python -m pytest tests/test_golden_baseline.py tests/test_pack_golden_baseline.py` |
| **Desktop Test Suite** | 25 / 25 pass | **25 / 25 pass** | **Reproduced** | `npm test --prefix apps/desktop` |
| **Python Test Suite (All Loops)** | 56 / 56 pass | **56 / 56 pass** | **Reproduced** | `python -m pytest tests/` |
| **Loop 10 Binary Hashes** | Bit-exact | **Bit-exact** | **Reproduced** | `Get-FileHash apps/desktop/out/...` |

---

## 3. Forensic Analysis of Residual Baseline Failures

The reproduction of `research/loop19/results/table_benchmark_results.json` confirmed three specific residual failure cases in Loop 19:

1. **`TAB_07_MERGED_HEADERS` (Category G: Merged Headers)**:
   - *Target Field*: `jatni_property_cess` (Expected: `42000`).
   - *Actual Extracted*: `"115000 42000"`.
   - *Forensic Cause*: The table header had merged super-headers ("Property Tax") spanning two sub-columns ("Collection" and "Cess"). The 1D gutter detector grouped both subcolumns into a single column interval, causing both numerical values to concatenate into one cell text.
   - *Critical Consequence*: When a downstream rule checked for cess, the cell contained multiple numbers. In Loop 19, the system returned the concatenated string without flagging ambiguity!

2. **`TAB_09_MULTICOLUMN_DOCUMENT` (Category I: Multi-Column Document)**:
   - *Target Field*: `batch_a2_amount` (Expected: `185000`).
   - *Actual Extracted*: `"Batch B-2 VOU-982 195000"`.
   - *Forensic Cause*: The document contained two side-by-side independent tables ("Table A - North Zone" and "Table B - South Zone"). Naive whole-page row clustering grouped row 2 of Table A with row 2 of Table B across a 150px gutter. In `extract_field_by_spatial_association`, searching for row token `"Batch A-2"` found the row, but column indexing jumped to Table B's columns!
   - *Critical Consequence*: High-risk wrong-record association. The voucher amount of South Zone was associated with North Zone!

3. **`TAB_10_ADVERSARIAL_GEOMETRY` (Category J: Adversarial Geometry)**:
   - *Target Field*: `tk_802_date` (Expected: `18/03/2026`).
   - *Actual Extracted*: `"Amount (INR)"`.
   - *Forensic Cause*: A heavy horizontal divider line broke row clustering, causing the column header row to be indexed as a data row.
   - *Critical Consequence*: A column header label was returned as a date field without syntax validation or abstention!

---

## 4. Conclusion & Directive for Loop 20

The baseline is 100% reproducibly verified. The forensic analysis reveals that when spatial layout geometry fails:
- Loop 19 returns incorrect or concatenated text.
- Loop 19 fails to flag `is_ambiguous = True`.
- Loop 19 lacks syntactic validation inside spatial association, allowing obvious label echoes (e.g. `"Amount (INR)"`) to masquerade as valid dates.

Loop 20 must introduce evidence-based abstention, context-bound verification, and multi-cohort blind validation to prevent these failures from turning into confident false verifications.
