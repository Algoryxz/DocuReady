# Loop 25 - Row-Label Failure Forensics

## Executive Summary

Loop 24 evaluated 30 independent documents across Cohort I (102 critical fields), reporting 83 abstentions (81.37% abstention rate) at $T=70.0$. Forensic investigation revealed that **52.8% of these abstentions (44 fields)** were caused not by ambiguous document structure, spatial misalignment, or value degradation, but by **OCR character confusion and single-character glyph degradation within row labels**.

When a row label such as `SOL-ORISSA-01` degraded to `SOL-ORISSA.O1`, or `SUITE-501` degraded to `SUITE-S01`, exact string matching failed completely. The table extractor returned `None` under the `"Missing evidence / no cell found"` category, even though the row existed, the column was identified correctly, and the target value was recognized with high OCR confidence.

## Failure Taxonomy Breakdown (Loop 24 Abstentions)

| Forensic Category | Count | Percentage | Primary Root Cause |
|---|---|---|---|
| Digit/Letter Confusion (`O/0`, `I/1`, `S/5`) | 28 | 33.7% | OCR font substitution in alphanumeric codes |
| Punctuation Substitution (`.` vs `-`) | 12 | 14.5% | Punctuation misclassification in compound IDs |
| Single-Character Insertion / Deletion | 9 | 10.8% | OCR noise in scanned / thermal conditions |
| Low OCR Confidence Floor (< 70.0) | 30 | 36.1% | Legitimate image blur / faint thermal text |
| Sub-token Header Gutter Bleed | 2 | 2.4% | Narrow gutter multi-token fusion |
| Low Resolution Micro-Font Loss | 2 | 2.4% | Micro-font glyph loss |
| **Total Abstentions** | **83** | **100.0%** | |

## Detailed Case Studies

### 1. `SOL-ORISSA-01` vs `SOL-ORISSA.O1` (Solar Tariff Invoice)
- **Document ID:** `COHORT_I_BLIND_01_SOLAR_TARIFF`
- **Field:** `sol1_tariff` (Expected: `3.15`)
- **Extracted Row Text:** `SOL-ORISSA.O1 100 3.15 1642500`
- **Root Cause:** Hyphen recognized as period (`.`), digit `0` recognized as letter `O`.
- **Target Cell Status:** `3.15` was recognized at confidence 88.0%.
- **Impact:** Exact match failed; verified evidence rejected falsely as missing.

### 2. `SUITE-501` vs `SUITE-S01` (Commercial Lease)
- **Document ID:** `COHORT_I_BLIND_08_COMMERCIAL_LEASE`
- **Field:** `s501_rent` (Expected: `18500`)
- **Extracted Row Text:** `SUITE-S01 850 18500 2200`
- **Root Cause:** Digit `5` recognized as capital letter `S`.
- **Target Cell Status:** `18500` recognized with confidence 85.0%.
- **Impact:** Entire commercial lease record dropped.

### 3. `AMOXICILLIN` vs `‘AMOXICILIN` (Pharma Receipt)
- **Document ID:** `COHORT_I_BLIND_06_PHARMACY_RECEIPT`
- **Field:** `amox_total` (Expected: `145.00`)
- **Extracted Row Text:** `‘AMOXICILIN 500MG 10 145.00`
- **Root Cause:** Single `L` deletion and leading apostrophe scan artifact.
- **Target Cell Status:** `145.00` recognized cleanly.

## Design Implications for Loop 25

1. **Deterministic Canonical OCR Equivalence:** Map known substitution equivalences (`O <-> 0`, `I/l <-> 1`, `S <-> 5`, `B <-> 8`, `Z <-> 2`) and strip stray non-alphanumeric punctuation.
2. **Levenshtein String Similarity with Safety Margin:** Allow string edit distance matching only when similarity $\ge 0.85$ and top candidate separates from runner-up by margin $\Delta \ge 0.15$.
3. **Structural Cell Validation:** Validate that target cell conforms to expected syntactic type (e.g. numeric characters present for amount/count).
4. **Risk-Calibrated Confidence Penalty:** Scale confidence by recovery score ($0.95$ for equivalence, ratio for Levenshtein) and require $T \ge 75.0$ for fuzzy recoveries.
