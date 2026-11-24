# DOCUREADY LOOP 27 — IMMUTABLE FORENSIC INVENTORY
## Comprehensive Root-Cause Reproduction & Taxonomy of Loop 26 False Verifications

**Loop:** 27  
**Branch:** `loop-27-identifier-integrity-and-verification-safety`  
**Base Commit:** `9509017bc3860ac4f7e17a4087e27b574a21062b`  
**Total Target Cases:** 10  
**Status:** 100% REPRODUCED & INVESTIGATED  

---

### 1. Executive Summary

In Loop 26, the independent evaluation of Cohort K revealed 10 false verifications among 113 verified claims (91.15% precision, 8.85% false verification rate). An exhaustive forensic reproduction establishes that:

1. **8 of 10 cases (80.0%)** were single-character OCR substitutions in Indian Financial System Codes (IFSC). Specifically, Tesseract OCR recognized the digit `0` as the capital letter `O` at character index 4 (`BARBOBHUBAN` instead of `BARB0BHUBAN`, and `SBINO001234` instead of `SBIN0001234`).
2. **2 of 10 cases (20.0%)** were receipt date values (`COHORT_K_BLIND_37_SROIE` and `COHORT_K_BLIND_39_SROIE`) where physical receipt text printed `2028` with a trailing comma (`10/10/2028,`), conflicting with the historical 2026 ground truth label.
3. In all 10 cases, the unconstrained verification policy verified the claims because raw OCR confidence exceeded the T*=70.0 threshold without structural syntax or visual glyph ambiguity gating.

---

### 2. Itemized Case Inventory

| Case ID | Document ID | Field Name | Expected | Extracted | Conf | Error Mechanism | Glyph Pair | Root Cause |
|---|---|---|---|---|---|---|---|---|
| `CASE_01` | `COHORT_K_DEV_01_FUNSD` | `State Bank IFSC` | `BARB0BHUBAN` | `BARBOBHUBAN` | 93.0% | Character-level OCR Substitution (O vs 0) | `O vs 0` | IFSC syntax requires 5th char to be 0 (^[A-Z]{4}0[A-Z0-9]{6}... |
| `CASE_02` | `COHORT_K_DEV_02_FUNSD` | `State Bank IFSC` | `BARB0BHUBAN` | `BARBOBHUBAN` | 93.0% | Character-level OCR Substitution (O vs 0) | `O vs 0` | IFSC syntax requires 5th char to be 0 (^[A-Z]{4}0[A-Z0-9]{6}... |
| `CASE_03` | `COHORT_K_DEV_03_FUNSD` | `Bank IFSC Branch Code` | `SBIN0001234` | `SBINO001234` | 71.0% | Character-level OCR Substitution (O vs 0) | `O vs 0` | IFSC syntax requires 5th char to be 0 (^[A-Z]{4}0[A-Z0-9]{6}... |
| `CASE_04` | `COHORT_K_DEV_04_FUNSD` | `State Bank IFSC` | `BARB0BHUBAN` | `BARBOBHUBAN` | 93.0% | Character-level OCR Substitution (O vs 0) | `O vs 0` | IFSC syntax requires 5th char to be 0 (^[A-Z]{4}0[A-Z0-9]{6}... |
| `CASE_05` | `COHORT_K_CAL_17_FUNSD` | `State Bank IFSC` | `BARB0BHUBAN` | `BARBOBHUBAN` | 93.0% | Character-level OCR Substitution (O vs 0) | `O vs 0` | IFSC syntax requires 5th char to be 0 (^[A-Z]{4}0[A-Z0-9]{6}... |
| `CASE_06` | `COHORT_K_CAL_18_FUNSD` | `State Bank IFSC` | `BARB0BHUBAN` | `BARBOBHUBAN` | 93.0% | Character-level OCR Substitution (O vs 0) | `O vs 0` | IFSC syntax requires 5th char to be 0 (^[A-Z]{4}0[A-Z0-9]{6}... |
| `CASE_07` | `COHORT_K_BLIND_32_FUNSD` | `State Bank IFSC` | `BARB0BHUBAN` | `BARBOBHUBAN` | 93.0% | Character-level OCR Substitution (O vs 0) | `O vs 0` | IFSC syntax requires 5th char to be 0 (^[A-Z]{4}0[A-Z0-9]{6}... |
| `CASE_08` | `COHORT_K_BLIND_37_SROIE` | `date` | `10/10/2026` | `10/10/2028,` | 89.5% | Glyph Confusion + Punctuation Bleed (6 vs 8) | `6 vs 8 + trailing comma` | OCR glyph confusion substituted 6 with 8 in year token, and ... |
| `CASE_09` | `COHORT_K_BLIND_39_SROIE` | `date` | `12/12/2026` | `12/12/2028,` | 73.0% | Glyph Confusion + Punctuation Bleed (6 vs 8) | `6 vs 8 + trailing comma` | OCR glyph confusion substituted 6 with 8 in year token, and ... |
| `CASE_10` | `COHORT_K_CHALL_53_FUNSD` | `State Bank IFSC` | `BARB0BHUBAN` | `BARBOBHUBAN` | 93.0% | Character-level OCR Substitution (O vs 0) | `O vs 0` | IFSC syntax requires 5th char to be 0 (^[A-Z]{4}0[A-Z0-9]{6}... |

---

### 3. Structural Root Cause Analysis

#### 3.1 The IFSC 5th Character Invariant
Under the Reserve Bank of India (RBI) structural specification:
$$\text{IFSC} = [A-Z]{4}0[A-Z0-9]{6}$$
The 5th character is **strictly and invariant digit `0` (zero)**, reserved for future use. A candidate containing `[A-Z]{4}O[A-Z0-9]{6}` is structurally invalid. Because sans-serif fonts render `O` and `0` identically or with minimal stroke contrast, high raw OCR confidence (>90%) provides zero protection against this visual glyph substitution.

#### 3.2 Trailing Punctuation Bleed
In receipt layouts, bounding boxes around dates frequently capture adjacent commas or colons. Without syntactic token sanitization, the trailing punctuation is included in the verified string, corrupting verification.
