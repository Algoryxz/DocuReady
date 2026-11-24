# Loop 25 - Limitations & Future Research Directions

## Identified Limitations

1. **Severely Warped Documents:** Extreme non-linear document curling (> 15 degrees) requires dedicated cylindrical mesh unwarping before grid assembly.
2. **Complex Multi-Row Spanning Cells:** Cells spanning across 3 or more rows in unbordered tables remain challenging for gutter detection.
3. **Highly Faint Thermal POS Print:** Extremely degraded thermal receipts with global contrast < 10% fall below the $T=70.0$ confidence floor and abstain by design.
