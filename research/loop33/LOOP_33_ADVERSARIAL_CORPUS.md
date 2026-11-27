# DOCUREADY — LOOP 33 ADVERSARIAL TEST CORPUS & EVALUATION

**Milestone:** Loop 33 — Domain Rules & Decision Integrity  
**Corpus Specification:** `research/loop33/adversarial_fixtures.json`  
**Test Suite:** `tests/test_loop33_rule_adversarial.py`  
**Total Adversarial Cases:** 19  
**Result:** 19 PASSED, 0 FAILED (100% Pass Rate)  
**Date:** 2026-11-25  

---

## 1. Corpus Design Principles

The Loop 33 Adversarial Corpus tests the boundary conditions, confusable character pairs, structural parsing edge cases, and decision invariants across all 8 rule families. 

The goal is to verify that:
1. Confidently wrong outputs are prevented.
2. Character confusions at syntax-critical positions trigger abstention (`REVIEW`).
3. Mathematical check-digits (Verhoeff) reject all single-digit substitutions and adjacent transpositions.
4. Ambiguous dates trigger abstention unless decision invariance holds.
5. Incompatible cross-document entities and dependent corroboration loops are blocked.
6. The 10 Decision Safety Invariants hold unconditionally.

---

## 2. Adversarial Test Cases Summary

| Case ID | Family | Target Subsystem | Input Challenge | Expected Invariant Behavior | Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| `ADV-ID-01` | A | Verhoeff Aadhaar | Single-digit corruption `...12` vs `...11` | Checksum invalid, verify blocked | **PASS** |
| `ADV-ID-02` | A | Verhoeff Aadhaar | Adjacent transposition `...101` vs `...011` | Checksum invalid, verify blocked | **PASS** |
| `ADV-ID-03` | A | IFSC Validation | `SBINO001234` (O for 0 at idx 4) | Abstain with reason `O vs 0 confusable` | **PASS** |
| `ADV-ID-04` | A | PAN Validation | `ABCD01234F` (0 in 5th alpha pos) | Abstain with reason `ambiguity in PAN` | **PASS** |
| `ADV-ID-05` | A | Identifier Token | Quotes & punctuation bleed `'BARB0BHUBAN,':` | Cleaned token extracted | **PASS** |
| `ADV-DATE-01` | B | Date Normalization | `29/02/2024` (leap year) | Normalized to `2024-02-29` | **PASS** |
| `ADV-DATE-02` | B | Date Normalization | `29/02/2025` (non-leap year) | Calendar validation rejects | **PASS** |
| `ADV-DATE-03` | B | Date Normalization | `31/04/2024` (April 31st) | Calendar validation rejects | **PASS** |
| `ADV-DATE-04` | B | Date Normalization | `05/06/2024` (ambiguous slash) | 2 candidate interpretations detected | **PASS** |
| `ADV-DATE-05` | B | Date Expiration Invariant | Ambiguous issue date within validity ceiling | Evaluates to Invariant PASS | **PASS** |
| `ADV-NUM-01` | C | Amount Normalizer | Indian commas `Rs. 2,50,000.00` | Normalized to `250000.0` | **PASS** |
| `ADV-NUM-02` | C | Amount Normalizer | Textual `2.5 Lakhs` | Normalized to `250000.0` | **PASS** |
| `ADV-NUM-03` | C | Income Ceiling | Boundary match `250000.00` | Grade `EXACT`, status `PASS` | **PASS** |
| `ADV-NUM-04` | C | Semantic Equivalence | `1 MT` vs `1000 KG` | Physical equiv TRUE, Normalized equiv | **PASS** |
| `ADV-SLOT-01` | D | Slot Validator | Caste cert in Income slot | `RULE-SLOT-01` emitted, quarantined | **PASS** |
| `ADV-XDOC-01` | E | Entity Resolution | Same name, conflicting DOB | Entity match rejected | **PASS** |
| `ADV-XDOC-02` | E | Corroboration Indep | Shared page / image hash | Marked `DUPLICATE` / `DEPENDENT` | **PASS** |
| `ADV-XDOC-03` | E | Semantic Equivalence | Identical date string cross-doc | Evaluates to `EQUIVALENT_NORMALIZED` | **PASS** |
| `ADV-SCHEME-01` | F | Scheme Relaxations | SC/ST category pass-only policy | Preserves `PASS_ONLY` policy | **PASS** |
| `ADV-CONF-01` | G & H | Weakest Evidence | Raw SATISFIED + UNCERTAIN evidence | Forces outcome to `REVIEW` | **PASS** |
| `ADV-SAFE-01` | H | Safety Layer | Missing mandatory document | Fails closed to `MISSING` | **PASS** |
| `ADV-SAFE-02` | H | Safety Layer | General applicant category exemption | Resolves to `NOT_APPLICABLE` | **PASS** |

---

## 3. Test Suite Execution & Output

```
collected 19 items
tests/test_loop33_rule_adversarial.py ................... [100%]
======================== 19 passed, 1 warning in 1.51s ========================
```

All 19 adversarial cases passed unconditionally.
