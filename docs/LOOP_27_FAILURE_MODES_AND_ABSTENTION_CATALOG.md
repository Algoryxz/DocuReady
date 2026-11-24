# DOCUREADY LOOP 27 — FAILURE MODES & ABSTENTION CATALOG
## Classification, Taxonomy & Distribution of Evidence-Guided Abstentions

**Loop:** 27  
**Total Evaluated Fields ($T$):** 791  
**Total Abstentions ($A$):** 447 (56.51% of evaluated fields)  
**Total False Verifications ($F$):** 0 (0.00%)  

---

### 1. The 12-Category Abstention Taxonomy
In high-stakes document verification, abstention is not a failure; it is a primary safety guarantee. DocuReady enforces 12 distinct abstention categories:

| Taxonomy Category | Empirical Count | % of Abstentions | Description & Trigger Conditions |
|---|---|---|---|
| **Identifier character ambiguity** | 18 | 4.0% | Glyph confusable (e.g. `O/0` in IFSC pos 4, `I/1` in numeric account) |
| **Identifier syntax violation** | 12 | 2.7% | Candidate violates formal grammar (length, structural regex, check digit) |
| **Ground-truth ambiguity** | 15 | 3.4% | Chronological boundary exceeded (e.g. year > 2026) or ambiguous layout |
| **Spatial ambiguity** | 32 | 7.2% | Candidate spans column boundary or cell boundaries overlap |
| **Header ambiguity** | 24 | 5.4% | Column header text contradicts expected semantic pattern |
| **Multi-token bleed** | 28 | 6.3% | Multiple whitespace tokens inside numeric or identifier cell |
| **Decimal/integer ambiguity** | 14 | 3.1% | Conflicting decimal morphology or micro-font degradation |
| **Missing evidence** | 215 | 48.1% | No candidate cell identified or empty table region |
| **Confidence floor** | 68 | 15.2% | Raw OCR confidence below operating threshold $T^*=70.0$ |
| **Unsupported font** | 11 | 2.5% | Severe degradation, low contrast, or non-Latin glyph noise |
| **Cross-doc conflict** | 4 | 0.9% | Disagreement between corroborating pages |
| **Processing failure** | 0 | 0.0% | Zero unhandled exceptions or runtime crashes |
| **Other** | 6 | 1.3% | Miscellaneous edge cases |
| **Total** | **447** | **100.0%** | **Mutually Exclusive Accounting Verified** |

---

### 2. Detailed Root-Cause Case Studies

#### Case 1: IFSC 5th Character Substitution
- **Trigger**: OCR token `BARBOBHUBAN` with 93.0% confidence.
- **Handling**: `validate_identifier_syntax_and_ambiguity` identifies category `IFSC_CODE`. Index 4 is character `'O'`. Matches confusable regex `^[A-Z]{4}[O0][A-Z0-9]{6}$`.
- **Classification**: `Identifier character ambiguity`.
- **Action**: Decision set to `ABSTAIN`. False verification completely prevented.

#### Case 2: Future Date Beyond Document Horizon
- **Trigger**: OCR token `10/10/2028,` with 89.5% confidence.
- **Handling**: Sanitizer strips trailing comma to `10/10/2028`. Date validator checks year against chronological document horizon ($1900 \le y \le 2026$). Year $2028$ exceeds horizon.
- **Classification**: `Ground-truth ambiguity`.
- **Action**: Decision set to `ABSTAIN`.
