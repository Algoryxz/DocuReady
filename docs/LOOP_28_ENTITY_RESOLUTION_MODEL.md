# Loop 28 Entity Identity & Disambiguation Model

## 1. Core Principles of Entity Identity
In real-world verification packets (scholarships, loan applications, procurement, legal filings), documents frequently mention multiple persons or corporate entities.
DocuReady enforces four strict safety invariants:
1. **Same Name $\ne$ Same Entity**: Two individuals sharing a common name (e.g., "Rohit Verma") but with distinct dates of birth, father names, or tax IDs are strictly distinct.
2. **Shared Address $\ne$ Same Entity**: Family members (e.g., two brothers) sharing an address and parent name cannot have their individual claims (e.g., academic scores, incomes) merged.
3. **Shared Amount $\ne$ Same Entity**: Unrelated applicants paying identical application fees must not be conflated as corroborating evidence.
4. **Anchor-Corroborated Spelling Variations**: Minor spelling variations (e.g., "Rohit Verma" vs "Rohit Varma") are resolved if and only if corroborated by an exact anchor attribute (DOB, PAN, or Father Name).

## 2. Multi-Attribute Resolution Algorithm
```
Input: Target Entity E_tgt, Claim Entity E_claim
1. Check Strong Identifiers (tax_id, national_id, account_number):
   If both present and id1 != id2 -> REJECT (ENTITY_MISMATCH)
2. Check Date of Birth:
   If both present and dob1 != dob2 -> REJECT (ENTITY_MISMATCH)
3. Check Parent/Guardian Name:
   If both present and similarity(g1, g2) < 0.80 -> REJECT (ENTITY_MISMATCH)
4. Check Canonical Name:
   If exact normalized match -> ACCEPT (MATCH)
   If similarity(n1, n2) >= 0.85 and has_anchor(DOB, Parent, Address) -> ACCEPT (RESOLVED_VARIATION)
   Else -> REJECT (ENTITY_MISMATCH)
```
