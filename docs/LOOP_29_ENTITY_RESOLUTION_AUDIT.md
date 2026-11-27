# Loop 29 Entity Resolution Audit & Safety Rules

## 1. Safety Rules Enforced
1. **Father Name Invariance**: Father name alone never establishes identity.
2. **Address Invariance**: Shared address never establishes identity.
3. **Amount Invariance**: Matching fee amounts never establish identity.
4. **Spelling Invariance**: Spelling variation resolved ONLY with corroborating anchor (DOB, PAN, parent).
5. **Conflict Rejection**: Conflicting DOB or PAN strictly rejects entity matching.
