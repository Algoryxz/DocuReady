# Loop 28 Cross-Document Contradiction Corpus Specification

## 1. Corpus Summary
- **Corpus File**: `research/loop28/corpus/cross_document_corpus.json`
- **Locked Blind SHA-256**: `9199efdc6016802b6d865c76fdc30d92fb135100d27ed3474926e7a547444562`
- **Total Multi-Document Packets**: 36
- **Total Cross-Document Claims Evaluated**: 92
- **Partitions**:
  - `DEV`: 10 packets
  - `CAL`: 8 packets
  - `BLIND`: 12 packets (Frozen and Hash-Locked)
  - `CHALL`: 6 packets (Adversarial Stress Cohort)

## 2. Coverage of Mandatory Evaluation Conditions
The corpus covers all 20 required conditions:
1. `COND_01_EXACT_AGREEMENT`: Multi-source application and passbook agreement.
2. `COND_02_NUMERIC_MISMATCH`: Salary slip vs tax summary gross amount conflict.
3. `COND_03_DECIMAL_MISMATCH`: Lab report decimal shift under micro-font OCR (5.60 vs 56.00).
4. `COND_04_DATE_MISMATCH`: Invoice delivery date vs receipt acknowledgement date conflict.
5. `COND_05_CURRENCY_MISMATCH`: USD vs INR invoice valuation conflict.
6. `COND_06_UNIT_MISMATCH`: Metric Tonnes (MT) vs Kilograms (KG) weight discrepancy.
7. `COND_07_DISTINCT_ENTITIES`: Two family members sharing parent/address in single packet.
8. `COND_08_SHARED_IDENTIFIERS`: Same ID belonging to unrelated records.
9. `COND_09_MISSING_ATTACHMENT`: Claim asserted without mandatory supporting certificate.
10. `COND_10_DUPLICATE_DOCUMENTS`: Identical file uploaded twice to simulate corroboration.
11. `COND_11_TABLE_ROW_CONTRADICTIONS`: Tabular item breakdown mismatch across invoices.
12. `COND_12_DOCUMENT_VERSIONS`: Draft Purchase Order (Rev A) vs Final Approved (Rev B).
13. `COND_13_ILLEGIBLE_EVIDENCE`: Required supporting evidence below confidence floor.
14. `COND_14_CONFLICTING_SOURCES`: Inter-bank transfer vs beneficiary receipt discrepancy.
15. `COND_15_REPEATED_OCR_ERROR`: Template-correlated O/0 misread across repeated forms.
16. `COND_16_PARTIAL_IDENTIFIER_MATCHES`: Truncated bank account number suffix matching.
17. `COND_17_MULTIPLE_ENTITIES`: Corporate subsidiaries in unified group submission.
18. `COND_18_MISSING_CRITICAL_FIELDS`: Omitted mandatory slot in application form.
19. `COND_19_WRONG_DOCUMENT`: Unrelated utility bill uploaded instead of domicile proof.
20. `COND_20_INCONSISTENT_CHRONOLOGY`: Delivery date precedes purchase order creation date.
