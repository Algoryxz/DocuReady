# Loop 25 - Comprehensive Abstention Ledger

## Aggregate Accounting

Across the combined 142-document, 416-critical-field benchmark, DocuReady achieved:
- **Total Evaluated Fields:** 416
- **Verified Claims:** 262 (Exact Matches: 262, False Verifications: 0)
- **Abstentions:** 154
- **Accounting Invariant:** 262 + 0 + 154 = 416 (100% mutually exclusive conservation)

## 12-Category Abstention Taxonomy Distribution

| Taxonomy Category | Combined Corpus | Cohort J (New) | Cohort I (Loop 24) | Loops 20-23 |
|---|---|---|---|---|
| Confidence Floor (< 70.0) | 83 | 15 | 45 | 23 |
| Missing Evidence (Unresolved Row/Table) | 48 | 13 | 29 | 6 |
| Header Ambiguity (Semantic Contradiction) | 16 | 10 | 0 | 6 |
| Spatial Ambiguity (BBox Overlap / Collision) | 2 | 0 | 0 | 2 |
| Multi-Token Bleed | 0 | 0 | 0 | 0 |
| Decimal/Integer Ambiguity | 0 | 0 | 0 | 0 |
| Cross-Doc Conflict | 0 | 0 | 0 | 0 |
| OCR Uncertainty | 0 | 0 | 0 | 0 |
| Unsupported Font | 0 | 0 | 0 | 0 |
| Ground-Truth Ambiguity | 0 | 0 | 0 | 0 |
| Processing Failure | 0 | 0 | 0 | 0 |
| Other (Syntax Garble / Compound Header) | 5 | 2 | 2 | 1 |
| **Total Abstentions** | **154** | **40** | **76** | **38** |

## Audit of Abstention Rationales

1. **Confidence Floor (53.9% of abstentions):** Cells with degraded ink, scanner blur, or thermal contrast where raw OCR confidence fell below the frozen $T=70.0$ threshold.
2. **Missing Evidence (31.2% of abstentions):** Adversarial test fixtures with intentionally omitted row identifiers or severely truncated OCR bounding boxes where no candidate exceeded recovery thresholds.
3. **Header Ambiguity (10.4% of abstentions):** Adversarial test cases verifying semantic guards (e.g. `freight_amount` column header rejecting queries for `net_weight`).
4. **Spatial Ambiguity (1.3% of abstentions):** Cell crops overlapping multiple row bounding boxes in tight multi-column accounting tables.
