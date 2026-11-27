# DOCUREADY — LOOP 45 PLAN

**Research Branch:** `loop-45-independent-upper-band-generalization`  
**Base Commit:** `02baae0` (Loop 44)  
**Protected Release:** Loop 10 (`bdc403a`) — IMMUTABLE  
**Commit Message:** `research(loop45): validate regional routing generalization and benchmark integrity`

---

## 1. Objectives

1. **Baseline & Release Freeze Integrity**:
   - Branch cleanly from `02baae0`; verify `02baae0` and `bdc403a` ancestry.
   - Recompute all five Loop 10 release artifact SHA-256 hashes directly from disk and compare against `docs/04-VALIDATION/LOOP_10_FEATURE_FREEZE_RECORD.md`.
2. **Benchmark Boundary & Stage-Timing Investigation**:
   - Explain why Loop 44 reported L17 warm `profile_document()` = `495.17 ms` while L17 warm `execute_adaptive_ocr()` = `368.85 ms`.
   - Measure `n=30` interleaved paired runs of `profile_document()` vs `execute_adaptive_ocr()` with internal stage breakdown (`profile_document`, `select_ocr_strategy`, Stage 3/4 OCR/TSV) plus `n=5` cold subprocess baselines.
3. **Independent Upper-Band Generalization & Negative Controls**:
   - Build a frozen evaluation cohort with explicit `DEV`, `CAL`, and `BLIND` partitions, separating existing real/corpus documents from synthetic/composited fixtures, recording SHA-256, provenance, layout, script distribution, and ground-truth method.
   - Evaluate Loop 44 Strategy D **unchanged** across Devanagari and Odia upper-header docs, Latin-header/Indic-body docs, short upper-only docs, two-column/tabular docs, and English-only negative controls (seals, logos, stamps, noise, decorative marks).
4. **Probe-Resolution & Threshold Audit**:
   - Test `1–5` Indic chars, `6–10` chars, longer passages, shallow headers, low-res/tiny fonts, sparse text, mixed-script identifiers, and false Indic-like glyph patterns across Devanagari and Odia independently.
5. **OCR, Evidence Integrity & Full Regression**:
   - Verify all 6 language configs, native/fallback word+box parity, region coordinate mapping, crop/resize, rotation/deskew, two-column & table association, confidence propagation, and abstention.
   - Run full Python and Electron test suites, reporting exact counts, durations, skips, failures, and overlap without double-counting.
6. **15 Deliverables & Honest A–Z Qualification**:
   - Produce all 15 `LOOP_45_*.md` reports and raw JSON artifacts under `research/loop45/`.
