# LOOP 18: Adversarial Critical-Field Stress Testing & Failure Boundaries

## 1. Executive Summary

To determine the true failure boundaries of DocuReady's offline OCR engine beyond clean synthetic fixtures, we constructed four dedicated adversarial stress documents (`research/loop18/stress_fixtures/`).

These fixtures simulate the most severe operational challenges encountered in real-world document digitization:
1. **Adversarial Character & Glyph Ambiguity** (similar digits: 0 vs O, 8 vs B, 1 vs I/l, 5 vs S)
2. **Physical Rubber Stamp Overlays** (faint semi-transparent official ink seals covering numbers and dates)
3. **Multi-Column Numerical Ledgers** (dual-column layout with embedded financial values)
4. **Geometrical Skew & Low Contrast** (2.8° scan tilt combined with 40% contrast reduction)

---

## 2. Quantitative Stress Test Results

| Adversarial Fixture | Primary Distortion Mode | Target Fields | Exact Match Rate | Mean Field CER | Mean Latency | Primary Failure Mechanism |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `STRESS_01_SIMILAR_DIGIT_CONFUSION` | Font-level glyph similarity (0/O, 8/B, 1/I, 5/S) | 4 | **75.0% (3/4)** | 1.7% | 1,203.3 ms | Mixed case token `1Il5S` suffered confusion between `1`, `I`, and `l`. |
| `STRESS_02_FAINT_RUBBER_STAMP_OVERLAY` | Translucent blue circular seal over text | 4 | **100.0% (4/4)** | 0.0% | 1,269.2 ms | **Resilient**: Otsu binarization cleanly separated high-contrast black text from faint blue stamp ink. |
| `STRESS_03_MULTICOLUMN_EMBEDDED_AMOUNTS` | Dense dual-column balance sheet with numbers | 4 | **50.0% (2/4)** | 24.2% | 1,571.0 ms | Column A suffered partial bounding-box truncation, though Column B fields (`DIS-VOU-909`, `194300`) passed 100%. |
| `STRESS_04_SKEW_LOW_CONTRAST` | 2.8° rotation + 40% contrast reduction | 3 | **66.7% (2/3)** | 2.2% | 978.4 ms | Certificate ID and date survived; slight character drop in hospital code (`AIIMS-BBSR-8921`). |
| **Stress Suite Aggregate** | **All 4 Severe Adversarial Tests** | **15** | **73.3% (11/15)** | **7.0%** | **1,255.5 ms** | **Robust Graceful Degradation** |

---

## 3. Detailed Fixture Analysis & Root Cause Audit

### Fixture 1: STRESS_01 — Similar Digit Confusion
- **Voucher ID `B801-O08B-1Il5S`**: Tesseract successfully distinguished `B` from `8` and `0` from `O` in `B801-O08B`. The sole failure was in the trailing string `1Il5S`, where the numeral `1` and lowercase `l` had identical stroke geometry in standard fonts.
- **PAN Code `AABCP0815S`**: 100% exact match. The structured 5-letter, 4-digit, 1-letter format was correctly segmented.
- **Meter Reading `808015`**: 100% exact match.

### Fixture 2: STRESS_02 — Faint Rubber Stamp Overlay
- Contrary to expectations that a circular stamp would destroy OCR accuracy, DocuReady achieved **100.0% exact match** on all four critical fields (`TR-2026-99318`, `285400`, `28/09/2026`, `SBIN0004910`).
- **Technical Explanation**: Because the stamp was rendered with low alpha opacity (`alpha = 110/255`), local adaptive binarization discarded the stamp stroke pixels while preserving the dark black text strokes.

### Fixture 3: STRESS_03 — Multi-Column Embedded Amounts
- Column B (`voucher_no`, `subtotal_b`) extracted with 100% precision.
- In Column A, horizontal alignment between `Property Tax: Rs 154000` and `Trade License: Rs 48200` caused adjacent text grouping to clip `ledger_id`.
- **Engineering Recommendation**: For tabular accounting ledgers, table detection or explicit cell bounding box extraction should precede OCR.

### Fixture 4: STRESS_04 — Skew & Low Contrast
- At 2.8° tilt and 40% contrast reduction, standard Tesseract begins to experience baseline wander.
- Despite this, `REG-LOW-2026-118` and `02/05/2026` extracted accurately.
- When contrast falls further (e.g. `CHALLENGE_04`), DocuReady's **Abstention Gate** cleanly triggers, avoiding hallucinated data.
