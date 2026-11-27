# DOCUREADY — LOOP 46 QUALIFICATION MATRIX (GATES A–Z)

**Total Gates:** `26` | **PASS:** `23` | **PARTIAL:** `1` (Gate P) | **BLOCKED:** `2` (Gates W, X) | **FAIL:** `0`

| Gate | Requirement | Expected | Observed | Evidence Path | Status |
|---|---|---|---|---|---|
| **A** | Loop 46 branch & `c7ed04f` ancestry | Clean branch from `c7ed04f` | Verified `c7ed04f` & `bdc403a` ancestors | `LOOP_46_BASELINE_AUDIT.md` | **PASS** |
| **B** | Loop 10 frozen artifact hashes (5/5) | Bit-exact match on disk | 5/5 SHA-256 exact match | `LOOP_46_FREEZE_HASH_AUDIT.md` | **PASS** |
| **C** | Reproduce `SYN_*_HDR_LAT_BODY` failure | Confirm lower Latin suppressed upper | Confirmed: `90` Latin in lower skipped `else:` | `LOOP_46_FAILURE_REPRODUCTION.md` | **PASS** |
| **D** | Strategy A–E calibration ablation | Select optimal strategy on CAL | Strategy C selected (`7/7` CAL, `<850 ms`) | `LOOP_46_ROUTING_STRATEGIES.md` | **PASS** |
| **E** | Negative-control false-positive resistance | `0%` false multilingual routing | `9/9` negative controls stayed `FAST_PATH_ENG` | `LOOP_46_FALSE_POSITIVE_AUDIT.md` | **PASS** |
| **F** | Loop 17 warm `profile_document` | `< 850.0 ms` (warm) | Warm mean `713.75 ms`, median `694.11 ms` (Cold `996.48 ms`) | `LOOP_46_PERFORMANCE_REPORT.md` | **PASS** |
| **G** | Loop 18 warm & cold `profile_document` | `< 1400.0 ms` | Warm `299.53 ms`, Cold `648.48 ms` | `LOOP_46_PERFORMANCE_REPORT.md` | **PASS** |
| **H** | Separate E2E `execute_adaptive_ocr` metrics | Cold & warm E2E measured separately | Warm `1244.15 / 2855.47 ms`, Cold `1732.37 / 3787.13 ms` | `LOOP_46_PERFORMANCE_REPORT.md` | **PASS** |
| **I** | Upper-band `500 px` & `>= 6` Indic guard | Preserved for Odia & Devanagari | Preserved in `adaptive_ocr.py` | `LOOP_46_ROUTING_STRATEGIES.md` | **PASS** |
| **J** | Two-column coordinate integrity | `0` out-of-bounds boxes | `CHALLENGE_02_ORI_ENG_2COL` -> `REGION_AWARE_ROUTING` | `LOOP_46_ROUTING_ABLATION.md` | **PASS** |
| **K** | Full-page bounding-box integrity | `0` out-of-bounds boxes | Verified across `294/294` Python + `25/25` Desktop | `LOOP_46_EVIDENCE_INTEGRITY.md` | **PASS** |
| **L** | Table & spatial association regression | `test_loop19` passes | Passed in `294/294` Python suite | `LOOP_46_TEST_REPORT.md` | **PASS** |
| **M** | Native/fallback TSV parity across 6 configs | `100%` word & box parity | `word_box_exact=True` across all 6 configs | `LOOP_46_EVIDENCE_INTEGRITY.md` | **PASS** |
| **N** | Uncertainty & monkeypatch safeguards | Preserved under patched/sparse inputs | `doclaynet_001..005` routed safely via `probe_uncertain` | `LOOP_46_ROUTING_ABLATION.md` | **PASS** |
| **O** | Indic-header + Latin-body recovery | `SYN_DEV_HDR_LAT_BODY` & `SYN_ORI_HDR_LAT_BODY` pass | `8/8` synthetic positive cohort (`100%` recall) | `LOOP_46_ROUTING_ABLATION.md` | **PASS** |
| **P** | Package A/B non-inferiority (`CI <= +1500 ms`) | `CI_high <= +1500.0 ms` | Carried forward `CONDITIONALLY QUALIFIED` | `LOOP_46_LIMITATIONS_AND_RISKS.md` | **PARTIAL** |
| **Q** | Loop 14/18 real/corpus preservation | No regression | `5/5` CAL + `8/8` L18 BLIND pass | `LOOP_46_ROUTING_ABLATION.md` | **PASS** |
| **R** | Offline operation & zero external API | Local DLL + local tessdata only | Verified offline, `0` network calls | `LOOP_46_TEST_REPORT.md` | **PASS** |
| **S** | Desktop IPC, isolation & crash recovery | `25/25` desktop tests pass | `25 / 25` passed in `29.32 s` | `LOOP_46_TEST_REPORT.md` | **PASS** |
| **T** | Full Loop 01–46 Python regression suite | Zero failures post-edit | `294 / 294` passed in `284.36 s` | `LOOP_46_TEST_REPORT.md` | **PASS** |
| **U** | English-only, Hindi-only, Odia-only stability | Zero regression | `DOC_CTRL_01`, `DOC_HIN_01`, `DOC_EXT_06` pass | `LOOP_46_ROUTING_ABLATION.md` | **PASS** |
| **V** | Separate real/corpus vs synthetic reporting | Disjoint cohorts & per-script audit | Reported separately in manifest & accuracy report | `LOOP_46_CORPUS_MANIFEST.md` | **PASS** |
| **W** | Windows Authenticode code signing | Signed EXEs + timestamp | `NotSigned`, `0` certs in store | `LOOP_46_LIMITATIONS_AND_RISKS.md` | **BLOCKED** |
| **X** | Clean-machine Windows VM & SmartScreen | Fresh VM install/upgrade/uninstall | Unavailable in CLI | `LOOP_46_LIMITATIONS_AND_RISKS.md` | **BLOCKED** |
| **Y** | All 16 Loop 46 deliverables complete | 16 reports under `research/loop46/` | All 16 reports created & verified | `research/loop46/` | **PASS** |
| **Z** | Loop 10 immutability preserved | Zero edits/promotion of `bdc403a` | Verified untouched & `5/5` bit-exact | `LOOP_46_FREEZE_HASH_AUDIT.md` | **PASS** |
