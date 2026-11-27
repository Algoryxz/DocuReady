# LOOP 19: Deep Audit of Loop 18 Critical-Field Metrics & Substring Fallacy

## 1. Executive Summary: The Substring Presence Fallacy

A primary directive of Loop 19 is an adversarial audit of Loop 18's reported **67/67 exact critical-field matches (100.0%)** alongside its **73.3% adversarial stress match rate**.

Our line-by-line inspection of the evaluation harness (`evaluate_critical_fields` in `research/loop18/benchmark/run_strategy_benchmark.py`) uncovered a foundational methodological limitation:
> **The Substring Fallacy**: Loop 18 evaluated critical-field accuracy solely by checking whether the expected target string existed anywhere within the full-page text hypothesis (`norm_val in norm_hyp`).

In an administrative verification system, **mere presence of a string on a page does not prove correct evidence association**:
- If an income amount `180000` is printed under applicant "Rohit Verma", but OCR groups it with co-applicant "Sunil Verma", a full-page substring search reports a "100% Match".
- In a two-column fiscal ledger (`STRESS_03`), if `Subtotal B: 194300` is parsed into the line `Property Tax: 154000 Subtotal B: 194300`, the substring check marks `194300` as PASS, even though its column and field association are spatially corrupted!

---

## 2. Answers to the 12 Governance Audit Questions

| Audit Question | Verified Finding & Evidence | Impact on Reliability |
| :--- | :--- | :--- |
| **1. Exact fields in 67-field denominator?** | 13 contracts across 25 documents: `DOC_CTRL_01` (4), `DOC_EXT_02` (6), `DOC_EXT_03` (6), `DOC_EXT_04` (7), `DOC_EXT_05` (4), `DOC_EXT_06` (6), `DOC_EXT_07` (6), `DOC_EXT_08` (5), `DOC_EXT_09` (4), `DOC_MIX_01` (5), `DOC_MULTI_04` (5), `CHALLENGE_03` (5), `CHALLENGE_06` (4). | Complete and accounted for. |
| **2. Independent from 15 stress fields?** | Yes. The 15 stress fields originate from `STRESS_01` through `STRESS_04` in `research/loop18/stress_fixtures/`. | Cleanly isolated populations. |
| **3. Are any fields missing from evaluation?** | No. All 67 annotated fields were evaluated across all 4 OCR strategies. | Zero omission. |
| **4. Are failed fields excluded from metrics?** | No. In `STRATEGY_PAGE_ROUTING`, 4 failed fields were properly counted (`63/67 = 94.03%`). | Transparent reporting. |
| **5. Does normalization hide true errors?** | Partially. Direct substring match was tested first; if not found, whitespace and punctuation stripping were applied. While helpful for minor spacing (e.g. `18 / 08 / 2026`), it masked hyphenation splits. | Identified for refinement. |
| **6. Are numeric comparisons genuinely exact?** | The numeric check compares extracted digit strings (`val_digits in hyp_digits`). | Digits must match exactly in order. |
| **7. Field CER calculation basis?** | Computed via a sliding window of length $|E|$ across the full hypothesis text to find $\min \text{Levenshtein}$. | Measures symbol presence, not field binding. |
| **8. Are row/column associations included?** | **NO.** The Loop 18 benchmark had zero concept of grid rows or columns. | **Critical Defect identified for Loop 19.** |
| **9. Does a field from the wrong cell count as correct?** | **YES.** If a value appeared anywhere in the text, it counted as matched. | **Core vulnerability of Loop 18.** |
| **10. Are incorrect field assignments captured?** | No. A value assigned to the wrong header is not caught by page-level substring matching. | Downstream verification risk. |
| **11. Population consistency for CER and Exact Match?** | Yes, both computed over the exact same 67-field set. | Internally consistent. |
| **12. Stratification by document type?** | Yes, stratified into `PRIMARY_VALIDATION` (58 fields) and `SEALED_CHALLENGE` (9 fields). | Clean stratification. |

---

## 3. The Mandate for Loop 19

Loop 19 must move DocuReady from **Text Extraction** to **Spatial Evidence Association**:
1. Every critical field must be bound to its **spatial coordinates** (`bbox`), **row index**, and **column header**.
2. A field is only marked as a valid match if:
   $$\text{Valid Match} = (\text{Value Match}) \land (\text{Correct Column/Header Binding}) \land (\text{Correct Row Context})$$
3. When spatial association is ambiguous (e.g. text bridging two columns), the system must **abstain** or flag uncertainty rather than emitting a falsely confident extraction.
