# Loop 22 Metric Discrepancy & Authoritative Ledger Reconciliation

## Executive Summary

During the transition from Loop 22 to Loop 23, an audit of the Loop 22 benchmark deliverables (`docs/LOOP_22_FINAL_REPORT.md` and `research/loop22/results/benchmark_results.json`) revealed two specific accounting anomalies:

1. **Table Row Sum Discrepancy:** The cohort breakdown table in Section 4.1 of `docs/LOOP_22_FINAL_REPORT.md` displayed row numbers that summed to 74 verified claims (71 exact matches, 3 false verifications, 21 abstentions), whereas the **TOTAL** row and the benchmark summary asserted 70 verified claims (67 exact matches, 3 false verifications, 25 abstentions).
2. **SEM (Spatial Extraction Match) vs. Verified Exact Yield:** The benchmark summary reported `sem_passes = 75` (78.95%), whereas exact verified claims were reported as 67 (70.53% of all 95 fields, or 95.71% precision among 70 verified claims).

This document establishes the definitive forensics, traces the provenance of both figures, provides the bit-exact authoritative ledger from `research/loop22/results/benchmark_results.json`, and defines the exact mathematical formulations for all metrics used in Loop 23.

---

## 1. Root Cause Forensics

### 1.1 Table Row Sum vs. Summary Total
Inspection of the benchmark runner script (`research/loop22/run_loop22_benchmark.py`) and its serialized output (`research/loop22/results/benchmark_results.json`) confirmed that:
- The JSON output file is the **authoritative machine-generated ledger**. It contains 46 evaluated documents, 95 total critical fields, 70 verified claims, 67 exact matches, 3 false verifications, and 25 abstentions.
- The summary block and the `TOTAL` row of `docs/LOOP_22_FINAL_REPORT.md` matched this machine output exactly (95 fields, 70 verified, 67 exact, 3 false, 25 abstained).
- The individual rows for cohorts A through G in `docs/LOOP_22_FINAL_REPORT.md` were manually transcribed from an earlier intermediate test run before the final 46-document dataset manifest was locked. Specifically:
  - Cohort C (Blind Evaluation) was recorded with 23 fields instead of the actual 20 fields present in the manifest.
  - Cohort D (Challenge Adversarial) was recorded with 16 fields instead of 13.
  - Cohort F (Decimal Integrity) was recorded with 6 fields instead of 12 (the 6 baseline fields plus 6 boundary stress fields).
  - Cohort G (Evidence Association) was recorded with 8 verified instead of 4 verified (the stricter confidence floor of $T=60.0$ and single-cell token guard converted 4 borderline extractions into safe abstentions in the final run).

### 1.2 Mathematical Derivation of SEM (Spatial Extraction Match)
In the benchmark pipeline, fields can be extracted correctly at the spatial geometry stage, but downstream verification filters (such as confidence thresholds, multi-token syntax guards, or negative control matching) determine whether the system commits to a verification claim or abstains.

The 75 SEM passes out of 95 fields (78.95%) break down as follows:
$$\text{SEM Passes} = \text{Verified Exact Matches } (67) + \text{PASS\_EMPTY\_CORRECT } (3) + \text{Abstained Spatial Exacts } (5) = 75$$

Where:
- **Verified Exact Matches (67):** Spatial extraction extracted the exact ground truth string, and verification confidence exceeded $T \ge 60.0$, yielding a verified claim.
- **PASS_EMPTY_CORRECT (3):** Negative control test fields where ground truth is empty, no claim was made, and the system correctly refrained from hallucinating.
- **Abstained Spatial Exacts (5):** The spatial cell extractor successfully isolated the correct ground-truth string from the table, but the verification confidence score fell below $T=60.0$ or triggered an ambiguity guard, causing the system to safely abstain rather than claim verification.

Hence:
- **Spatial Extraction Match Rate (SEM):** Measures pure spatial/geometric extraction capability ($75 / 95 = 78.95\%$).
- **Verified Claim Precision (CFP):** Measures precision of claims made by the engine:
  $$\text{CFP} = \frac{\text{Exact Verified Claims}}{\text{Total Verified Claims}} = \frac{67}{70} = 95.71\%$$
- **False Verification Rate (FVR):**
  $$\text{FVR} = \frac{\text{False Verified Claims}}{\text{Total Verified Claims}} = \frac{3}{70} = 4.29\%$$
- **Verified Exact Yield (Overall Accuracy):**
  $$\text{Exact Yield} = \frac{\text{Exact Verified Claims}}{\text{Total Document Fields}} = \frac{67}{95} = 70.53\%$$
- **Coverage:**
  $$\text{Coverage} = \frac{\text{Total Verified Claims}}{\text{Total Document Fields}} = \frac{70}{95} = 73.68\%$$
- **Abstention Rate:**
  $$\text{Abstention Rate} = \frac{\text{Abstained Fields}}{\text{Total Document Fields}} = \frac{25}{95} = 26.32\%$$

---

## 2. Authoritative Loop 22 Benchmark Ledger

The table below is generated directly by parsing `research/loop22/results/benchmark_results.json` without manual transcription. This represents the immutable baseline for Loop 23.

| Cohort | Documents | Total Fields | Verified Claims | Exact Matches | False Verifications | Abstentions | SEM Passes | Precision | Coverage |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A: Development** | 8 | 16 | 15 | 15 | 0 | 1 | 16 | 100.00% | 93.75% |
| **B: Validation** | 8 | 16 | 14 | 14 | 0 | 2 | 15 | 100.00% | 87.50% |
| **C: Blind Evaluation** | 10 | 20 | 14 | 14 | 0 | 6 | 15 | 100.00% | 70.00% |
| **D: Challenge Adversarial** | 8 | 13 | 9 | 9 | 0 | 4 | 11 | 100.00% | 69.23% |
| **E: Hierarchical Headers** | 3 | 6 | 5 | 5 | 0 | 1 | 6 | 100.00% | 83.33% |
| **F: Decimal Integrity** | 3 | 12 | 9 | 6 | 3 | 3 | 6 | 66.67% | 75.00% |
| **G: Evidence Association** | 6 | 12 | 4 | 4 | 0 | 8 | 6 | 100.00% | 33.33% |
| **TOTAL** | **46** | **95** | **70** | **67** | **3** | **25** | **75** | **95.71%** | **73.68%** |

---

## 3. The 3 False Verifications in Cohort F

The authoritative ledger isolates exactly 3 false verifications across the entire 95-field suite, all located within Cohort F (Decimal Integrity):

1. **`DEC_01` — `serum_albumin`:**
   - Expected: `4.2`
   - Extracted/Claimed: `42`
   - Confidence: `84.0`
   - Root Cause: Sub-10px numeric height raster binarization loss; 1px decimal dot fused/eroded into background during global binarization.
2. **`DEC_01` — `blood_urea`:**
   - Expected: `24`
   - Extracted/Claimed: `28`
   - Confidence: `82.0`
   - Root Cause: Sub-10px numeric height distortion; open loop of digit '4' merged with vertical bar under low resolution, recognized as '8'.
3. **`DEC_02` — `chana_opening`:**
   - Expected: `68.5`
   - Extracted/Claimed: `685`
   - Confidence: `85.0`
   - Root Cause: Sub-10px font height rasterization loss; decimal dot eroded between closely spaced glyphs.

---

## 4. Policy for Loop 23 Benchmark Accounting

To maintain absolute accounting integrity in Loop 23:
1. **Automated Markdown Generation:** The benchmark runner script `research/loop23/benchmark/run_loop23_benchmark.py` will directly emit the markdown summary table and json ledger synchronously, preventing any manual transcription discrepancies.
2. **Disjoint Metric Taxonomy:** Every field evaluation must resolve to exactly one state in the verification partition:
   $$\text{Total Fields} = \text{Verified Exact} + \text{Verified False} + \text{Abstained}$$
   SEM and Yield are derived secondary metrics explicitly labeled with their mathematical denominators.
