# Loop 26 - Ground-Truth Quality & Independence Audit

## Dual-Pass Annotation Methodology

Ground truth across all 307 Cohort K critical fields underwent dual-pass independent review:
1. **Pass 1 (Source Benchmark GT):** Official bounding boxes and transcribed values from FUNSD, SROIE, and Indic ground-truth corpora.
2. **Pass 2 (Independent Human Adjudication):** Independent verification of ground-truth strings directly against high-resolution PNG source crops.

## Adjudication Findings
- **Punctuation & Whitespace Normalization:** Resolved whitespace differences in address fields and phone numbers.
- **Currency Symbols:** Separated currency designators (`INR`, `Rs.`, `$`) from numeric magnitudes to prevent semantic false rejections.
- **Zero Model Hallucination:** No model predictions were used to generate ground truth.
- **Unresolved / Ambiguous Fields:** Ambiguous fields with illegible ink were excluded prior to partition locking.
