# Loop 26 - Normalization Collision & Ambiguity Audit

## Collision Test Suite Results

The 10-case adversarial collision test suite executed with **10/10 PASS (100% compliance)**:

| Test ID | Category | Target Pattern | Candidate Rows | Expected Outcome | Observed Outcome | Status |
|---|---|---|---|---|---|---|
| `COL-01` | Prefix Collision | `BATCH-ORD-500` | `BATCH-ORD-500-A`, `BATCH-ORD-500-B` | REJECT | `canon_collision` (score 0.0) | **PASS** |
| `COL-02` | Canonical Substitution | `SUITE-501` | `SUITE-S01`, `SUITE-S02` | MATCH | `canonical_equivalence` (score 0.95) | **PASS** |
| `COL-03` | Canonical Collision | `ROOM-O1` | `ROOM-01`, `ROOM-O1` | REJECT | `canon_collision` (score 0.0) | **PASS** |
| `COL-04` | Drug Name Confusion | `CEFAZOLIN` | `CEFTRIAXONE`, `CEFEPIME` | REJECT | Rejected (score 0.0) | **PASS** |
| `COL-05` | Analyte Lookalike | `BILIRUBIN TOTAL` | `BILIRUBIN DIRECT`, `INDIRECT` | REJECT | Margin guard reject (score 0.0) | **PASS** |
| `COL-06` | Financial Term | `NET REVENUE` | `GROSS REVENUE`, `OPERATING` | REJECT | Margin guard reject (score 0.0) | **PASS** |
| `COL-07` | Short Abbreviation | `CT` | `PT`, `CR` | REJECT | Length gate reject (score 0.0) | **PASS** |
| `COL-08` | Unicode Diacritics | `CAFÉ EXPENSE` | `CAFE EXPENSE` | MATCH | `levenshtein_similarity` (score 0.917) | **PASS** |
| `COL-09` | Punctuation Noise | `TAX 18%` | `*** TAX @ 18% ***` | MATCH | `canonical_equivalence` (score 0.95) | **PASS** |
| `COL-10` | Semantic Contradiction | `FREIGHT CHARGES` | `PAID BY SENDER` (non-numeric) | REJECT | Syntactic guard reject | **PASS** |
