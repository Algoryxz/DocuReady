# Loop 23 Micro-Font Numeric Benchmark

## 1. Overview & Evaluation Scope

Micro-font numbers in documents present severe OCR challenges due to pixel discretization effects:
- An 8px to 10px character height offers only ~6-7 rows of stroke information.
- A decimal point at this resolution is rendered as a 1px dot ($1 \times 1$ pixel).
- Standard OCR page-level binarization frequently fuses fine dots with adjacent numerals or erodes them into the white background.

Loop 23 benchmarks micro-font numeric integrity across 9 dedicated test documents comprising Cohort F (Loop 21 Decimal Stress) and Cohort H (Loop 23 Blind Micro-Font & Narrow-Gutter Suite).

---

## 2. Experimental Results on Micro-Font Fixtures

### Cohort F: Decimal Integrity Cohort (3 Documents, 12 Critical Fields)

| Document | Field | Value | Category | Ground Truth | Loop 22 Outcome | Loop 23 Outcome | Latency |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `DEC_01_BIOCHEMISTRY` | `serum_albumin` | `4.2` | Clinical Dec | `4.2` | FAIL (`42`) | **PASS_SPATIAL_EXACT** | 480ms |
| `DEC_01_BIOCHEMISTRY` | `total_bilirubin` | `0.8` | Clinical Dec | `0.8` | ABSTAIN | **ABSTAIN** | 480ms |
| `DEC_01_BIOCHEMISTRY` | `serum_creatinine` | `1.25` | Clinical Dec | `1.25` | PASS (`1.25`) | **PASS_SPATIAL_EXACT** | 480ms |
| `DEC_01_BIOCHEMISTRY` | `blood_urea` | `24` | Small Int | `24` | FAIL (`28`) | **PASS_SPATIAL_EXACT** | 480ms |
| `DEC_02_COMMODITY` | `mustard_settlement`| `56.25` | Market Dec | `56.25` | PASS (`56.25`) | **PASS_SPATIAL_EXACT** | 510ms |
| `DEC_02_COMMODITY` | `chana_opening` | `68.5` | Market Dec | `68.5` | FAIL (`685`) | **PASS_SPATIAL_EXACT** | 510ms |
| `DEC_02_COMMODITY` | `turmeric_settlement`| `138.50`| Market Dec | `138.50`| ABSTAIN | **ABSTAIN** | 510ms |
| `DEC_02_COMMODITY` | `barley_volume` | `3100` | Standard Int | `3100` | PASS (`3100`) | **PASS_SPATIAL_EXACT** | 510ms |
| `DEC_03_PHARMA` | `levo_strength` | `0.25` | Pharma Dec | `0.25` | PASS (`0.25`) | **PASS_SPATIAL_EXACT** | 495ms |
| `DEC_03_PHARMA` | `clonazepam_strength`| `0.5` | Pharma Dec | `0.5` | PASS (`0.5`) | **PASS_SPATIAL_EXACT** | 495ms |
| `DEC_03_PHARMA` | `amlodipine_strength`| `2.5` | Pharma Dec | `2.5` | ABSTAIN | **ABSTAIN** | 495ms |
| `DEC_03_PHARMA` | `metformin_strength` | `500` | Standard Int | `500` | PASS (`500`) | **PASS_SPATIAL_EXACT** | 495ms |

**Summary for Cohort F:**
- Fields: 12
- Verified: 9 (9 Exact, 0 False Verifications)
- Abstentions: 3 (100% safe, no hallucinations)
- Precision: **100.00%** (vs 66.67% in Loop 22)
- FVR: **0.00%** (vs 33.33% in Loop 22)

---

### Cohort H: Micro-Font Subsets (Clinical Panel & Dosage Audit)

| Document | Field | Ground Truth | Status | Confidence | Note |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `COHORT_H_01_CLINICAL` | `hba1c_result` | `5.8` | ABSTAIN | 0.0 | Safe abstention (candidate not isolated) |
| `COHORT_H_01_CLINICAL` | `platelet_count` | `240` | **PASS_SPATIAL_EXACT** | 94.0 | Small integer exact |
| `COHORT_H_01_CLINICAL` | `potassium_result` | `4.1` | **ABSTAIN** | 0.0 | Type contradiction guard rejected '4a' |
| `COHORT_H_01_CLINICAL` | `sodium_result` | `138` | ABSTAIN | 59.0 | Below T=60.0 confidence floor |
| `COHORT_H_02_DOSAGE` | `lora_strength` | `0.75` | ABSTAIN | 0.0 | Borderless alignment safeguard |
| `COHORT_H_02_DOSAGE` | `lora_purity` | `99.2` | ABSTAIN | 0.0 | Borderless alignment safeguard |
| `COHORT_H_02_DOSAGE` | `diaz_strength` | `2.4` | ABSTAIN | 0.0 | Borderless alignment safeguard |
| `COHORT_H_02_DOSAGE` | `omep_strength` | `20` | **PASS_SPATIAL_EXACT** | 76.0 | Small integer exact |

**Key Takeaways:**
1. Zero False Verifications: In all situations where micro-font raster distortion prevented high-confidence extraction (e.g. `'4a'` for `'4.1'`), the system safely abstained rather than claiming false verification.
2. Verified claims achieve 100% precision.
