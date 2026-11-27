# DOCUREADY — LOOP 47 PLAN

**Research Branch:** `loop-47-independent-mixed-script-generalization`  
**Base Commit:** `a9d9b7f` (Loop 46)  
**Protected Release:** Loop 10 (`bdc403a`) — IMMUTABLE  
**Commit Message:** `research(loop47): validate mixed-script generalization and probe efficiency`

---

## 1. Objectives

1. **Baseline & Release Integrity**: Branch from `a9d9b7f`; verify `a9d9b7f` and `bdc403a` ancestry; recompute all 5 Loop 10 artifact SHA-256 hashes from disk.
2. **Independent Corpus Provenance & Unchanged Strategy C Baseline**: Keep real/corpus documents strictly separate from synthetic/composited fixtures; evaluate Loop 46 Strategy C **unchanged** across all cohorts, recording band-level evidence, probe activation, routing, and CER/WER.
3. **Expanded Negative Controls & Threshold Audit**: Expand negative controls (seals, stamps, crests, logos, watermarks, signatures, diagonal marks, noise, English tables, visually Indic-like marks, sparse/low-quality scans); evaluate `>= 6` Indic guard, `0.003` ink threshold, `0.05..0.22` boundaries, and `500 px` probe dimension across Devanagari and Odia independently.
4. **Upper-Band Overhead & Cold/Warm Qualification**: Decompose the `+246.23 ms` L17 upper-band probe overhead (`crop/resize`, `recognize_gray`, codepoint counting, full-res TSV OCR, coordinate mapping); run paired `n=30` warm and `n=5` cold subprocess benchmarks for L17 and L18, preserving historical `< 850 ms` / `< 1400 ms` thresholds and comparing honestly against Loop 46 cold L17 (`996.48 ms`).
5. **Evidence Integrity & Full Regression**: Verify 6-lang TSV parity, original-page coordinate accuracy across upper/central/lower/two-column regions, and run full Python + Electron test suites.
6. **16 Deliverables**: Produce all 16 `LOOP_47_*.md` reports and raw JSON artifacts under `research/loop47/`.
