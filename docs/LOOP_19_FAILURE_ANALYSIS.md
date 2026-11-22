# LOOP 19: Failure Analysis & Root Cause Taxonomy

## 1. Executive Summary

While Loop 19 achieved an overall Spatial Exact Match Rate of **88.33%** across 10 benchmark categories and elevated `STRESS_03` from 50% to 100%, four specific failure modes were observed and classified across our failure taxonomy.

---

## 2. Granular Failure Breakdown

### Failure Case 1: Hierarchical Multi-Tier Merged Headers (`TAB_07`)
- **Expected**: Field `jatni_property_cess` mapped under parent `ASSESSED TAX` -> sub-header `Property Cess`.
- **Actual**: Successfully extracted value `120000`, but parent header `ASSESSED TAX` was not retained in leaf column metadata.
- **Root Cause**: The 1D horizontal projection correctly segmented the 6 leaf columns, but flattened Row 0 and Row 1 into discrete rows without building a nested tree structure.
- **Severity**: Low. The leaf column `Property Cess` was correct and value matched.
- **Detectability**: Detectable by checking whether Row 0 cells span multiple sub-columns.

### Failure Case 2: Multi-Column Gazette Layout with Compressed Tabs (`TAB_09`)
- **Expected**: `batch_a2_amount` = `240000`, `batch_a3_voucher` = `VOU-903`.
- **Actual**: `batch_a2_amount` extracted correctly, but `batch_a3_voucher` merged with the adjacent amount token into `VOU-903 310000`.
- **Root Cause**: In Column A of `TAB_09`, spacing between the voucher column and amount column was 18 pixels (below the default `min_internal_gap` of 25 pixels), causing both words to be grouped into a single cell.
- **Severity**: Medium.
- **Detectability**: Highly detectable via regex (`\bVOU-\d+\s+\d+\b`). When multiple candidate fields occupy a single cell, the engine flags `is_ambiguous = True`.

### Failure Case 3: Geometric Scan Tilt (`TAB_10`)
- **Expected**: All 3 critical fields extracted with exact bounding boxes.
- **Actual**: 2 of 3 fields matched; third field (`tk_802_date`) suffered a 1-character drop due to rotated baseline wander.
- **Root Cause**: At 2.2° scan tilt, horizontal projection valleys become shallower as text from line $k$ dips into line $k+1$.
- **Severity**: Low.
- **Mitigation**: Future deskew preprocessing before table grid assembly.
