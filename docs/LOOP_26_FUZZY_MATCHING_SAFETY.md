# Loop 26 - Fuzzy Matching Safety & Confidence Gating

## Gating Architecture

Evidence-guided fuzzy matching operates under three cascading safety barriers:

1. **Safety Margin Guard (Delta >= 0.15):** A candidate must lead its runner-up by at least 0.15 similarity ratio to eliminate prefix collisions.
2. **Elevated Confidence Floor (T_fuzzy = 75.0):** Fuzzy matches must achieve an effective OCR confidence >= 75.0% (vs 70.0% for exact/canonical matches).
3. **Target Cell Syntactic Type Validation:** Candidate cell contents must conform to the expected data type (e.g. numeric characters present for amount/count), completely preventing textual labels from binding to numeric fields.
