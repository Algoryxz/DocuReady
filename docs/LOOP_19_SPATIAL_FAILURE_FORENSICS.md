# LOOP 19: Forensic Failure Analysis: The Multi-Column & Table Association Breakdown

## 1. Executive Summary & Forensic Discovery

In Loop 18, `STRESS_03_MULTICOLUMN_EMBEDDED_AMOUNTS` suffered a severe failure, matching only 2 of 4 critical fields (50.0%) and producing an elevated Field CER of 24.2%.

Our forensic deep-dive into the raw execution traces of `execute_adaptive_ocr` on `STRESS_03` uncovered four interacting architectural failure modes:

```
[STRESS_03 Page Layout: 1000 x 1300]
┌─────────────────────────────────────────────────────────────┐
│      Top Banner: DISTRICT AUDIT LEDGER - DUAL COLUMN        │  <-- Spans x=0 to 1000
├──────────────────────────────┬──────────────────────────────┤
│  COLUMN A: REVENUE           │  COLUMN B: DISBURSEMENTS     │
│  Ledger ID: REV-COL-101      │  Voucher No: DIS-VOU-909     │  <-- True Divider at x=500
│  Property Tax: Rs 154000     │  Civil Works: Rs 112000      │
│  Subtotal A: Rs 221700       │  Subtotal B: Rs 194300       │
└──────────────────────────────┴──────────────────────────────┘
                               ▲
                 Gutter Scan Slice at x=367 (INCORRECT)
```

---

## 2. Root Cause Forensic Breakdown

### Root Cause 1: Whole-Page Vertical Slicing Slices the Full-Width Header
- In `adaptive_ocr.py`, when `profile.has_column_gutter` was detected, the engine split the **entire page height** ($y=0$ to $y=1300$) into two crops: `[0, 0, split_x, h]` and `[split_x, 0, w, h]`.
- Because the top banner (`DISTRICT AUDIT LEDGER - DUAL COLUMN`) spanned horizontally across $x=180$ to $x=820$, the vertical cut sliced the words in half.
- The left crop received `DISTRICT AUDIT` and the right crop received `LEDGER - DUAL COLUMN`.

### Root Cause 2: False Script Routing from Dividing Line Noise
- The targeted script probe sampled the central strip of the page with `eng+hin+ori`.
- The pixel strokes of the vertical dividing line (`x=500, width=1`) and colons (`:`) generated noise features that the unconstrained Tesseract probe classified as 2 Devanagari and 11 Odia characters (`Script counts: {'latin': 53, 'devanagari': 2, 'odia': 11}`).
- Because `has_dev > 0` was satisfied, `adaptive_ocr.py` routed the left crop to `lang="hin"`.
- **Result**: Tesseract's Hindi LSTM processed pure English text (`COLUMN A: REVENUE`), producing garbled Devanagari glyphs:
  `[€१5श |॥0:7६&५४-00-04` instead of `Ledger ID: REV-COL-101`.

### Root Cause 3: Column Gutter Offset Error (367 vs 500)
- The horizontal projection profile valley detection looked for the global minimum of ink density.
- In `STRESS_03`, the internal whitespace between the label `Property Tax:` and `Rs 154000` created a vertical whitespace valley at $x=367$ that was deeper than the 1-pixel line at $x=500$.
- The engine chose $x=367$ as the split point, slicing directly through Column A's numerical values!

---

## 3. The Need for Table-Aware Spatial Cell Association

These forensic findings prove that **simple whole-page vertical splitting is fragile**:
1. Documents are not purely two columns from top to bottom; they contain full-width headers, multi-row metadata, and embedded tabular grids.
2. Slicing images before OCR destroys text that crosses the cut line and misidentifies script languages.
3. **The Robust Solution**: Run full-page OCR once (or per coherent block), extract word bounding boxes, and use **spatial geometry and projection profiling** on the detected bounding boxes to cluster words into true table cells, rows, and columns without destructive image cropping!
