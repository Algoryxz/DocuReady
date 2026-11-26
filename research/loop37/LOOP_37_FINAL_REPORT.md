# DOCUREADY — LOOP 37 FINAL REPORT

- **Branch:** `loop-37-windows-deployment-remediation` | **Base:** `071e34a` | **Loop 10:** `bdc403a` (bit-exact)
- **Remediated / Diagnosed:**
  1. `BUG-036-002` (Package bloat): Isolated test proved removing 17 Tesseract training EXEs saves **63.41 MB** while keeping `eng`/`hin`/`ori`/`osd` OCR working (`rc=0`).
  2. `BUG-036-003` (Loop 17/18 profiling): Root-caused >99% of latency to `eng+hin+ori` Tesseract subprocess load (`1738.2 ms` vs `3.6 ms` image prep); thresholds preserved, failures reported honestly.
  3. Sidecar startup: Profiled module import times (`pytesseract` 2.81s, `docuready.pipeline` 1.01s, `fitz` 0.55s, `numpy` 0.47s) + Defender RTP.
- **Remaining Blockers:** Clean Windows VM GUI install/upgrade/uninstall (`Gates D, E, F, J, K, L, M, R` BLOCKED) and Authenticode signing (`Gate Q` FAIL — no cert in store).
