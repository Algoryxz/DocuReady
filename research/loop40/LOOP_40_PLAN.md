# DOCUREADY — LOOP 40 EXECUTION PLAN & CRITIQUE (`/plan` + `/grill-me`)

**Branch:** `loop-40-performance-multilingual-and-windows-qualification`  
**Base Commit:** `77c1f57056fc5373d6b0f30ff24bb6108a5f25fd` (Loop 39)  
**Protected Release:** Loop 10 (`bdc403a601f88008c43c0630f5e8c71ce22c9977`) — 5/5 artifacts bit-exact, untouched.  
**Date:** 27 November 2026

---

## 1. Orchestration & Agent Ownership (`/teamwork` + `/boost`)

| Agent | Scope | Primary Files / Artifacts |
|---|---|---|
| **Agent A — Performance Engineering** | Loop 17 (`DOC_CTRL_01` < 850 ms) & Loop 18 (`DOC_EXT_06` < 1400 ms) profiling, stage instrumentation, ablations, Tesseract startup/model-load cost. | `src/docuready/ingest/adaptive_ocr.py`, `research/loop40/LOOP_40_PERFORMANCE_ROOT_CAUSE.md` |
| **Agent B — Multilingual OCR** | English–Odia adaptive regression (`6.35%` vs `9.36%` CER), script routing, expanded frozen dev/calibration/blind corpus, micro/macro metrics. | `src/docuready/ingest/adaptive_ocr.py`, `src/docuready/ingest/script_router.py`, `research/loop40/LOOP_40_MULTILINGUAL_ACCURACY_REPORT.md` |
| **Agent C — Windows Deployment** | Package A/B paired trials (predeclared margin, sample size, cold/warm startup, throughput, memory), Authenticode signing status, clean-machine lifecycle gates. | `research/loop40/LOOP_40_PACKAGE_AB_QUALIFICATION.md`, `research/loop40/LOOP_40_WINDOWS_TRUST_REPORT.md` |
| **Agent D — Security & Evidence Integrity** | `probe_uncertain` / `probe_error` fail-safe, provenance, offline/no-network, privacy/log redaction, historical regression suites (Loops 09–39). | `research/loop40/LOOP_40_SECURITY_PRIVACY_REPORT.md`, `research/loop40/LOOP_40_TEST_REPORT.md` |
| **Integration Agent** | Shared-file integration (`adaptive_ocr.py`), conflict resolution, full regression verification, A–Z qualification matrix, final commit. | `research/loop40/LOOP_40_QUALIFICATION_MATRIX.md`, `research/loop40/LOOP_40_FINAL_REPORT.md` |

---

## 2. Plan Critique (`/grill-me`)

1. **Are Loop 17/18 regressions reproducible and are we measuring the real path?**
   - Yes: `test_loop17_adaptive_efficiency.py` and `run_loop39_evaluation.py` measure `profile_document(img).profiling_latency_ms` directly. Every call spawns `tesseract.exe` with `lang="eng+hin+ori"` on a `450px` crop.
   - **Risk:** Optimizing `profile_document()` by shrinking the crop too aggressively or dropping Indic models could cause script misdetection. Must preserve `probe_uncertain` fail-safe and validate on all 5 languages.
2. **Why did adaptive `eng+ori` underperform global `eng+hin+ori` on `DOC_MIX_02`?**
   - Hypothesis 1: Tesseract 5.4.0 LSTM model ordering (`eng+ori` vs `ori+eng` vs `eng+hin+ori`) or script-probe threshold (`15%`) / Devanagari-Odia character confusion. Must run controlled ablation on `DOC_MIX_02` and an expanded multi-document corpus before tuning.
3. **Is Package B minimization (`-63.41 MB`) actually beneficial and equivalent?**
   - Loop 39's 3 trials had `~6500 ms` stdev, which is too noisy for 3 samples. We must predeclare a non-inferiority margin (e.g., `+5%` or `+1500 ms`) and run an adequate paired sample size (`n >= 10` alternating `A/B` pairs) measuring cold/warm startup, throughput, memory, packet processing, and export.
4. **Which Windows qualification claims lack real execution evidence?**
   - Authenticode signing credentials and a separate clean Windows VM are unavailable in this local session; those gates must be explicitly marked **BLOCKED**, never simulated.
