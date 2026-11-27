# DOCUREADY — LOOP 45 QUALIFICATION MATRIX (GATES A–Z)

**Total Gates:** `26` | **PASS:** `22` | **PARTIAL:** `2` (Gates O, P) | **BLOCKED:** `2` (Gates W, X) | **FAIL:** `0`

| Gate | Requirement | Expected | Observed | Evidence Path | Status |
|---|---|---|---|---|---|
| **A** | Loop 45 branch & `02baae0` ancestry | Clean branch from `02baae0` | Verified `02baae0` & `bdc403a` ancestors | `LOOP_45_BASELINE_AUDIT.md` | **PASS** |
| **B** | Loop 10 frozen artifact hashes (5/5) | Bit-exact match on disk | 5/5 SHA-256 exact match | `LOOP_45_FREEZE_HASH_AUDIT.md` | **PASS** |
| **C** | Benchmark boundary anomaly root cause | Explain L44 `495.17` vs `368.85` ms | Sequential `n=30` vs `n=5` cache/thermal mismatch | `LOOP_45_BENCHMARK_BOUNDARY_AUDIT.md` | **PASS** |
| **D** | Paired stage-timing model | Additive `profile + Stage 3/4 = E2E` | `465.18 + 498.02 = 963.20 ms` (L17 `n=30`) | `LOOP_45_BENCHMARK_BOUNDARY_AUDIT.md` | **PASS** |
| **E** | Negative-control false-positive resistance | `0%` false multilingual triggers | `6/6` negative controls stayed `FAST_PATH_ENG` | `LOOP_45_FALSE_POSITIVE_AUDIT.md` | **PASS** |
| **F** | Loop 17 warm & cold `profile_document` | `< 850.0 ms` | Warm `467.52 ms`, Cold `540.12 ms` (`n=30`/`n=5`) | `LOOP_45_E2E_PERFORMANCE.md` | **PASS** |
| **G** | Loop 18 warm & cold `profile_document` | `< 1400.0 ms` | Warm `317.89 ms`, Cold `762.01 ms` (`n=30`/`n=5`) | `LOOP_45_E2E_PERFORMANCE.md` | **PASS** |
| **H** | Separate E2E `execute_adaptive_ocr` metrics | Cold & warm E2E measured separately | Warm `963.20 / 2955.40 ms`, Cold `1844.16 / 3853.46 ms` | `LOOP_45_E2E_PERFORMANCE.md` | **PASS** |
| **I** | Probe-resolution & threshold audit | Devanagari vs Odia tested independently | Odia `350px` (`5` chars) vs `500px` (`25` chars) | `LOOP_45_THRESHOLD_ABLATION.md` | **PASS** |
| **J** | Two-column coordinate integrity | `0` out-of-bounds boxes | `CHALLENGE_02_ORI_ENG_2COL`: `64` boxes, `0` OOB | `LOOP_45_EVIDENCE_INTEGRITY.md` | **PASS** |
| **K** | Full-page bounding-box integrity | `0` out-of-bounds boxes | `0` OOB across `DOC_CTRL_01`, `DOC_EXT_06`, `SYN_ORI_HDR_LAT_ID` | `LOOP_45_EVIDENCE_INTEGRITY.md` | **PASS** |
| **L** | Table & spatial association regression | `test_loop19` passes | Passed in `289/289` Python suite | `LOOP_45_TEST_REPORT.md` | **PASS** |
| **M** | Native/fallback TSV parity across 6 configs | `100%` word & box parity | Passed in `test_loop42` within `289/289` | `LOOP_45_EVIDENCE_INTEGRITY.md` | **PASS** |
| **N** | Uncertainty & monkeypatch safeguards | Preserved under patched/sparse inputs | `doclaynet_001..005` routed safely via `probe_uncertain` | `LOOP_45_ROUTING_GENERALIZATION.md` | **PASS** |
| **O** | Independent upper-band generalization | All upper-band layouts recover Indic | `SYN_*_HDR_LAT_ID` pass; `SYN_*_HDR_LAT_BODY` miss (non-blank lower) | `LOOP_45_ROUTING_GENERALIZATION.md` | **PARTIAL** |
| **P** | Package A/B non-inferiority (`CI <= +1500 ms`) | `CI_high <= +1500.0 ms` | Carried forward `CONDITIONALLY QUALIFIED` | `LOOP_45_LIMITATIONS_AND_RISKS.md` | **PARTIAL** |
| **Q** | Loop 14/18 real/corpus preservation | No regression | `5/5` CAL + `8/8` L18 BLIND pass | `LOOP_45_ROUTING_GENERALIZATION.md` | **PASS** |
| **R** | Offline operation & zero external API | Local DLL + local tessdata only | Verified offline, `0` network calls | `LOOP_45_TEST_REPORT.md` | **PASS** |
| **S** | Desktop IPC, isolation & crash recovery | `25/25` desktop tests pass | `25 / 25` passed in `35.16 s` | `LOOP_45_TEST_REPORT.md` | **PASS** |
| **T** | Full Loop 01–44 Python regression suite | Zero failures | `289 / 289` passed in `338.20 s` | `LOOP_45_TEST_REPORT.md` | **PASS** |
| **U** | English-only, Hindi-only, Odia-only stability | Zero regression | `DOC_CTRL_01`, `DOC_HIN_01`, `DOC_EXT_06` pass | `LOOP_45_ROUTING_GENERALIZATION.md` | **PASS** |
| **V** | Separate real/corpus vs synthetic reporting | Disjoint cohorts & per-script audit | Reported separately in manifest & ablation | `LOOP_45_CORPUS_MANIFEST.md` | **PASS** |
| **W** | Windows Authenticode code signing | Signed EXEs + timestamp | `NotSigned`, `0` certs in store | `LOOP_45_LIMITATIONS_AND_RISKS.md` | **BLOCKED** |
| **X** | Clean-machine Windows VM & SmartScreen | Fresh VM install/upgrade/uninstall | Unavailable in CLI | `LOOP_45_LIMITATIONS_AND_RISKS.md` | **BLOCKED** |
| **Y** | All 15 Loop 45 deliverables complete | 15 reports under `research/loop45/` | All 15 reports created & verified | `research/loop45/` | **PASS** |
| **Z** | Loop 10 immutability preserved | Zero edits/promotion of `bdc403a` | Verified untouched & `5/5` bit-exact | `LOOP_45_FREEZE_HASH_AUDIT.md` | **PASS** |
