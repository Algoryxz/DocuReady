# Loop 28 Cross-Document Verification Policy

## 1. Operating Rules & Thresholds
- **Primary Operating Threshold**: $T^* = 70.0$
- **Fuzzy / Confusable Threshold**: $T_{\text{fuzzy}} = 75.0$
- **Corroborating Anchor Sim Threshold**: $0.85$

## 2. Verification Decision Flow
```mermaid
flowchart TD
    Start[Packet Field Evaluation] --> CheckMissing{Required Doc Types Present?}
    CheckMissing -- No --> MissingOut[MISSING_EVIDENCE -> ABSTAIN]
    CheckMissing -- Yes --> CheckLegible{Supporting Evidence Legible?}
    CheckLegible -- No --> AbstainIllegible[ABSTAIN]
    CheckLegible -- Yes --> FilterEntities{Entity Resolution Match?}
    FilterEntities -- None Match --> EntityOut[ENTITY_AMBIGUOUS -> ABSTAIN]
    FilterEntities -- Valid Matches --> CheckChrono{Chronology Consistent?}
    CheckChrono -- Anachronistic --> ContradictionOut[CONTRADICTION_DETECTED -> ABSTAIN]
    CheckChrono -- Valid --> CheckCurrencies{Currency / Unit Conflict?}
    CheckCurrencies -- Discrepancy --> ContradictionOut
    CheckCurrencies -- Harmonious --> CheckValues{Multiple Distinct Values?}
    CheckValues -- Conflicting Values --> ContradictionOut
    CheckValues -- Single Value --> CheckConfidence{Max Confidence >= T*?}
    CheckConfidence -- Below T* --> AbstainLowConf[ABSTAIN]
    CheckConfidence -- Meets T* --> VerifyOut[VERIFIED]
```
