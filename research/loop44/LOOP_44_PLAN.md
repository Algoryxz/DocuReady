# DOCUREADY — LOOP 44 PLAN

**Research Branch:** `loop-44-upper-band-mixed-script-and-e2e-integrity`  
**Base Commit:** `e5ba978` (Loop 43)  
**Protected Release:** Loop 10 (`bdc403a`) — IMMUTABLE  
**Commit Message:** `research(loop44): improve upper-band script recovery and qualify end-to-end performance`

---

## 1. Objectives

1. **Immutable Baseline & Freeze Hash Audit**:
   - Create `loop-44-upper-band-mixed-script-and-e2e-integrity` from `e5ba978`.
   - Recompute SHA-256 hashes of all five Loop 10 release artifacts and reconcile against `docs/04-VALIDATION/LOOP_10_FEATURE_FREEZE_RECORD.md` (specifically checking the `app.asar` hash character-by-character without modifying the freeze record).
2. **Reproduce & Remediate `BLIND43_IND_HDR_LAT_ID`**:
   - Trace Strategy C on documents with an Indic header above the central probe window (`y < 0.25`) and a blank lower half (`y > 0.52`).
   - Design and implement **Strategy D**: conditional upper-band probing (`0.05–0.22`) only when central (`0.25–0.45`) is monolingual `LATIN` and lower (`0.52–0.85`) is blank/inconclusive, guarded by `>= 6` real Indic letter codepoints to prevent false positives on English pages with logos/stamps.
3. **Routing Ablation & Accuracy Qualification**:
   - Evaluate Strategy D across the existing corpus (`DOC_CTRL_01`, `DOC_EXT_06`, `DOC_HIN_01`, `DOC_MIX_01`, `DOC_MIX_02`) plus rasterized `BLIND44_IND_HDR_LAT_ID`, `BLIND44_LAT_HDR_HIN_BODY`, and `BLIND44_ENG_UPPER_SEAL`.
4. **Separate Profile-Stage vs. E2E Performance Integrity**:
   - Measure cold (`n=5` subprocess) and warm (`n=30` profile / `n=5` E2E) latencies separately for `profile_document()` and `execute_adaptive_ocr()`.
   - Verify Loop 17 (`< 850 ms`) and Loop 18 (`< 1400 ms`) `profile_document()` thresholds remain passing without conflating E2E latency.
5. **Evidence Integrity, Package/Windows Audit & 26-Gate Qualification**:
   - Verify TSV word+box parity across 6 language configurations, run full Python (`tests/test_loop*.py`) + Desktop (`npm --prefix apps/desktop test -- --run`) suites, and produce the 26-gate A–Z qualification matrix.
