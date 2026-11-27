# Loop 40 Multilingual OCR Generalization & Accuracy Report

**Date:** 2026-11-27  
**Branch:** `loop-40-performance-multilingual-and-windows-qualification`  
**Target File:** `src/docuready/ingest/adaptive_ocr.py`  
**Data File:** `research/loop40/accuracy_results.json`

---

## 1. Mixed English–Odia Regression Root Cause & Fix

In Loop 39, `DOC_MIX_02_ORI_ENG_SCHOLARSHIP` regressed under `GLOBAL_MULTILINGUAL` (`eng+ori`: CER `9.36%`, WER `21.74%`) compared to Global `eng+hin+ori` (CER `6.35%`, WER `17.39%`).

**Root Cause:** `select_ocr_strategy()` in `src/docuready/ingest/adaptive_ocr.py` routed `has_ori and not has_dev` to `chosen_lang = "eng+ori"`. Controlled Tesseract 5.4.0 LSTM ablation showed:
- `eng+hin+ori`: CER **`6.35%`**, WER **`17.39%`**
- `eng+ori` / `ori+eng` / `ori+eng+hin`: CER `9.36%`, WER `21.74%`

**Fix:** Updated `select_ocr_strategy()` so `GLOBAL_MULTILINGUAL` routes `has_ori` to `chosen_lang = "eng+hin+ori"`, restoring `DOC_MIX_02_ORI_ENG_SCHOLARSHIP` to **CER `6.35%` / WER `17.39%`** (matching Global) while preserving `MONOLINGUAL_ORI` (`ori`) and `FAST_PATH_ENG` (`eng`).

---

## 2. Frozen 35-Document Multilingual Corpus Evaluation

Corpus partitions (deduplicated across Loop 14 + Loop 18 corpora, `N = 35` documents):
- **`DEV` (`n = 10`):** Loop 14 development documents not in Loop 18.
- **`CALIBRATION` (`n = 19`):** Loop 18 `PRIMARY_VALIDATION` split.
- **`BLIND` (`n = 6`):** Loop 18 `SEALED_CHALLENGE` split (`1` abstained: `CHALLENGE_04_LOW_CONTRAST_UNREADABLE_STRESS`).

### 2.1 Overall & Partition Metrics (`accuracy_results.json`)

| Scope | Docs (Abstained) | Adaptive Micro CER | Global Micro CER | Adaptive Micro WER | Global Micro WER | Adaptive Macro CER | Global Macro CER | Mean Adaptive / Global (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Overall** | `35 (1)` | **`19.56%`** | `20.81%` | **`32.43%`** | `33.74%` | **`35.85%`** | `37.54%` | `2024.08` / `2093.49` |
| **DEV** | `10 (0)` | **`16.76%`** | `17.70%` | **`28.81%`** | `29.54%` | **`17.30%`** | `18.54%` | `954.17` / `1097.84` |
| **CALIBRATION** | `19 (0)` | **`20.79%`** | `21.98%` | **`34.51%`** | `35.50%` | **`50.94%`** | `52.39%` | `2823.58` / `2858.83` |
| **BLIND** | `6 (1)` | **`17.16%`** | `19.10%` | **`26.63%`** | `30.34%` | **`15.65%`** | `19.10%` | `1275.50` / `1329.35` |

### 2.2 Per-Language-Bucket Breakdown

| Language Bucket | Docs | Adaptive Micro CER | Global Micro CER | Adaptive Micro WER | Global Micro WER | Mean Adaptive / Global (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `English-only` | `8` | `51.02%` | `50.94%` | `62.81%` | `63.09%` | `1132.39` / `1568.95` |
| `Hindi-only` | `4` | **`19.74%`** | `22.71%` | **`41.24%`** | `44.33%` | `1336.00` / `1729.33` |
| `Odia-only` | `1` | **`3.76%`** | `7.52%` | **`20.00%`** | `25.00%` | `313.42` / `539.60` |
| `Eng+Hin` | `11` | `12.11%` | `9.23%` | `23.07%` | `20.33%` | `2815.51` / `2626.20` |
| `Eng+Ori` | `2` | **`3.69%`** | `3.69%` | **`10.00%`** | `10.00%` | `3087.38` / `2822.81` |
| `Tri-script (Eng+Hin+Ori)` | `8` | **`15.53%`** | `23.36%` | **`31.87%`** | `39.45%` | `2364.78` / `2168.17` |
| `Unreadable/Stress` | `1` | `ABSTAIN` (`100%`) | — | — | — | — |

### 2.3 Key Anchor Documents

| Sample ID | Strategy (`selected_lang`) | Adaptive CER / WER | Global CER / WER |
| :--- | :--- | :---: | :---: |
| `DOC_CTRL_01_ENGLISH_CERTIFICATE` | `FAST_PATH_ENG` (`eng`) | **`0.00%` / `0.00%`** | `0.00%` / `0.00%` |
| `DOC_EXT_06_ODIA_REVENUE_NOTICE` | `GLOBAL_MULTILINGUAL` (`eng+hin+ori`) | **`4.37%` / `12.93%`** | `4.37%` / `12.93%` |
| `DOC_MIX_01_HIN_ENG_SCHOLARSHIP` | `GLOBAL_MULTILINGUAL` (`eng+hin+ori`) | **`8.57%` / `18.87%`** | `8.57%` / `18.87%` |
| `DOC_MIX_02_ORI_ENG_SCHOLARSHIP` | `GLOBAL_MULTILINGUAL` (`eng+hin+ori`) | **`6.35%` / `17.39%`** | `6.35%` / `17.39%` |
| `DOC_ORI_01_ADMIN_CIRCULAR` | `MONOLINGUAL_ORI` (`ori`) | **`8.21%` / `39.66%`** | `8.21%` / `39.66%` |

### 2.4 Critical-Field & Table-Cell Integrity

All critical-field contracts and table-association assertions in `tests/test_loop17_adaptive_efficiency.py`, `tests/test_loop18_accuracy_and_critical_fields.py`, `tests/test_loop19_table_association.py`, and `tests/test_loop20_blind_generalization.py` passed (`0` failures).
