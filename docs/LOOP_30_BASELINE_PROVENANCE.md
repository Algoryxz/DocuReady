# Loop 30 — Baseline Provenance & Policy Invariants

## 1. Provenance Context & Authorization
- **Mission:** Loop 30 — Reproducibility, Dataset Provenance, Cohort Integrity & Statistical Qualification.
- **Operating Policy:** Isolated Research Branch. Promotion to production and modification of the frozen release is **STRICTLY PROHIBITED**.
- **Base Commit SHA:** `e5fafd5614ec0646beca37e943439da000116311` (Loop 29 Research Commit).
- **Protected Competition Release:** Loop 10 (`bdc403a`).

---

## 2. Protected Baseline Verification
All 5 release binaries from the Loop 10 competition freeze have been cryptographically audited and confirmed bit-exact:
1. `apps/desktop/dist/DocuReady Setup 0.1.0.exe`
2. `apps/desktop/dist/win-unpacked/DocuReady.exe`
3. `apps/desktop/dist/win-unpacked/resources/sidecar/docuready-engine.exe`
4. Release checksums in `release_manifest.json`
5. Test validation in `tests/test_loop09_release_integrity.py` (9 / 9 passed).

Zero release artifacts were touched, recompiled, or altered during Loop 30.

---

## 3. Threshold Calibration Standards
- **Standard Operating Threshold:** $T^* = 70.0$.
- **Fuzzy String Threshold:** $T_{\text{fuzzy}} = 75.0$.
- **Abstention Policy:** Strict safety-first abstention. Any candidate claim failing entity matching, character ambiguity filters, or cross-document corroboration must abstain.
