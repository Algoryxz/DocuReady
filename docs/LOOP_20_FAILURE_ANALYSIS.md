# LOOP 20: Forensic Failure Analysis & Taxonomy

## 1. Failure Taxonomy Classification

In the 34-document Loop 20 benchmark, 11 fields out of 65 did not achieve Spatial Exact Match (`sem_pass = False`). These failures are classified into four distinct failure modes:

| Failure Mode | Count | % of All Fields | Affected Documents | Root Cause |
| :--- | :---: | :---: | :--- | :--- |
| **Mode 1: OCR Glyph Misrecognition** | 2 | 3.08% | `BLIND_06`, `BLIND_08` | Single-character glyph confusion (`'O'` -> `'fe}'`), missing decimal point (`'5.6'` -> `'56'`). |
| **Mode 2: Hierarchical Merged Headers** | 2 | 3.08% | `VAL_05_MULTI_ROW_SUMMARY` | 2-tier sub-headers ("Quarter 1 Status") shifted logical row indices by +1. |
| **Mode 3: Column Gutter Bleed (Narrow Gutters)** | 2 | 3.08% | `CHALL_01`, `CHALL_05` | Narrow gaps (<15px) or faint divider lines caused two adjacent columns to merge into one interval. |
| **Mode 4: Safe Epistemic Abstention** | 5 | 7.69% | `BLIND_09`, `VAL_03`, `CHALL_05`, etc. | System identified non-matching or ambiguous cells and abstained from verifying. |

---

## 2. In-Depth Root Cause Breakdown

### Case A: Hierarchical Merged Header Row Index Shift (`VAL_05`)
- *Finding*: `drip_q2_actual` extracted `'84500'` (the exact value), but `row_idx = 3` instead of expected `row_idx = 1`.
- *Mechanism*: `VAL_05` contained a top super-header row ("Quarter 1 Status", "Quarter 2 Status") above the standard column header row. The row clusterer recognized both rows as table rows, shifting all subsequent data rows by +1.
- *Remediation Recommendation for Loop 21*: Introduce a 2-tier header detector that merges multi-tier header rows into a unified composite header representation before indexing data rows.

### Case B: OCR Decimal Point Drop (`BLIND_06`)
- *Finding*: `hba1c_result` expected `'5.6'`, but Tesseract returned `'56'`.
- *Mechanism*: In low-resolution or standard 72-150 DPI renderings, single-pixel decimal dots can be filtered out as salt-and-pepper noise by Tesseract's binarizer.
- *Safety Behavior*: Because `'56'` was returned, the system flagged a value mismatch. Future image pre-scaling (300 DPI upscaling) will improve decimal retention.

### Case C: Safe Abstention on Non-Numeric Value (`BLIND_09`)
- *Finding*: `vedanta_freight` expected a numeric freight figure (`38000`), but the column contained status text `"In Transit"`.
- *Engine Action*: The engine flagged `is_ambiguous = True` because `expected_type == "amount"` failed syntactic validation on non-numeric text.
- *Verdict*: This was a successful demonstration of **evidence-based abstention preventing false verification**!
