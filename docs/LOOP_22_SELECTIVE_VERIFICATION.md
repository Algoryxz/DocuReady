# Loop 22 — Selective Verification & Risk-Calibrated Abstention

**Core Policy:** Trustworthy Verification Over Blind Coverage  
**Principle:** A False Verification carries a substantially higher penalty than an Abstention.

---

## 1. Decision States & Rationale

DocuReady enforces a 4-state outcome policy for critical fields:
1. **`VERIFIED` (PASS_SPATIAL_EXACT):** High-confidence, syntactically valid, spatially verified candidate with consistent column and row headers.
2. **`ABSTAIN_FILTERED`:** High ambiguity, low confidence, multi-token gutter bleed, or column header semantic contradiction.
3. **`PASS_EMPTY_CORRECT`:** Ground truth expects an empty cell, and the cell is confirmed empty without spurious value inheritance.
4. **`FAIL_MISMATCH` / `FAIL_WRONG_COORDINATE`:** False verification where unflagged evidence was asserted incorrectly.

---

## 2. Risk-Calibrated Abstention Triggers

| Trigger Condition | Target Failure Mode | Implemented Reason Code |
| :--- | :--- | :--- |
| **Confidence $< 60.0$** | Prevents verifying degraded optical noise | `Low OCR confidence (< 60.0)` |
| **Multi-Token Numeric** | Prevents verifying cell gutter bridging | `Multiple whitespace-separated tokens detected` |
| **Stray Syntax Glyphs** | Catches broken non-alphanumeric OCR | `Stray punctuation or non-alphanumeric syntax garble` |
| **Header Contradiction** | Prevents wrong-column capture | `Column header contradicts expected field semantic` |
| **Label Echo** | Prevents label name being returned as value | `Label-echo rejected` |
| **Multiple Row Collision** | Prevents ambiguous row association | `Ambiguous cell boundaries or candidate collision` |

---

## 3. Impact on Trust and Reliability

In financial, audit, and legal document processing, an erroneous verification is catastrophic, leading to incorrect disbursements, regulatory fines, or compliance failure. An abstention, by contrast, transparently flags uncertainty and requests human review.

By abstaining on high-risk, ambiguous cells:
- False verifications plunged from **14 down to 3**.
- Verified-field precision surged from **80.82% up to 95.71%**.
- Coverage was maintained at a dependable **73.68%**.
