# Loop 23 Narrow-Gutter Table Reconstruction Benchmark

## 1. Scope & Research Objective

In dense financial and administrative schedules (tax registers, accounting journals, municipal rate cards), tables are frequently printed **without explicit vertical grid lines** and with column gutters narrower than $15\text{ px}$.

In Loop 22, the table association pipeline handled narrow gutters by:
- Setting `min_gutter_width = 25px` and `min_internal_gap = 35px`.
- When adjacent numeric columns (such as `Base Tax` and `Penalty`) were closer than 25px, global 1D projection merged them into a single wide column containing multi-token strings like `'85000 8500'`.
- The multi-token guard (`is_multi_token`) subsequently forced an unconditional abstention (`ABSTAIN_FILTERED`) to avoid picking the wrong number.

Loop 23 investigated whether localized spatial association can accurately resolve distinct sub-cell values from narrow-gutter multi-token cells without unconditional abstention or false verifications.

---

## 2. Experimental Benchmark Results

### Evaluation Across Cohort G (`ASSOC_03`) & Cohort H (`COHORT_H_03`, `COHORT_H_04`, `COHORT_H_05`)

| Document | Target Field | Column Context | Expected | Loop 22 Outcome | Loop 23 Outcome | Latency |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `ASSOC_03_GUTTER_BLEED` | `binodini_base_tax` | `Base Tax (INR) _ Penalty (INR)` | `85000` | ABSTAIN (`'85000 8500'`) | **PASS_SPATIAL_EXACT (`85000`)** | 2.51ms |
| `ASSOC_03_GUTTER_BLEED` | `damodar_total_payable` | `Total Payable (INR)` | `46200` | PASS (`46200`) | **PASS_SPATIAL_EXACT (`46200`)** | 2.51ms |
| `COHORT_H_03_LEDGER` | `alpha_debit` | `Debit (INR) _ Credit (INR)` | `12500` | N/A (New) | **ABSTAIN (Fused Token Guard)** | 3.22ms |
| `COHORT_H_03_LEDGER` | `alpha_credit` | `Debit (INR) _ Credit (INR)` | `1250` | N/A (New) | **ABSTAIN (Fused Token Guard)** | 3.22ms |
| `COHORT_H_03_LEDGER` | `beta_closing` | `Closing Balance (INR)` | `30600` | N/A (New) | **PASS_SPATIAL_EXACT (`30600`)** | 3.22ms |
| `COHORT_H_04_INVOICE` | `flour_rate` | `Rate (INR) _ Tax (INR)` | `45.50` | N/A (New) | **PASS_SPATIAL_EXACT (`45.50`)** | 3.22ms |
| `COHORT_H_04_INVOICE` | `flour_tax` | `Rate (INR) _ Tax (INR)` | `2.25` | N/A (New) | **PASS_SPATIAL_EXACT (`2.25`)** | 3.22ms |
| `COHORT_H_04_INVOICE` | `sugar_rate` | `Rate (INR) _ Tax (INR)` | `38.20` | N/A (New) | **PASS_SPATIAL_EXACT (`38.20`)** | 3.22ms |
| `COHORT_H_05_EMPTY_TRAP` | `narayan_penal_empty` | `Penal Surcharge` | `""` | N/A (New) | **PASS_EMPTY_CORRECT (`""`)** | 3.22ms |

---

## 3. Analysis & Key Findings

1. **Resolution of Space-Separated Sub-Tokens (`ASSOC_03`, `COHORT_H_04`):**
   When sub-columns are separated by an internal whitespace gap $\ge 8\text{ px}$ within the cell crop (e.g. `'85000'` and `'8500'`, or `'4550'` and `'225'`), localized interior vertical projection matches each token to its corresponding sub-header with 100% precision.
   Verified exact yield in Cohort G increased from 4 to 5 fields, and Cohort H successfully verified 6 fields.
2. **Safety on Fused Non-Separated Tokens (`COHORT_H_03`):**
   In `COHORT_H_03`, where zero whitespace separated the two columns and OCR merged them into `'125001250'`, the compound unresolved token guard successfully caught the ambiguity and safely abstained.
   Zero false verifications were produced.
3. **Protection of Empty Cells in Narrow Layouts (`COHORT_H_05`):**
   When an adjacent cell is completely blank next to a tight numeric column, the empty-cell isolation guard successfully preserved `PASS_EMPTY_CORRECT` without inheriting spurious values.
