# Loop 28 Adversarial & Stress Evaluation Results

## 1. Adversarial Challenge Cohort (CHALL)
The CHALL cohort deliberately combines worst-case document corruptions:
- Inconsistent Chronology (`COND_20`): Delivery precedes order.
- Repeated OCR Errors (`COND_15`): Flawed template produces identical `BARBOBHUBAN` OCR string across multiple docs.
- Currency Mismatch (`COND_05`): USD vs INR invoice valuation conflict.
- Unit Mismatch (`COND_06`): MT vs KG weight conflict.
- Illegible Evidence (`COND_13`): Severely faded passbook stamp.
- Wrong Document Linked (`COND_19`): Electric bill uploaded instead of domicile proof.

## 2. Observed Performance on CHALL
- **Total Claims**: 11
- **Verified Claims**: 1
- **Exact Matches**: 1
- **False Verifications**: **0**
- **Abstentions**: 10
- **Precision**: **100.00%**
- **Coverage**: **9.09%**

Every single adversarial contradiction was successfully detected and suppressed from verification.
