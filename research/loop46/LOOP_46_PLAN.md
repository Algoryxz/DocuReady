# DOCUREADY — LOOP 46 PLAN

**Research Branch:** `loop-46-indic-header-latin-body-recovery`  
**Base Commit:** `c7ed04f` (Loop 45)  
**Protected Release:** Loop 10 (`bdc403a`) — IMMUTABLE  
**Commit Message:** `research(loop46): recover Indic headers with Latin bodies safely`

---

## 1. Objectives

1. **Baseline & Freeze Audit**: Verify `c7ed04f` and `bdc403a` ancestry; recompute all 5 Loop 10 artifact SHA-256 hashes from disk.
2. **Reproduce Conditional-Probe Failure**: Trace exact central/lower/upper counts, ink densities, thumbnail dimensions, and routing decisions on `SYN_DEV_HDR_LAT_BODY` and `SYN_ORI_HDR_LAT_BODY`.
3. **Evaluate Strategies A–E on Calibration Cohort**: Compare A (Loop 45 unchanged), B (probe upper when central & lower are Latin), C (probe upper when central & lower are Latin AND upper ink >= 0.003), D (conflict/inconclusive), and E (3-band + uncertainty) on CAL, checking both accuracy and L17 `< 850 ms` budget.
4. **Implement Winning Strategy & Run Full Qualification**:
   - Positive cohort (Indic header + Latin body/ID, Latin header + Indic body, short upper-only, two-column, tables).
   - Expanded English-only negative controls (seals, stamps, crests, logos, diagonal marks, noise, blank upper + dense Latin, unusual typography).
   - Independent vs synthetic cohorts kept strictly separate.
   - Paired `n=30` warm + `n=5` cold performance qualification (`profile_document()` vs `execute_adaptive_ocr()`).
   - Evidence & coordinate accuracy, full Python + Electron suites, and 26-gate A–Z matrix.
