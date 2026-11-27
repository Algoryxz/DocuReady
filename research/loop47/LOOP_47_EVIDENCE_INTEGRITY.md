# LOOP 47 — EVIDENCE & COORDINATE INTEGRITY REPORT

1. **Original-Page Coordinate Accuracy (`SYN_ORI_HDR_LAT_BODY`, `1200×1600`)**:
   - Upper-band region (`0.03..0.25 * H`): `36` recognized words mapped accurately inside the header band.
   - Central/lower body (`0.25..0.85 * H`): `56` recognized words mapped accurately inside the body band.
   - Out-of-bounds (`<0` or `>W,H`): **`0`**.
2. **Native/Fallback Parity, Two-Column, Table Association & Abstention**:
   - All 6 language configurations (`eng`, `hin`, `ori`, `eng+hin`, `eng+ori`, `eng+hin+ori`), two-column horizontal translation (`CHALLENGE_02_ORI_ENG_2COL`), table row/cell association (`test_loop19`), rotation/deskew, and abstention (`ABSTAIN_UNREADABLE`) are verified in the `294 / 294` Python + `25 / 25` Electron test suites (`LOOP_47_TEST_REPORT.md`).
