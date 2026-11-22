# LOOP 20: Evidence-Based Abstention & Selective Reliability Report

## 1. Selective Prediction Principles

DocuReady applies conformal selective classification: when epistemic uncertainty is elevated, the system **abstains** from making a statutory determination and routes the field to human review.

The system refuses to verify a critical field when:
1. **Multiple Matching Rows**: An anchor key matches more than one row without disambiguating secondary context (e.g. repeated account number in `CHALL_04`).
2. **Cross-Column Bounding Box Bleed**: Cell tokens cross adjacent column boundaries by $>20\text{px}$.
3. **Empty Cell Value Bleed**: A cell contains zero word tokens; the system preserves `value = ""` rather than inheriting adjacent numbers.
4. **Syntactic Incompatibility**: The extracted string fails basic semantic type constraints (e.g. non-numeric string for an `amount` field, or missing day/month for a `date` field).
5. **Label Echo Trap**: The extracted string is identical to the queried column label or row header pattern.
6. **Sub-Threshold OCR Confidence**: Calibrated token confidence is below $\tau_{\text{abstain}} = 30.0\%$.

---

## 2. Empirical Abstention Metrics

In the Loop 20 benchmark:
- **Total Eligible Fields**: 65
- **System Abstentions**: 7 fields (Abstention Rate: **10.77%**)
- **Abstention Breakdown**:
  - `PASS_EMPTY_CORRECT`: 3 fields (Empty cells correctly preserved without spurious value inheritance in `VAL_06`, `CHALL_05`, `CHALL_06`).
  - `ABSTAIN_AMBIGUOUS`: 1 field (`BLIND_09_TRANSPORT_FREIGHT_MANIFEST`: value was `"In Transit"` rather than numeric freight amount).
  - `FAIL_NOT_EXTRACTED`: 3 fields (No valid candidate cell identified).
- **False Abstentions on Valid Fields**: 3 fields (4.62% of corpus).
- **Abstention Impact on Precision**:
  Without abstention, Critical Field Precision drops to **83.08%**; with abstention gating, Precision increases to **88.52%**.
