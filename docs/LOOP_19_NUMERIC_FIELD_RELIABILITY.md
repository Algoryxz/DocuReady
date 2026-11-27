# LOOP 19: Critical-Field Extraction & Numeric Reliability Analysis

## 1. Executive Summary & Numeric Safeguards

Numerical extraction in document audits carries disproportionate risk:
- Dropping a zero turns \$10,000 into \$1,000.
- Confusing a digit `8` with `B` or `0` with `O` corrupts tax IDs and voucher codes.
- Assigning a number from Row 2 to Row 1 switches benefits between applicants.

In Loop 19, we stress-tested numeric reliability using `TAB_04_SIMILAR_ADJACENT_VALUES` and `TAB_03_DENSE_NUMERIC_COLUMNS` to evaluate exact value preservation and row/column binding.

---

## 2. Quantitative Results on Similar Adjacent Values (`TAB_04`)

| Field Name | Expected Numeric Value | Adjacent Confuser Value in Same Row | Extracted Value | Row / Col Binding | Result |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `tier_01_topup` | `10000` | `1000` (Base Subsidy in Col 1) | `10000` | Row 1, Col 2 | **EXACT PASS** |
| `tier_02_base` | `10000` | `1000` (Top-Up Grant in Col 2) | `10000` | Row 2, Col 1 | **EXACT PASS** |
| `tier_03_beneficiaries`| `1080` | `8800` (Final Total in Col 3) | `1080` | Row 3, Col 4 | **EXACT PASS** |
| `tier_04_beneficiaries`| `1800` | `8800` (Final Total in Col 3) | `1800` | Row 4, Col 4 | **EXACT PASS** |

### Key Numeric Protections Implemented
1. **Zero Leading-Zero Truncation**: Numeric values are extracted as strings to prevent loss of leading zeros in serial codes (e.g. `TK-801`, `01`, `08/01/2026`).
2. **Columnar Coordinate Boundaries**: Because `1000` and `10000` appeared on the same horizontal row in adjacent cells, full-page regex would match either interchangeably. Spatial cell projection ensured that `Base Subsidy` (Col 1) and `Top-Up Grant` (Col 2) remained strictly isolated.
3. **Punctuation Sensitivity**: Strips currency prefixes (`Rs`, `INR`, `$`) while preserving decimal points and negative signs.
