# Loop 26 - Limitations & Honest Failure Modes

## Documented Real-World Limitations
1. **Alphanumeric ID Single-Pass OCR Confusion:** On degraded scanned documents without check digits (such as Indian Bank IFSC codes), `O` vs `0` substitutions can slip past high confidence thresholds.
2. **Ultra-Low Contrast Thermal Receipts:** Faded thermal receipts with global contrast < 15% fall below the T=70.0 floor and abstain by design.
3. **Scope Clarification:** DocuReady verifies extracted evidence and spatial association; it does NOT verify document authenticity or detect counterfeit physical paper.
