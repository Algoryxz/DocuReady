# DocuReady — Target Users & Stakeholders

## Ownership & Contribution Responsibilities

| Role | Assignee | Primary Scope & Focus |
|---|---|---|
| **Primary Owner** | **Deeptiman** (Product Owner & Integration Lead) | Persona definitions, user journey pain points, stakeholder value mapping, claims grounding |
| **Supporting Contributor** | **Susmita** (Domain Rules & Evaluation Lead) | CSC / Mo Seva Kendra operator workflows, field document realities, clerk verification patterns |
| **Supporting Contributor** | **Akriti** (Platform, Privacy & Delivery Lead) | Operational environment constraints (low-spec hardware, offline field laptops) |

### Detailed Responsibilities & Deliverables
- **Primary Owner (Deeptiman)**:
  - Maintain grounded, defensible user personas (Welfare Applicants, CSC Operators, Verification Clerks, Field NGOs).
  - Ensure demographic statements, applicant totals, and pain point descriptions are strictly grounded in credible public evidence.
  - Keep user persona expectations aligned with actual product UI and CLI deliverables.
- **Domain Contributor (Susmita)**:
  - Supply real-world domain nuances on how CSC operators and college verification clerks physically handle document packets and spot errors.
- **Platform Contributor (Akriti)**:
  - Ensure hardware and operational profiles (e.g. offline field laptops without persistent internet) match the system's runtime and deployment design.

### Coordination & Review Gates
- Personas must not be modified to justify speculative features without Deeptiman's approval.
- Governed by [TEAM_RESPONSIBILITIES.md](../TEAM_RESPONSIBILITIES.md) and the Claims Register (Task T1.1).

---

## 1. Primary User Personas

DocuReady serves four core user groups across the public welfare and educational application ecosystem:

### Persona 1: Scholarship & Welfare Applicants
- **Profile**: Rural or semi-urban students applying for post-matric scholarships, merit-cum-means awards, or government grants.
- **Pain Points**:
  - Anxiety over complex scheme eligibility rules.
  - Lack of legal clarity on certificate validity periods.
  - Fear of accidental disqualification due to spelling variations in regional names.
- **DocuReady Benefit**: A friendly, pre-submission readiness score (0-100) and step-by-step guidance showing which document to update before submission.

### Persona 2: Common Service Center (CSC) & Mo Seva Kendra Operators
- **Profile**: Village-level entrepreneurs assisting hundreds of rural citizens in submitting digital applications every season.
- **Pain Points**:
  - High volume of customer document packets with varying scan qualities.
  - High rejection rates reflecting poorly on the operator's service quality.
  - Time-consuming manual checking of dates, names, and account numbers across 6 physical documents.
- **DocuReady Benefit**: High-throughput offline batch auditing. An operator can scan and audit a complete packet in under 10 seconds, immediately advising the customer to obtain a fresh income certificate or provide a clearer passbook scan before submitting.

### Persona 3: College & Institute Verification Clerks
- **Profile**: Nodal scholarship officers at universities, ITIs, and polytechnics responsible for first-tier verification.
- **Pain Points**:
  - Backlog of thousands of applications arriving at the end of admission deadlines.
  - Tedious cross-referencing between university roll sheets, income certificates, and state scholarship portals.
- **DocuReady Benefit**: Standardized pre-submission readiness certificate exported as JSON or PDF, enabling instant clerical sign-off.

### Persona 4: Non-Governmental Organizations (NGOs) & Citizen Helpdesks
- **Profile**: Grassroots education foundations helping disadvantaged and tribal communities access government entitlements.
- **DocuReady Benefit**: 100% offline, privacy-first operation that can run on inexpensive field laptops in tribal areas without requiring continuous 4G/5G internet connectivity.
