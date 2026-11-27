# DOCUREADY — LOOP 47 FINAL REPORT
## Independent Mixed-Script Generalization, False-Positive Calibration & Upper-Probe Performance Audit

**Branch:** `loop-47-independent-mixed-script-generalization`  
**Base Commit:** `a9d9b7f` (Loop 46)  
**Protected Release:** `bdc403a` (Loop 10 — unmodified, unpromoted)

---

## 1. Executive Summary

1. **Release Freeze Verified (`5 / 5` SHA-256 Exact Match)**: All five Loop 10 artifacts match `docs/04-VALIDATION/LOOP_10_FEATURE_FREEZE_RECORD.md` byte-for-byte (`LOOP_47_FREEZE_HASH_AUDIT.md`).
2. **Strategy C Evaluated Unchanged (`LOOP_47_STRATEGY_C_BASELINE.md`, `LOOP_47_ROUTING_GENERALIZATION.md`)**:
   - **Real/Corpus (`22` docs)**: `5/5` CAL + `12/12` L18 BLIND routed accurately; `5/5` `doclaynet_001..005` triggered `probe_uncertain=True` conservative fallback (`GLOBAL_MULTILINGUAL`).
   - **Synthetic Positive (`10/11` PASS)**: All 8 Loop 45/46 positive cases + `SYN47_SHALLOW_DEV_HDR` + `SYN47_INDIC_HDR_LAT_BODY_INDIC_TBL` passed; `SYN47_SHALLOW_ORI_HDR` (`10%` height compressed Odia header) missed (`FAST_PATH_ENG`), exposing Odia's stricter glyph-height floor.
   - **Expanded Negative Controls (`14/14` PASS)**: `0%` false-positive multilingual routing across `12` synthetic + `2` real/corpus negative controls (including signatures, shirorekha-like decorative marks, English tables, blur scans, sparse upper text, seals, crests, and noise).
3. **Upper-Band Overhead & Paired Performance (`LOOP_47_PROBE_PERFORMANCE.md`, `LOOP_47_E2E_PERFORMANCE.md`)**:
   - Blank upper bands skip OCR in `5.22 ms` (`full_profile = 453.97 ms`); inked English headers add `295.81 ms` (`full_profile = 830.00 ms`).
   - Warm `profile_document()` (`n=30`): L17 mean `817.17 ms` (`< 850 ms` PASS), L18 mean `323.34 ms` (`< 1400 ms` PASS). Loop 46 cold L17 profile mean (`996.48 ms`) is preserved in the comparison.
   - Warm `execute_adaptive_ocr()` (`n=30`, separate scope): L17 mean `1326.98 ms`, L18 mean `3100.91 ms`.
4. **Evidence Integrity & Disjoint Tests (`LOOP_47_EVIDENCE_INTEGRITY.md`, `LOOP_47_TEST_REPORT.md`)**:
   - `SYN_ORI_HDR_LAT_BODY` mapped `36` upper words + `56` body words into their exact original-page regions with `0` OOB.
   - **319 / 319 disjoint tests passing**: `294 / 294` Python (`308.78 s`) + `25 / 25` Electron desktop (`32.90 s`), `0` skipped, `0` failed.
5. **26-Gate Matrix (A–Z)**: **22 PASS**, **2 PARTIAL** (Gate O: `SYN47_SHALLOW_ORI_HDR` boundary; Gate P: Package A/B), **2 BLOCKED** (Gates W, X: Windows signing & clean-VM SmartScreen), **0 FAIL**.
