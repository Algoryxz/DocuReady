# Loop 22 — Forensic Failure Analysis of Remaining Errors

**Total Documents:** 46  
**Total Critical Fields:** 95  
**Remaining False Verifications:** 3 (All in Cohort F: Decimal Integrity)

---

## 1. Inventory of the 3 Remaining Failures

In the Loop 22 evaluation, false verifications dropped by 78.6% (from 14 down to 3). All 3 remaining false verifications are localized strictly within Cohort F (Low-Resolution Decimal Stress Fixtures):

### Failure 1: `DEC_01_BIOCHEMISTRY_REPORT` — `serum_albumin`
- **Expected:** `'4.2'`
- **Extracted:** `'42'`
- **Cell BBox:** `(292, 122, 307, 130)` (Height: 8px, Width: 15px)
- **OCR Confidence:** 92.0
- **Root Cause:** C. OCR Candidate Error (Missed Decimal Dot).
- **Technical Analysis:** In an 8px tall crop, the period is a single 1px dot abutting the vertical stem of digit '2'. Because the space between digits is only 3px and the dot touches the adjacent column in row 7, the strict 4-sided whitespace isolation filter deliberately rejected it to avoid creating false dots on character stems.
- **Why It Passed Gate:** Tesseract reported 92.0 confidence on the two digits '42', and because the digits are clean and within standard range, no syntax garble or multi-token trigger was activated.
- **Remediation Path:** Sub-pixel bicubic interpolation or high-resolution scanning.

### Failure 2: `DEC_01_BIOCHEMISTRY_REPORT` — `blood_urea`
- **Expected:** `'24'`
- **Extracted:** `'28'` (Confidence: 66.0)
- **Root Cause:** C. OCR Candidate Error (Character Misrecognition).
- **Technical Analysis:** In low-resolution raster rendering, the horizontal crossbar and diagonal of digit '4' merged with the right vertical stroke, causing Tesseract to recognize digit '8' instead of '4' (`'24'` -> `'28'`).
- **Remediation Path:** Raising the confidence threshold to $T = 70.0$ safely abstains this field (as verified in `threshold_sweeps`), but at the cost of 5 valid fields elsewhere.

### Failure 3: `DEC_02_COMMODITY_RATES` — `chana_opening`
- **Expected:** `'68.5'`
- **Extracted:** `'685'`
- **Cell BBox:** `(292, 202, 316, 210)` (Height: 8px, Width: 24px)
- **OCR Confidence:** 70.0
- **Root Cause:** C. OCR Candidate Error (Missed Decimal Dot).
- **Technical Analysis:** Similar to `serum_albumin`, at 8px vertical crop height, the period is drawn at row 3 with empty padding below, causing baseline zone profiling to miss the dot.

---

## 2. Key Takeaways

1. **Zero Failures in Generalization Cohorts:** All 10 blind documents and all 8 challenge documents achieved 0 false verifications.
2. **Resolution Boundary:** The remaining failures reflect fundamental limits of 1x resolution raster OCR on sub-8px character heights, not algorithmic or spatial association defects.
