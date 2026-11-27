# DOCUREADY — LOOP 43 COORDINATE INTEGRITY REPORT

- **Two-Column Synthetic Bilingual Test (`1200x700` Hindi left + English right):**
  - Selected strategy: `REGION_AWARE_ROUTING`
  - Words extracted: `17`
  - Out-of-bounds bounding boxes (`l < 0`, `t < 0`, `l+w > W+2`, `t+h > H+2`): **`0`**
- **Loop 42/43 Full-Page `DOC_CTRL_01` Bounds Check:** `83` TSV rows, **`0` out-of-bounds** (`coord_oob_17 = 0`).
- **Table & Spatial Association (`test_loop19_table_association.py`):** Passed within the `267/267` pytest regression run.
