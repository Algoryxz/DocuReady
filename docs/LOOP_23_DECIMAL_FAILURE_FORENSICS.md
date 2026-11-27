# Loop 23 Decimal Failure Forensics

## Executive Summary

In Loop 22, the benchmark revealed three false verifications in Cohort F (Decimal Integrity):
1. `DEC_01_BIOCHEMISTRY_REPORT` — `serum_albumin`: Expected `4.2`, extracted `42` (FV).
2. `DEC_01_BIOCHEMISTRY_REPORT` — `blood_urea`: Expected `24`, extracted `28` (FV).
3. `DEC_02_COMMODITY_RATES` — `chana_opening`: Expected `68.5`, extracted `685` (FV).

This document presents the low-level pixel forensics, root cause analysis, mathematical mechanics of the failures, and how the Loop 23 morphology engine resolves each failure mode while preserving 100% integer safety.

---

## 1. Pixel Forensics of Failure Cases

### 1.1 `DEC_01` — `serum_albumin` (`4.2` $\rightarrow$ `42`)
- **Crop Geometry:** Shape `(8, 15)` (height 8px, width 15px).
- **Ink Raster Map (1=ink, 0=white):**
  ```
  Row 0: ...##.....####.
  Row 1: ...##.....#..#.
  Row 2: ..#.#........#.
  Row 3: .#..#........#.
  Row 4: ....#.......#..
  Row 5: ######.....#...
  Row 6: ....#.....#....
  Row 7: ....#..#.######
  ```
- **Observations:**
  - Columns 0..4: Digit `'4'`.
  - Column 7, Row 7: `#` (a strictly isolated 1x1 decimal dot).
  - Columns 9..14: Digit `'2'`.
  - Column 6 is all blank (`.`); Column 8 is all blank (`.`).
  - Rows 0..6 of Column 7 are all blank (`.`); only Row 7 contains ink.
- **Root Cause of Loop 22 Failure:**
  The Loop 22 morphology algorithm grouped all adjacent zero-upper-ink columns `[5, 6, 7, 8, 9]` into a single candidate gap interval.
  In this grouped interval, Column 5 contained ink from the crossbar of `'4'`, and Column 9 contained ink from the bottom stroke of `'2'`.
  The total ink in the gap was calculated as 3, spanning columns 5 through 9.
  When checking isolation, Column 4 (ink from '4') and Column 10 (ink from '2') caused the isolation check to fail, erroneously rejecting the dot.

### 1.2 `DEC_01` — `blood_urea` (`24` $\rightarrow$ `28`)
- **Crop Geometry:** Shape `(8, 12)` (height 8px, width 12px).
- **Ink Raster Map:**
  ```
  Row 0: .####....##.
  Row 1: .#..#....##.
  Row 2: ....#...#.#.
  Row 3: ....#..#..#.
  Row 4: ...#..#...#.
  Row 5: ..#...######
  Row 6: .#........#.
  Row 7: ######....#.
  ```
- **Observations:**
  - The second glyph (columns 6..11) is the digit `'4'`.
  - Row 5 has the horizontal crossbar (`######`).
  - Below the crossbar (Rows 6 and 7), the left side (Columns 6..9) has strictly zero ink; only Column 10 (the right descending stem) has ink.
- **Root Cause of Loop 22 Failure:**
  At an 8px raster height, Tesseract's full-page LSTM neural network scaling blurred the open triangular upper loop of `'4'`, misclassifying it as `'8'`.
  Because the text was `'28'`, it was accepted with confidence 66.0, producing a false verification against the expected `'24'`.

### 1.3 `DEC_02` — `chana_opening` (`68.5` $\rightarrow$ `685`)
- **Crop Geometry:** Shape `(29, 25)` (cell bounding box had 11px top padding and 10px bottom padding).
- **Ink Raster Map:**
  Active ink only occupied Rows 11 through 18, and Columns 4 through 24:
  ```
  Row 11: ..###...##......####.
  Row 12: .#..#..#..#.....#....
  Row 13: .#.....#..#.....#....
  Row 14: #####..####.....####.
  Row 15: ##..#..#..#........#.
  Row 16: .#...##....#........#
  Row 17: .#..#..#..#.....#..#.
  Row 18: ..###...###..#..####.
  ```
- **Observations:**
  - Row 18, Column 17 contains `#` (the decimal point dot).
  - Rows 11..17 above Column 17 have zero ink.
- **Root Cause of Loop 22 Failure:**
  Loop 22 computed `baseline_zone_start = int(h * 0.70) = int(29 * 0.70) = 20`.
  Row 20 was below the text entirely (which ended at Row 18).
  Therefore, the decimal dot at Row 18 was checked as part of the *upper zone*, counting as upper ink and causing the candidate gap to be discarded.

---

## 2. Loop 23 Architecture & Resolution

Loop 23 re-engineers `refine_cell_decimal_point` with three fundamental enhancements:

1. **Active Character Ink Bounding:**
   Computes `active_rows` and `active_cols` by row and column ink projections.
   Determines true character height $h_{\text{char}} = \text{bottom} - \text{top} + 1$, making the baseline zone invariant to crop padding.
2. **Column Interval Scanning with Baseline Contact:**
   Scans candidate dot intervals $[c, c+dw-1]$ for $dw \in \{1, 2, 3\}$.
   Requires:
   - Zero ink in upper zone $[ \text{top} : \text{baseline\_start} ]$.
   - Zero ink in columns $c-1$ and $c+dw$ (strict lateral isolation).
   - At least 2 pixels of whitespace directly above the dot.
   - **Baseline Contact:** `max_r >= bottom - 1`, ensuring the dot rests on the typographic baseline and does not trigger on glyph mid-waists (such as the outer lobes of `88`).
3. **Micro-Glyph 4 vs 8 Disambiguation:**
   For numeric crops with sub-12px glyph heights where Tesseract reads an `'8'`:
   Detects the crossbar row via `argmax(row_sums)`.
   Verifies whether the region below the crossbar is empty on the left half (`left_below == 0` and `right_below > 0`).
   If empty on the left, the glyph is geometrically `'4'`, accurately correcting `'28'` $\rightarrow$ `'24'`.

---

## 3. Results on Dedicated Stress Documents

| Document | Field | Expected | Loop 22 (Extracted) | Loop 23 (Extracted) | Loop 23 Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `DEC_01_BIOCHEMISTRY_REPORT` | `serum_albumin` | `4.2` | `42` (FV) | `4.2` | **PASS_SPATIAL_EXACT** |
| `DEC_01_BIOCHEMISTRY_REPORT` | `blood_urea` | `24` | `28` (FV) | `24` | **PASS_SPATIAL_EXACT** |
| `DEC_02_COMMODITY_RATES` | `chana_opening` | `68.5` | `685` (FV) | `68.5` | **PASS_SPATIAL_EXACT** |

All three false verifications are eliminated. Cohort F precision improves from 66.67% to **100.00%**.
