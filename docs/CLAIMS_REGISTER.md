# DocuReady — Claims Register

**Current Status:** Active Governance Artifact (Task T1.1)  
**Authority:** Deeptiman (Product Owner & Architecture Lead)  
**Governing Standard:** `docs/ARCHITECTURE_V2.md` §2 (Product Positioning)

---

## 1. Purpose & Policy

DocuReady enforces strict honesty and evidence-based positioning in all documentation, code comments, UI labels, and public communications. 

Per `docs/ARCHITECTURE_V2.md` §2:
> **DocuReady is an applicant-side preparation aid.** It checks whether the documents in a packet are consistent with each other and with a scheme's published document requirements, and explains each defect and how to fix it. It does **not** decide eligibility, replace government verification, or guarantee acceptance.

### Dispositions:
- **`verified`**: Backed by authoritative primary documentation (official gazettes, scheme guidelines, or reproducible CI contracts).
- **`softened`**: Rephrased to describe technical capabilities or preparation assistance accurately without asserting absolute legal compliance, uncalibrated statistics, or guaranteed outcomes.
- **`removed`**: Deleted because the statement made an unsupported numerical, statutory, or outcome claim.

---

## 2. Complete Inventory of Public Claims

| ID | Claim Text | Location | Category | Disposition | Evidence / Source & Retrieval Date | Explanation & Action Taken |
|---|---|---|---|---|---|---|
| **CLM-001** | "Over 80 million students and citizens apply annually..." / "80M applicants" | `docs/03-RESEARCH/HACKNATION_IDEA_SELECTION.md` (L19) | Quantitative / Market Scope | **removed** | Unsupported estimate across aggregated disparate schemes; no single authoritative census. | Removed exact numerical count "80 million". Softened to "millions of students and citizens apply annually across diverse national and state schemes". |
| **CLM-002** | "...preventing the 18%–32% rejection rate caused by clerical discrepancies." | `PUBLICATION_REPORT.md` (L15), earlier README drafts | Quantitative / Performance | **removed** | Secondary survey estimate lacking unified primary government statistical grounding. | Removed the 18%–32% precision claim. Replaced with descriptive focus on clerical discrepancies causing preventable pre-submission delays. |
| **CLM-003** | "30–45% rejection rate..." | Historical bundle notes | Quantitative / Performance | **removed** | Contradicted CLM-002; neither figure had an authoritative gazette or ministry source. | Purged entirely. No unsourced percentage ranges permitted in public documentation. |
| **CLM-004** | "Every finding cites an enacted statutory clause or gazette." | `docs/03-RESEARCH/COMPETITOR_ANALYSIS.md` (L28), earlier drafts | Legal / Regulatory | **softened** | `packs/generic.demo/sources.yaml` (Task T1.5). Core rules cite published guidelines, but not all checks are enacted statutory clauses. | Softened to "findings cite published scheme guidelines and document requirements". Explicitly disclaims that all checks constitute primary statutory legislation. |
| **CLM-005** | "100% DPDP compliant" / "DPDP compliance" | `PUBLICATION_REPORT.md` (L125), `README.md` (L342) | Privacy / Compliance | **softened** | *Digital Personal Data Protection Act, 2023* (Gazette Notification 11 Aug 2023). Local execution supports data minimization, but legal compliance requires organizational deployment governance. | Softened from "100% compliant" to "architected with privacy-by-design principles informed by data protection frameworks such as India's DPDP Act 2023 (local processing, telemetry suppression, no network egress)". |
| **CLM-006** | "Zero Data Exfiltration" / "guaranteed zero exfiltration" | `docs/03-RESEARCH/COMPETITOR_ANALYSIS.md` (L26) | Security / Reliability | **softened** | Verified in code by `tests/contract/test_no_network.py` (tripwire blocking `socket.connect` and `socket.getaddrinfo`). | Softened from absolute guarantee to technical invariant: "Core pipeline operates under strict zero-network egress contracts enforced by automated socket tripwire tests." |
| **CLM-007** | "Deterministic & Explainable... Instant replacement in sub-second time." | `docs/01-PRODUCT/PRODUCT_OVERVIEW.md` (L52-53) | Performance / Determinism | **verified** | Verified via deterministic unit tests and synthetic benchmark harness (mean latency 0.38s native vector). | Preserved with clear qualification: verified under controlled synthetic benchmark environment. |
| **CLM-008** | Synthetic benchmark tables (100.0% Exact Match, 91.7%, 93.0%) | `README.md` (L355-360) | Accuracy / Evaluation | **verified** | Evaluated on synthetic corpora (`synthetic_data/` and synthetic degradation sets). | Retained with prominent mandatory label: **Synthetic Benchmark Dataset** and disclaimer stating results reflect controlled test conditions and do not guarantee field portal outcomes. |
| **CLM-009** | "Tests: 88 Passing" static badge | `README.md` (L10) | Testing / Verification | **removed** | Codebase advances dynamically (e.g. 99+ tests in G1); static badges diverge and mislead. | Removed static test count badge. Dynamic GitHub Actions CI badge retained as authoritative source of test execution state. |
| **CLM-010** | "Pre-Submission Advisory Only... NOT an official government portal, legal authority, or Aadhaar authentication service." | `README.md` (L367), `docs/01-PRODUCT/PRODUCT_SCOPE.md` (L56) | Legal / Scope Boundary | **verified** | Core product boundary defined by Product Owner Deeptiman. | Retained and emphasized across all user documentation and UI entrypoints. |
| **CLM-011** | Uncalibrated terminology: `MANUAL REVIEW` vs `NEEDS REVIEW` | `README.md` (L117, L125) | UX / Decision Safety | **softened** | `src/docuready/outcome/safety_layer.py` | Unified public reporting terminology to `NEEDS REVIEW / UNKNOWN` (or `MANUAL REVIEW`) systematically across documentation to prevent user confusion. |

---

## 3. Enforcement Policy & Contract Tests

All documentation additions are checked by `tests/contract/test_claims.py`:
- Banned phrases (e.g. `80 million`, `18–32%`, `30–45%`, `100% DPDP compliant`, `guaranteed zero exfiltration`, static test count badges) trigger test failure.
- Benchmark tables must include the synthetic qualification notice.
- Disclaimers regarding pre-submission advisory scope must be present in `README.md`.
