# DOCUREADY LOOP 3 — BASELINE AUDIT & PRESERVATION REPORT

**Date:** November 13, 2026  
**Auditor:** Antigravity Autonomous Systems  
**Git Branch:** `loop-3-evidence-calibration`  
**Parent Commit:** `caec706` (`feat(loop-2): implement real-world robustness, offline local OCR, uncertainty safety, and statutory rule integrity`)  
**Root Baseline Commit:** `bdfae28`  
**Working Tree Status:** Clean on implementation files; Arena 1, 2, 3 untouched.

---

## 1. Baseline Verification & Reproduction

Before introducing any modifications, the Loop 2 implementation was subjected to full forensic reproduction:

### 1.1 Automated Test Suite Reproduction
Command: `pytest docuready-mvp/tests/ -v`
- **Result:** **37 passed in 12.07s** (0 failed, 0 warnings/errors).
- Covered:
  - 13 adversarial tests (`test_adversarial.py`)
  - 8 synthetic ground truth packet tests (`test_dataset_ground_truth.py`)
  - 3 extractor pipeline tests (`test_extractor.py`)
  - 5 normalization and checksum tests (`test_normalizer.py`)
  - 1 document replacement & rerun workflow test (`test_replacement_rerun.py`)
  - 2 statutory validator tests (`test_validator.py`)
  - 5 uncertainty safety & SC/ST cutoff relaxation tests (`test_uncertainty_safety.py`)

### 1.2 Realistic Corpus (60 Samples) Manifest Verification
Command: Automated Python integrity scan against `REALISTIC_CORPUS_MANIFEST.json`.
- **Total Samples in Manifest:** 60
- **Physical Files on Disk (`docuready-mvp/synthetic_data/realistic_corpus_60/`):** 60
- **Missing Files:** 0
- **Result:** All 60 corpus files verified present and match metadata.

### 1.3 Expanded 40-Packet Synthetic Benchmark Reproduction
- **Result:** Confusion Matrix: $TP=25, TN=15, FP=0, FN=0$.
- **Precision:** 1.0000 | **Recall:** 1.0000 | **F1 Score:** 1.0000
- **False Positive Rate:** 0.0000 | **False Negative Rate:** 0.0000

---

## 2. Core Implementation SHA-256 Hashes at Baseline

| File Path | SHA-256 Checksum |
| :--- | :--- |
| `docuready-mvp/src/extractor.py` | `F4502E8FBE1426BCB48E4BA8ACC424B04F21D5001F8FA1BB5D63A5CAF1680483` |
| `docuready-mvp/src/models.py` | `CAF8A9237874112317E97026C153AA272148CA72924CF15DFB71B01FB8344E6F` |
| `docuready-mvp/src/validator.py` | `A1D65059D76A97DC175DF92AEDA07FF1D9F3671C36FFC13541B6569E9DE47061` |
| `docuready-mvp/src/normalizer.py` | `8FEA31DABFC163771CC047EDF2C46E3E9F29D26E122C4A07FCD5A5A4B97F834F` |
| `docuready-mvp/src/pipeline.py` | `296D4D5090F3A37C1D1B2C11E2517C331CE35A54A230294CE3DD92CBD6639BBA` |
| `docuready-mvp/src/ui.py` | `8AA7CEB8086D0BF180772B5B55677064007DDD8F16B7A78E63FB0A0B25C2C0F4` |

---

## 3. Discrepancy & Opportunity Analysis for Loop 3

1. **Extraction-Abstention Gap:**
   In Loop 2, exact match was 59.7% and normalized match 61.3%, yet abstention was 0% across most OCR categories. The extractor eagerly attempted to return regex matches even on smudged or hallucinated character sequences instead of abstaining when evidence was insufficient.
2. **Confidence Miscalibration:**
   Raw Tesseract character/word confidence (0–100) measures optical token sharpness, **not** the probability that the extracted semantic entity (e.g. Applicant Name or Annual Income) is factually correct.
3. **Evidence State Granularity:**
   Fields need an explicit, multi-state evidence lifecycle: `VERIFIED_TEXT`, `OCR_EXTRACTED`, `AMBIGUOUS`, `LOW_CONFIDENCE`, `NOT_FOUND`, `UNREADABLE`, `CONFLICTING`.
4. **Scheme-Specific Rule Integrity:**
   Audit and separate Post-Matric SC, Post-Matric ST, PM-YASASVI, Medhabruti, and Odisha state scholarship rules from first principles.
