# LOOP 24 — ABSTENTION FORENSICS & TAXONOMY AUDIT

## 1. 12-Category Abstention Taxonomy

Loop 24 standardizes all non-verified fields across 12 mutually exclusive root-cause categories:

1. **OCR uncertainty / low confidence**: OCR token confidence is low or character noise detected.
2. **Spatial ambiguity / overlapping cells**: Cell boundaries exceed expected column gutters or bleed across cells.
3. **Header ambiguity / unmapped columns**: Column label contradicts expected semantic or target column is unmapped.
4. **Multi-token bleed across narrow gutters**: Space-delimited numbers merged in single cell cannot be safely disambiguated.
5. **Decimal/integer ambiguity**: Number format is ambiguous or cannot be verified with high confidence.
6. **Cross-document conflict / inconsistency**: Conflicting values across multiple pages or tables.
7. **Missing evidence / unlocated field**: Target pattern or row could not be located in the OCR stream.
8. **Confidence below frozen threshold**: OCR recognition confidence is below the frozen threshold ($T^* = 70.0$).
9. **Unsupported font / scale degradation**: Micro-glyphs smaller than readable resolution.
10. **Ground-truth ambiguity**: Ambiguous ground-truth specification.
11. **Processing failure / exception**: Unhandled exception during extraction.
12. **Other**: Miscellaneous edge cases.

---

## 2. Quantitative Abstention Breakdown

### Cohort I (30 Documents, 83 Abstentions)

| Abstention Category | Count | Percentage | Primary Root Cause Analysis |
| :--- | :---: | :---: | :--- |
| **Missing evidence** | 51 | 61.45% | Tesseract character substitution in target labels (e.g. `SKU-7734` read as `SKU-T734`, `CN-2026-081` read as `CN-2026-08|`). DocuReady abstained rather than making probabilistic guesses. |
| **Confidence floor** | 30 | 36.14% | Cell tokens recognized with confidence between 40% and 69.9% (below the frozen $T^*=70.0$ threshold). |
| **Other** | 2 | 2.41% | Expected empty cells correctly verified as empty and withheld from numeric claim metrics. |
| **Total** | **83** | **100.00%** | **Zero spurious or uncategorized drops.** |

---

### Combined 82-Document Corpus (125 Abstentions)

| Abstention Category | Count | Percentage |
| :--- | :---: | :---: |
| **Missing evidence** | 66 | 52.80% |
| **Confidence floor** | 48 | 38.40% |
| **Header ambiguity** | 5 | 4.00% |
| **Spatial ambiguity** | 3 | 2.40% |
| **Other** | 3 | 2.40% |
| **Total** | **125** | **100.00%** |

---

## 3. Key Forensics Finding

The dominant driver of abstention in Cohort I is **OCR character degradation in row identifiers** (e.g. slight font rasterization leading Tesseract to misrecognize hyphenated codes or single letters). 

Because DocuReady requires exact token matching on target row labels before intersecting with columns, when an identifier is corrupted by OCR, DocuReady **safely abstains** under `Missing evidence` instead of falsely binding adjacent values.

This explains why **Critical Field Precision remains 100.00%**: the system refuses to guess when evidence is missing or corrupted.
