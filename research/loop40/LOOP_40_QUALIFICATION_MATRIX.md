# Loop 40 Qualification Matrix (26 Reconciled Gates: A–Z)

**Date:** 2026-11-27  
**Branch:** `loop-40-performance-multilingual-and-windows-qualification`  
**Baseline:** Loop 39 (`77c1f57`) | **Protected Release:** Loop 10 (`bdc403a`)

| Gate | Domain | Criterion / Threshold | Observed Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **A** | Release Protection | Loop 10 (`bdc403a`) untouched & 5/5 SHA-256 hashes match | 5/5 bit-exact SHA-256 match | **PASS** |
| **B** | Branch Isolation | Isolated branch `loop-40-performance-multilingual-and-windows-qualification` | Verified on isolated branch | **PASS** |
| **C** | Loop 17 Latency | `DOC_CTRL_01` `profile_document()` 30-rep mean `< 850.0 ms` | Mean `142.00 ms` (cold `271.96 ms`) | **PASS** |
| **D** | Loop 18 Latency | `DOC_EXT_06` `profile_document()` 10-rep mean `< 1400.0 ms` | Mean `159.95 ms` (cold `321.62 ms`) | **PASS** |
| **E** | Probe Fail-Safe | `probe_uncertain` / `probe_error` fallback preserved | `test_loop39_probe_hardening.py` 3/3 pass | **PASS** |
| **F** | Unreadable Abstention | Blank/unreadable pages abstain (`ABSTAIN_UNREADABLE`) | `CHALLENGE_04` & blank test abstain | **PASS** |
| **G** | Eng+Ori Routing Fix | `DOC_MIX_02` matches/beats `eng+hin+ori` (`6.35%` CER) | CER `6.35%`, WER `17.39%` | **PASS** |
| **H** | English-Only Anchor | `DOC_CTRL_01` `FAST_PATH_ENG` accuracy preserved | CER `0.00%`, WER `0.00%` | **PASS** |
| **I** | Hindi-Only Accuracy | Adaptive beats Global on `Hindi-only` (`n=4`) | Micro CER `19.74%` vs `22.71%` | **PASS** |
| **J** | Odia-Only Accuracy | Adaptive beats Global on `Odia-only` (`n=1`) | Micro CER `3.76%` vs `7.52%` | **PASS** |
| **K** | Tri-Script Accuracy | Adaptive beats Global on `Tri-script` (`n=8`) | Micro CER `15.53%` vs `23.36%` | **PASS** |
| **L** | Blind Generalization | Adaptive beats Global on `BLIND` partition (`n=6`) | Micro CER `17.16%` vs `19.10%` | **PASS** |
| **M** | Overall Corpus | Adaptive beats Global across 35-doc corpus | Micro CER `19.56%` vs `20.81%` | **PASS** |
| **N** | Critical Fields & Tables | Loop 17/18/19/20 critical-field & table tests pass | All pytest assertions pass | **PASS** |
| **O** | Package B Footprint | 17 unused EXEs removed without functional loss | `-66,485,066 B` (`-63.40 MiB`), `10/10` ok | **PASS** |
| **P** | Package A/B Margin | Paired `95% CI_high <= +1500 ms` (`n=10`) | Mean `-33.87 ms`, CI `[-4584, +4516]` | **FAIL** |
| **Q** | Python Core & OCR | Loops 09, 10, 14–20, 27, 28, 32, 33, 35, 39 + OCR suites | `190/190` passed | **PASS** |
| **R** | Desktop Unit & Sidecar | `@docuready/desktop` `npm test` | `25/25` passed | **PASS** |
| **S** | Desktop TypeScript | `@docuready/desktop` `npm run lint:types` | `tsc --noEmit` exit `0` | **PASS** |
| **T** | Zero-PII & Redaction | `test_redaction_safe_logging.py` & `test_ui_privacy.py` | Passed | **PASS** |
| **U** | IPC & Path Security | `validateIpcSender`, CSP, traversal block | Passed in `npm test` | **PASS** |
| **V** | Evidence Provenance | `test_evidence_provenance_contract.py` & bbox tests | Passed | **PASS** |
| **W** | Authenticode Signing | Signed `DocuReady.exe`, `sidecar.exe`, `Setup.exe` | `NotSigned`; no cert / `signtool` | **BLOCKED** |
| **X** | Clean-VM SmartScreen | Clean Windows VM install & SmartScreen reputation | No clean VM available on host | **BLOCKED** |
| **Y** | Pre-Existing Artifacts | Untouched `.agents/`, `docs/product/`, `hacknation*`, etc. | Preserved untouched, uncommitted | **PASS** |
| **Z** | Deliverables & Commit | All Loop 40 docs/JSONs & exact commit message | Verified before commit | **PASS** |

**Summary:** **23 PASS**, **1 FAIL** (Gate P: statistical CI width on `n=10` noisy cold-process A/B runs), **2 BLOCKED** (Gates W, X: Windows code signing & clean VM).
