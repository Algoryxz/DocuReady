# DocuReady — Product Scope & Non-Goals

## Ownership & Contribution Responsibilities

| Role | Assignee | Primary Scope & Focus |
|---|---|---|
| **Primary Owner** | **Deeptiman** (Product Owner & Integration Lead) | MVP scope boundaries, non-goals, exclusion rationale, statutory authority disclaimers |
| **Supporting Contributor** | **Akriti** (Platform, Privacy & Delivery Lead) | Technical boundary enforcement (zero-network, local sandboxing, no cloud dependencies) |
| **Supporting Contributor** | **Susmita** (Domain Rules & Evaluation Lead) | Scope of statutory rules, non-authenticity boundary, document slot coverage |

### Detailed Responsibilities & Deliverables
- **Primary Owner (Deeptiman)**:
  - Define and protect in-scope vs. out-of-scope boundaries to prevent mission creep and over-claiming.
  - Explicitly document statutory non-goals (no Aadhaar biometric checks, no live bank balance lookups, no forensic paper fraud detection, no final welfare benefit approvals).
  - Prioritize core MVP features against gate milestones.
- **Platform Contributor (Akriti)**:
  - Enforce technical boundaries: ensure no-network guarantees and local-only compute remain inviolable non-functional requirements.
- **Domain Contributor (Susmita)**:
  - Clearly articulate the boundary between document consistency linting and official legal eligibility verification.

### Coordination & Review Gates
- Proposing new features into MVP scope requires unanimous consensus and Deeptiman's formal acceptance.
- Any change affecting technical boundaries requires Akriti's sign-off; statutory boundary changes require Susmita's review.
- Governed by [TEAM_RESPONSIBILITIES.md](../TEAM_RESPONSIBILITIES.md).

---

## 1. What DocuReady IS (In-Scope)

1. **Pre-Submission Client-Side Linter**:
   - Inspects documents on the user's device prior to portal submission.
   - Operates completely offline without sending document bytes to third-party cloud APIs.
2. **Cross-Document Entity Consistency Verification**:
   - Compares extracted demographic and financial facts across multi-document packets.
   - Evaluates applicant name variants, DOB, income declarations, certificate reference numbers, and bank account numbers.
3. **Deterministic Statutory Rules Engine**:
   - Evaluates scheme-specific income ceilings, state domicile mandates, certificate expiration periods, and category reservation rules citing official legal sources.
4. **Explainable Provenance**:
   - Links every finding to the exact source document, page number, bounding box coordinates, and extracted text snippet.
5. **Epistemic Evidence State Tracking**:
   - Distinguishes between native vector text (`VERIFIED_TEXT`), high-confidence OCR (`OCR_EXTRACTED`), ambiguous dates (`AMBIGUOUS`), and degraded scans (`LOW_CONFIDENCE` / `UNREADABLE`).
6. **Decision Safety Firewall**:
   - Strictly enforces non-rejection principles: uncertain evidence downgrades to human `REVIEW`, never automatic `FAIL`.

---

## 2. What DocuReady IS NOT (Out-of-Scope / Explicit Non-Goals)

To prevent misunderstandings regarding official authority, DocuReady explicitly declares the following non-goals:

| Capability | Out of Scope Reason | Proper Authority |
|---|---|---|
| **Aadhaar Biometric Verification** | DocuReady does not connect to UIDAI CIDR or perform iris/fingerprint authentication. | Official UIDAI Authentication User Agencies (AUA). |
| **Bank Balance & Ownership Lookup** | DocuReady checks IFSC structure and passbook account number consistency; it does not query NPCI APB/e-KYC live balances. | Scheduled Commercial Banks / RBI DBT Gateway. |
| **Forensic Counterfeit Detection** | DocuReady does not verify physical paper fibers, invisible UV watermarks, or cryptographic digital signatures on revenue seals. | State Forensic Science Laboratories & e-District Portals. |
| **Final Welfare Benefit Approval** | DocuReady is an advisory pre-submission pre-checker. Passing DocuReady does NOT guarantee government scholarship disbursement. | District Welfare Officers / Sanctioning Authorities. |
| **Official Submission Portal** | DocuReady does not submit applications on behalf of citizens or store government credentials. | National Scholarship Portal (NSP) / State Portals. |
