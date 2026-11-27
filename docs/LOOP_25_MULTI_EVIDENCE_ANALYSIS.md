# Loop 25 - Multi-Evidence Agreement Analysis

## Triangulation Protocol

DocuReady achieves 100% precision by requiring multi-evidence consensus across three orthogonal signals before confirming any recovered field:

1. **Row Evidence:** Alphanumeric label matches either exactly, through canonical equivalence, or via margin-guarded Levenshtein similarity.
2. **Column Evidence:** Extracted cell bounding box aligns horizontally with the column header, or header text matches the requested semantic pattern.
3. **Target Cell Evidence:** The extracted cell value conforms to the syntactic type expected by the domain schema (e.g. numeric digits for amounts/counts, date format for dates, non-empty for non-empty fields).

If any of the three evidence signals fails, the field is safely abstained.
