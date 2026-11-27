# DOCUREADY — LOOP 46 FINAL REPORT
## Indic Header + Latin Body Recovery, False-Positive Resistance & Routing Cost Qualification

**Branch:** `loop-46-indic-header-latin-body-recovery`  
**Base Commit:** `c7ed04f` (Loop 45)  
**Protected Release:** `bdc403a` (Loop 10 — unmodified, unpromoted)

---

## 1. Executive Summary

1. **Release Freeze Verified (`5 / 5` SHA-256 Exact Match)**: All five Loop 10 artifacts match `docs/04-VALIDATION/LOOP_10_FEATURE_FREEZE_RECORD.md` byte-for-byte (`LOOP_46_FREEZE_HASH_AUDIT.md`).
2. **Loop 45 Failure Reproduced & Resolved via Strategy C**:
   - Confirmed `SYN_DEV_HDR_LAT_BODY` and `SYN_ORI_HDR_LAT_BODY` failed in Loop 45 because `90` Latin chars in `0.52..0.85` skipped the `else:` upper-band probe.
   - Evaluated Strategies A–E on the frozen `7`-doc CAL cohort; selected **Strategy C** (`7/7` CAL), which probes `0.05..0.22` (`max_dim=500.0`, `>= 6` Indic guard) whenever central+lower still look monolingual `LATIN` and upper-band ink `>= 0.003`.
3. **Positive & Negative-Control Qualification**:
   - **Synthetic Positive Cohort (`8 / 8`, `100%`)**: `SYN_DEV_HDR_LAT_BODY` (`eng+hin`) and `SYN_ORI_HDR_LAT_BODY` (`eng+hin+ori`) now route to `GLOBAL_MULTILINGUAL`, alongside all `SYN_*_HDR_LAT_ID`, `SYN_LAT_HDR_*_BODY`, and `SYN_SHORT_UPPER_*` cases.
   - **Expanded Negative Controls (`9 / 9`, `0%` FP)**: Zero false multilingual triggers across circular seals, decorative crests, 1.5% noise, diagonal marks, blank upper + dense Latin, ambiguous typography, official stamps/watermarks, `CHALLENGE_06_FAINT_SEAL`, and `STRESS_02_STAMP`.
   - **Real/Corpus Cohort (`18` docs)**: `5/5` CAL + `8/8` L18 BLIND passed; `5/5` DocLayNet routed safely via `probe_uncertain=True`.
4. **Performance & Overhead (`n=30` Paired Warm + `n=5` Cold)**:
   - **L17 (`DOC_CTRL_01`)**: Warm `profile_document()` mean `713.75 ms` (`< 850 ms` PASS; `+246.23 ms` upper-band overhead vs Loop 45 when upper band has ink; `< 1 ms` when blank); Cold `996.48 ms`; Warm E2E `1244.15 ms`; Cold E2E `1732.37 ms`.
   - **L18 (`DOC_EXT_06`)**: Warm `profile_document()` mean `299.53 ms` (`< 1400 ms` PASS); Cold `648.48 ms`; Warm E2E `2855.47 ms`; Cold E2E `3787.13 ms`.
5. **Evidence Integrity & Disjoint Tests**:
   - `word_box_exact=True` across all 6 language configs (`eng`, `hin`, `ori`, `eng+hin`, `eng+ori`, `eng+hin+ori`).
   - **319 / 319 disjoint tests passing**: `294 / 294` Python (`284.36 s`) + `25 / 25` Electron desktop (`29.32 s`).
6. **26-Gate Matrix (A–Z)**: **23 PASS** (Gate O upgraded to PASS), **1 PARTIAL** (Gate P: Package A/B), **2 BLOCKED** (Gates W, X: Windows signing & clean-VM SmartScreen), **0 FAIL**.
