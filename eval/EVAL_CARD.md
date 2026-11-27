# DocuReady Evaluation Card (`eval/EVAL_CARD.md`)

**Data Label:** `synthetic` (All metrics below are measured exclusively on synthetic documents; real-world accuracy is unmeasured pending T4.4)
**Owner:** Susmita — Domain Rules, Evidence & Evaluation Lead
**Harness:** `eval/harness.py` (T4.1) & `eval/generators/generator_v2.py` (T4.3)
**Target Pack:** `odisha.subhadra` (`as_of=2024-07-01`)

---

## 1. Dataset Splits & Leakage Controls

| Split | Seed | Sample Count | Layouts Permitted | Purpose |
|---|---:|---:|---|---|
| `dev` | `101` | 24 | `L1_STANDARD_PORTRAIT`, `L2_COMPACT_GRID` | Rule & feature development |
| `calib` | `202` | 32 | `L1_STANDARD_PORTRAIT`, `L2_COMPACT_GRID` | Exclusive fit of 9-feature logistic calibrator |
| `test` | `303` | 48 | `L3_BILINGUAL_HEADER`, `L4_TWO_COLUMN_SEAL`, `L5_BOXED_DECLARATION` | Held-out evaluation (layouts strictly unseen in `dev`/`calib`) |

`check_split_leakage()` verifies zero overlap in `layout_id`, `packet_id`, and `document_sha256` (96 unique PDFs across 48 `test` packets; `test_dataset_sha256`: `cd29f3507d26c56249491bfc7c9eaee8e5c91c04608a9632983b9312bd51ccfd`). Persistent packet-level audit artifact: [`eval/reports/t4_1_packet_audit.json`](reports/t4_1_packet_audit.json). Test labels never influence fitted calibrator parameters or thresholds.

---

## 2. Headline Metrics, Raw Counts & Uncertainty (Synthetic `test` Split, n = 48)

> **Methodological Note (CI Correction):** An earlier draft reported `[0.0000, 0.0000]` bootstrap CIs for zero observed false passes and false fails. Because naive bootstrap collapses to `[0, 0]` when $k = 0$, binomial rates now use the **95% Wilson score confidence interval** with exact denominators ($n_{\text{def}} = 24$, $n_{\text{clean}} = 24$). **Zero observed errors in $n = 24$ synthetic packets only bounds the rate below `0.1380` at 95% confidence and does NOT establish zero real-world risk.**

| Metric | Observed Rate | Raw Count / Denominator | 95% Confidence Interval (Method) |
|---|---:|---|---|
| **1. Packet-Level False-Pass Rate (Overall)** | `0.0000` | `0 / 24` defective packets | `[0.0000, 0.1380]` (Wilson score 95%) |
| **1a. Conditional False-Pass Rate (Decisive Defective)** | `0.0000` | `0 / 2` decisive defective packets | `[0.0000, 0.6576]` (Wilson score 95%) |
| **2. Packet-Level False-Fail Rate (Overall)** | `0.0000` | `0 / 24` clean packets | `[0.0000, 0.1380]` (Wilson score 95%) |
| **2a. Conditional False-Fail Rate (Decisive Clean)** | `0.0000` | `0 / 4` decisive clean packets | `[0.0000, 0.4899]` (Wilson score 95%) |
| **3. Abstention Rate** | `0.8750` | `42 / 48` packets (`NEEDS_CHECKS`) | — |
| **4. Overall Decision Coverage** | `0.1250` | `6 / 48` packets (`4` PASS + `2` FAIL) | — |
| **4a. Clean-Packet Decision Coverage** | `0.1667` | `4 / 24` clean packets (`PASS`) | — |
| **4b. Defective-Packet Decision Coverage** | `0.0833` | `2 / 24` defective packets (`FAIL`) | — |
| **5. Per-Field Extraction Accuracy** | `0.5000` | `24 / 48` (`applicant_name`, `dob`, `passbook_name`) | — |
| **6. 10-Bin ECE** | `0.2177` | `n = 48` calibrated predictions | `[0.1896, 0.2475]` (Bootstrap 500, seeded) |

### Explicit Coverage & Abstention Definitions
- **Overall Decision Coverage:** $(\text{Decisive PASS} + \text{Decisive FAIL}) / N_{\text{test}} = (4 + 2) / 48 = 0.1250$. Abstentions (`NEEDS_CHECKS`) are **not** counted as successful decisions.
- **Clean-Packet Decision Coverage:** Clean packets receiving a decisive outcome (`4 / 24 = 0.1667`).
- **Defective-Packet Decision Coverage:** Defective packets receiving a decisive outcome (`2 / 24 = 0.0833`).
- **Why Conditional Wilson Intervals Are Wide:** Only `2` defective packets and `4` clean packets received decisive evaluations (`PASS`/`FAIL`), so conditional 95% Wilson intervals (`[0.0000, 0.6576]` and `[0.0000, 0.4899]`) reflect genuine small-denominator uncertainty.

---

## 3. Why Abstention Is 87.5% (Evidence-State & Perturbation Breakdown)

Under Architecture V2 §6 (`resolve_outcome()`), only `EvidenceState.VERIFIED` ($P \ge 0.85$ or `NATIVE_VECTOR`) can emit `PASS` or `FAIL`.

| Packet Evidence State | n | Mean Calibrated Prob | Abstention Count | Abstention Rate | Explanation |
|---|---:|---:|---:|---:|---|
| `VERIFIED` | 6 | `0.9740` | 0 | `0.0000` | All 6 `unperturbed` (`NATIVE_VECTOR`) packets (4 ground-truth clean $\to$ `PASS`, 2 ground-truth defective $\to$ `FAIL`) resolve decisively. |
| `PROVISIONAL` | 12 | `0.7950` | 12 | `1.0000` | `bilingual_indic` & `rotation` OCR packets score `< 0.85`, so `resolve_outcome()` downgrades to `NEEDS_CHECKS`. |
| `UNCERTAIN` | 30 | `0.2868` | 30 | `1.0000` | `blur`, `jpeg_low_quality`, `low_contrast`, `low_dpi`, and `overlapping_stamp` packets fail closed to `REVIEW`. |

---

## 4. 10-Bin Reliability Table (`test` Split, n = 48)

| Bin | Range | Count | Avg Confidence | Empirical Accuracy |
|---:|---|---:|---:|---:|
| 0 | `[0.0, 0.1)` | 0 | 0.0000 | 0.0000 |
| 1 | `[0.1, 0.2)` | 6 | 0.1420 | 0.0000 |
| 2 | `[0.2, 0.3)` | 18 | 0.2427 | 0.0000 |
| 3 | `[0.3, 0.4)` | 0 | 0.0000 | 0.0000 |
| 4 | `[0.4, 0.5)` | 0 | 0.0000 | 0.0000 |
| 5 | `[0.5, 0.6)` | 6 | 0.5640 | 1.0000 |
| 6 | `[0.6, 0.7)` | 0 | 0.0000 | 0.0000 |
| 7 | `[0.7, 0.8)` | 12 | 0.7950 | 1.0000 |
| 8 | `[0.8, 0.9)` | 0 | 0.0000 | 0.0000 |
| 9 | `[0.9, 1.0]` | 6 | 0.9740 | 1.0000 |

---

## 5. Perturbation Matrix & Negative Controls (`test` Split)

| Perturbation | n | False-Pass Rate | False-Fail Rate | Abstention Rate | Field Accuracy |
|---|---:|---:|---:|---:|---:|
| `unperturbed` | 6 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| `bilingual_indic` | 6 | 0.0000 | 0.0000 | 1.0000 | 1.0000 |
| `overlapping_stamp` | 6 | 0.0000 | 0.0000 | 1.0000 | 1.0000 |
| `rotation` | 6 | 0.0000 | 0.0000 | 1.0000 | 1.0000 |
| `blur` | 6 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| `jpeg_low_quality` | 6 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| `low_contrast` | 6 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| `low_dpi` | 6 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |

### Cross-Tabulation: Ground Truth $\times$ Perturbation $\times$ Final Outcome (`n = 48`)

| Ground Truth | Perturbation | `PASS` | `FAIL` | `REVIEW` | Total |
|---|---|---:|---:|---:|---:|
| `clean` | `unperturbed` | 4 | 0 | 0 | 4 |
| `clean` | `bilingual_indic` / `rotation` / `overlapping_stamp` / `blur` / `jpeg_low_quality` / `low_contrast` / `low_dpi` | 0 | 0 | 20 | 20 |
| `defective` | `unperturbed` | 0 | 2 | 0 | 2 |
| `defective` | `bilingual_indic` / `rotation` / `overlapping_stamp` / `blur` / `jpeg_low_quality` / `low_contrast` / `low_dpi` | 0 | 0 | 22 | 22 |
| **Total** | **All 8 Perturbations** | **4** | **2** | **42** | **48** |

### Negative Controls (`test` Split Subset: `8 / 48` Packets)
> **Population Note:** These 8 negative-control packets are a **strict subset of the 48 primary `test` packets** (not an additional test set) and overlap with perturbation categories (`low_contrast`, `jpeg_low_quality`, `rotation`, `bilingual_indic`). All 8 are ground-truth `defective` and are included in `n_defective = 24`. **All `8 / 8` negative-control packets abstained (`0 / 8` decisive coverage); zero false passes in a completely abstained category is NOT proof that the underlying condition was detected.**

| Negative Control | n | Decisive Coverage | Abstention Rate | False-Pass Rate |
|---|---:|---:|---:|---:|
| `common_name_collision` | 2 | 0.0000 (`0/2`) | 1.0000 (`2/2`) | 0.0000 |
| `near_identical_numbers` | 2 | 0.0000 (`0/2`) | 1.0000 (`2/2`) | 0.0000 |
| `same_name_different_person` | 2 | 0.0000 (`0/2`) | 1.0000 (`2/2`) | 0.0000 |
| `wrong_doc_in_slot` | 2 | 0.0000 (`0/2`) | 1.0000 (`2/2`) | 0.0000 |

---

## 6. Nine-Feature Calibration Input Provenance

| # | Feature (`features.py`) | Normalization | Production Extractor (`extractor.py`) | Synthetic Eval (`harness.py`) |
|---|---|---|---|---|
| 1 | `ocr_token_confidence` | Clamped `[0, 1]` (`0.50` if `None`; `1.0` if native) | Supplied from Tesseract | Simulated per perturbation |
| 2 | `supporting_token_count` | `min(1.0, count / 3.0)` (`0.25` for 1-token name) | Supplied from `len(val.split())` | Simulated (`2`) |
| 3 | `anchor_label_proximity` | `1.0` ($\le 25$pt) $\to$ `0.30` ($>150$pt), `0.20` if undetected | Supplied from `label_distance_pt` | Simulated (`12.0`pt) |
| 4 | `label_match_confidence` | Clamped `[0, 1]` | **DEFAULTED** (`1.0` if `label_detected` else `0.20`) | Simulated per perturbation |
| 5 | `format_validation` | `1.0` if syntax valid else `0.0` | Supplied from `validate_field_syntax()` | Validated (`1.0`) |
| 6 | `candidate_ambiguity` | `min(1.0, max(0, count - 1) / 3.0)` | Supplied from `candidate_count` | Simulated (`1`) |
| 7 | `layout_consistency` | Clamped `[0, 1]` | **DEFAULTED** (`0.90`) | Simulated per perturbation |
| 8 | `extraction_source` | `1.0` (`LOCAL_OCR`) vs `0.0` (`NATIVE_VECTOR`) | Supplied from `ExtractionMethod` | Simulated per perturbation |
| 9 | `rotation_skew` | `min(1.0, abs(rotation_deg) / 15.0)` | **DEFAULTED** (`0.0`; `PageOCRData.rotation_applied` not wired) | Simulated (`8.5` deg on `rotation`) |

**Cross-Owner Dependency:** Full 9-feature production calibration requires Akriti to wire `rotation_deg`, `layout_consistency`, and `label_match_confidence` into `src/docuready/ingest/extractor.py`.

---

## 7. Plain-Language Limitations

- **Synthetic Only:** All documents and OCR feature profiles are synthetic. These numbers demonstrate deterministic safety under controlled degradations, **not** real-world OCR accuracy on photographed citizen documents.
- **Zero Observed Errors $\ne$ Zero Risk:** With $n=24$ defective and $n=24$ clean packets, the 95% Wilson upper bound is `0.1380` (`13.8%`).
- **Real-Sample Prerequisite:** Real-world accuracy claims remain prohibited until real specimen/consented documents are evaluated under [REAL_SAMPLE_PROTOCOL.md](../docs/REAL_SAMPLE_PROTOCOL.md).
