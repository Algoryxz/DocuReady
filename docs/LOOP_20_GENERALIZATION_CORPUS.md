# LOOP 20: Independent Document Generalization Corpus Report

## 1. Corpus Design Rationale

Loop 19 established a baseline across 10 controlled fixtures (`TAB_01`–`TAB_10`). While `STRESS_03` was resolved, the evaluation suite was small and partially shared structure with development samples.

Loop 20 expands the evaluation horizon to **34 independent documents** across **6 major administrative and commercial domains**:
1. **Commercial & Fiscal Invoices**: Invoices, tax schedules, bills of entry, procurement budgets.
2. **Academic & Examination Records**: School boards, high school certificates, university semester transcripts.
3. **Public Revenue & Land Records**: Tehsildar Khatauni, municipal property holding taxes, cess registers.
4. **Treasury & Banking Statements**: Government pension disbursement orders, cooperative savings ledgers, urban body vouchers.
5. **Civic & Social Welfare Records**: PDS foodgrain ration allocations, social welfare applicant forms.
6. **Judicial & Transport Manifests**: High court petition fee registries, interstate freight manifests.

---

## 2. Structural Layout Distribution

Across the 34 documents:
- **Table Density**: 4 to 6 columns, 3 to 6 rows per table (totaling >140 distinct table cells).
- **Layout Variations**:
  - Bordered grids with sharp stroke dividers (26 documents).
  - Borderless whitespace-delimited tabular alignment (2 documents).
  - Multi-line wrapped cell descriptions (3 documents).
  - Hierarchical multi-tier merged headers (2 documents).
  - Degraded photocopied noise scans (2 documents).
  - Narrow column gutters (<15px) for spatial bleed stress (2 documents).
  - Intentionally empty and blank cells (4 documents).
- **Script Coverage**:
  - English monolingual documents (32 documents).
  - Odia/English mixed bilingual administrative registers (2 documents).

---

## 3. Critical Field Specification

Every document in the corpus is accompanied by an independent `_cf.json` contract defining:
- `name`: Target critical field identifier.
- `expected`: Ground-truth string value.
- `row`: Logical 0-indexed data row within the table body.
- `col`: Logical 0-indexed column within the table.
- `type`: Semantic category (`amount`, `date`, `id`, `marks`, `count`, `weight`, `empty`).
- `target_pattern`: Row or record anchor string used for semantic localization.

Total critical fields across the 34 documents: **68 critical fields**.
- Cohort A (Dev): 16 fields
- Cohort B (Val): 16 fields
- Cohort C (Blind): 20 fields
- Cohort D (Challenge): 16 fields
