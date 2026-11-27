# DOCUREADY — LOOP 47 QUALIFICATION MATRIX (GATES A–Z)

**Total Gates:** `26` | **PASS:** `22` | **PARTIAL:** `2` (Gates O, P) | **BLOCKED:** `2` (Gates W, X) | **FAIL:** `0`

| Gate | Requirement | Expected | Observed | Evidence Path | Status |
|---|---|---|---|---|---|
| **A** | Loop 47 branch & `a9d9b7f` ancestry | Clean branch from `a9d9b7f` | Verified `a9d9b7f` & `bdc403a` ancestors | `LOOP_47_BASELINE_AUDIT.md` | **PASS** |
| **B** | Loop 10 frozen artifact hashes (5/5) | Bit-exact match on disk | 5/5 SHA-256 exact match | `LOOP_47_FREEZE_HASH_AUDIT.md` | **PASS** |
| **C** | Strategy C unchanged baseline | Evaluate without modification | Evaluated across 22 real + 23 synthetic docs | `LOOP_47_STRATEGY_C_BASELINE.md` | **PASS** |
| **D** | Upper-band overhead decomposition | Break down `+246.23 ms` L17 cost | Blank `5.22 ms` vs Inked `295.81 ms` | `LOOP_47_PROBE_PERFORMANCE.md` | **PASS** |
| **E** | Expanded negative-control resistance | `0%` false multilingual routing | `14/14` negative controls stayed `FAST_PATH_ENG` | `LOOP_47_FALSE_POSITIVE_AUDIT.md` | **PASS** |
| **F** | Loop 17 warm `profile_document` | `< 850.0 ms` (warm) | Warm mean `817.17 ms`, median `751.67 ms` (L46 cold `996.48 ms`) | `LOOP_47_E2E_PERFORMANCE.md` | **PASS** |
| **G** | Loop 18 warm `profile_document` | `< 1400.0 ms` (warm) | Warm mean `323.34 ms`, median `321.30 ms` | `LOOP_47_E2E_PERFORMANCE.md` | **PASS** |
| **H** | Separate E2E `execute_adaptive_ocr` metrics | Cold & warm E2E measured separately | Warm `1326.98 / 3100.91 ms` | `LOOP_47_E2E_PERFORMANCE.md` | **PASS** |
| **I** | Threshold & `500 px` probe audit | Compare Devanagari vs Odia | `>= 6` + `500 px` + `0.003` ink validated | `LOOP_47_THRESHOLD_ABLATION.md` | **PASS** |
| **J** | Two-column coordinate integrity | `0` out-of-bounds boxes | `CHALLENGE_02_ORI_ENG_2COL` -> `REGION_AWARE_ROUTING` | `LOOP_47_ROUTING_GENERALIZATION.md` | **PASS** |
| **K** | Original-page coordinate accuracy | Accurate upper/body region mapping | `36` upper + `56` body words, `0` OOB | `LOOP_47_EVIDENCE_INTEGRITY.md` | **PASS** |
| **L** | Table & spatial association regression | `test_loop19` passes | Passed in `294/294` Python suite | `LOOP_47_TEST_REPORT.md` | **PASS** |
| **M** | Native/fallback TSV parity across 6 configs | `100%` word & box parity | Passed in `294/294` Python suite | `LOOP_47_EVIDENCE_INTEGRITY.md` | **PASS** |
| **N** | Uncertainty & monkeypatch safeguards | Preserved under patched/sparse inputs | `doclaynet_001..005` routed safely via `probe_uncertain` | `LOOP_47_ROUTING_GENERALIZATION.md` | **PASS** |
| **O** | Upper-band & shallow-header generalization | All Devanagari & Odia upper headers pass | `10/11` synthetic pass (`SYN47_SHALLOW_ORI_HDR` missed at `10%` height) | `LOOP_47_ROUTING_GENERALIZATION.md` | **PARTIAL** |
| **P** | Package A/B non-inferiority (`CI <= +1500 ms`) | `CI_high <= +1500.0 ms` | Carried forward `CONDITIONALLY QUALIFIED` | `LOOP_47_LIMITATIONS_AND_RISKS.md` | **PARTIAL** |
| **Q** | Loop 14/18 real/corpus preservation | No regression | `5/5` CAL + `12/12` L18 BLIND pass | `LOOP_47_ROUTING_GENERALIZATION.md` | **PASS** |
| **R** | Offline operation & zero external API | Local DLL + local tessdata only | Verified offline, `0` network calls | `LOOP_47_TEST_REPORT.md` | **PASS** |
| **S** | Desktop IPC, isolation & crash recovery | `25/25` desktop tests pass | `25 / 25` passed in `32.90 s` | `LOOP_47_TEST_REPORT.md` | **PASS** |
| **T** | Full Loop 01–46 Python regression suite | Zero failures | `294 / 294` passed in `308.78 s` | `LOOP_47_TEST_REPORT.md` | **PASS** |
| **U** | English-only, Hindi-only, Odia-only stability | Zero regression | `DOC_CTRL_01`, `DOC_HIN_01`, `DOC_EXT_06` pass | `LOOP_47_ROUTING_GENERALIZATION.md` | **PASS** |
| **V** | Separate real/corpus vs synthetic reporting | Disjoint cohorts & provenance | Reported separately in manifest & generalization | `LOOP_47_CORPUS_MANIFEST.md` | **PASS** |
| **W** | Windows Authenticode code signing | Signed EXEs + timestamp | `NotSigned`, `0` certs in store | `LOOP_47_LIMITATIONS_AND_RISKS.md` | **BLOCKED** |
| **X** | Clean-machine Windows VM & SmartScreen | Fresh VM install/upgrade/uninstall | Unavailable in CLI | `LOOP_47_LIMITATIONS_AND_RISKS.md` | **BLOCKED** |
| **Y** | All 16 Loop 47 deliverables complete | 16 reports under `research/loop47/` | All 16 reports created & verified | `research/loop47/` | **PASS** |
| **Z** | Loop 10 immutability preserved | Zero edits/promotion of `bdc403a` | Verified untouched & `5/5` bit-exact | `LOOP_47_FREEZE_HASH_AUDIT.md` | **PASS** |
