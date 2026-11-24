# Loop 25 - Hierarchical Header Conditioning & Semantic Guards

## Header Analysis & Multi-Tier Fusion

Table headers often span multiple physical lines or contain super-headers (e.g. `Total / Amount (INR)`). DocuReady implements hierarchical header conditioning:

1. **Multi-Tier Detection:** Identifies parent header rows lacking numeric tokens and empty spanning cells, fusing parent labels with child column headers.
2. **Semantic Contradiction Guards:** Rejects values when the column header semantically contradicts the query field:
   - Queries expecting `weight` (kg/MT) reject headers containing `freight`, `amount`, `INR`, or `Rs`.
   - Queries expecting `penalty` reject headers containing `advance`, `cleared`, or `base`.
3. **Narrow Gutter Sub-Column Token Resolution:** When narrow borders cause adjacent sub-columns to merge (e.g. `Rate / Tax` containing `45.50 2.25`), sub-header matching isolates the correct token using whitespace gap analysis ($	ext{gap} \ge 8	ext{ px}$).
