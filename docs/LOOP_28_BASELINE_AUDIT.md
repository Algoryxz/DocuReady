# Loop 28 Baseline Audit: Cross-Document Verification & Multi-Source Integrity

## 1. Executive Summary & Starting Baseline
DocuReady Loop 28 establishes reliable, evidence-grounded cross-document verification with explicit entity identity resolution, factual contradiction detection, evidence independence tracking, and risk-calibrated abstention.

- **Research Branch**: `loop-28-cross-document-verification-reliability`
- **Starting Base Commit**: `511ba824ecac000180489cd2e92f1cc634fe7098` (Loop 27 milestone)
- **Protected Competition Release**: Loop 10 (`bdc403a`) — strictly read-only, bit-exact verified.
- **Operating Policy Baseline**: $T^* = 70.0$, $T_{\text{fuzzy}} = 75.0$.

## 2. Inherited Loop 27 Performance
Loop 27 delivered single-document identifier validation (IFSC confusable detection, Aadhaar Verhoeff check-digit enforcement, GSTIN checksum verification) and reported 0 false verifications on its 791-field aggregate benchmark.
However, Loop 27 exposed critical boundaries:
1. **Adversarial Identifier Ablation**: Reported 5 false verifications among 16 claims (100% were PAN 10th-character mutations where single-document syntax was valid).
2. **Cross-Document Isolation**: Single-document extraction could not cross-reference corroborating documents or detect contradictions across packets.
3. **Statistical Accounting Discrepancies**: Loop 26 vs Loop 27 field counts required formal reconciliation.

## 3. Scope of Loop 28
Loop 28 addresses multi-document packets, cross-referencing identity across disparate documents, detecting duplicate scans, catching factual contradictions (amounts, dates, decimals, currencies, units), and strictly avoiding false verifications.
