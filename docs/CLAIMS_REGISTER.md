# DocuReady — Public Claims Register

> [!NOTE]
> **DocuReady 2.0 Audit Addendum (28 Nov 2026):** Loop 0 forensics ([docs/07-DOCUREADY-2.0/BASELINE_AUDIT.md](07-DOCUREADY-2.0/BASELINE_AUDIT.md)) flagged two remaining public-surface items for remediation in 2.0: (1) `apps/desktop/src/renderer/main.tsx:486` still displays `"100% Offline · Local Workspace"` (reconcile to `"Local Processing · Ephemeral Workspace"`), and (2) `site/index.html` still describes the local app as `"the Python/Streamlit application"` and links to `#installation--setup`.

**Version:** 1.0.0  
**Authority:** Deeptiman (Product Owner & Architecture Lead)  
**Governance Task:** T1.1 / WS1 (Trust & Compliance)  
**Last Audited:** 2026-11-15  

---

## 1. Governance & Purpose

This register catalogues and audits all public-facing claims made across DocuReady's public surface (including `README.md`, documentation, code docstrings, CLI help texts, and Streamlit user interface). 

Under the DocuReady Trust & Compliance Framework (G1), every claim must be classified into one of three dispositions:
- **Verified:** Fully substantiated by automated regression tests, statutory citations, or reproducible local execution contracts.
- **Qualified:** Legitimate technical or operational capability that must be bounded with explicit conditions, statutory scope, or synthetic dataset disclosures.
- **Removed:** Any ungrounded, hyperbolic, or overreaching statement that exceeds demonstrated system capabilities or asserts unverified field outcomes.

---

## 2. Claims Catalog & Audit Matrix (CLM-001 to CLM-011)

| Claim ID | Claimed Statement / Feature | Location | Classification | Evidence / Qualification Scope | Audit Date |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CLM-001** | `Privacy: 100% Local \| Zero Telemetry` | `README.md` badge | **Qualified** | Re-labeled to `Privacy: Local Execution \| No Telemetry (Verified)`. Substantively verified via `tests/contract/test_no_network.py` socket-level interception prohibiting outbound HTTP/HTTPS/DNS requests during pipeline execution. | 2026-11-15 |
| **CLM-002** | `Statutory Rules Engine` | `README.md` diagram & headings | **Qualified** | Re-labeled to `Document Consistency & Scheme Requirement Rules Engine (with verified statutory citations where available)`. As documented in `docs/CITATION_AUDIT.md`, 5 rules possess verified primary statutory citations (MoSJE, CBSE, RBI), while 8 rules function as operational heuristics. | 2026-11-15 |
| **CLM-003** | "Across government welfare portals, millions of students and citizens apply annually... millions face rejection" | `README.md` ("The Problem") | **Removed / Qualified** | Removed ungrounded macro-statistical assertions regarding nationwide applicant counts. Rephrased to focus objectively on verified clerical friction points (name spelling variations, DOB mismatches, scan degradation). | 2026-11-15 |
| **CLM-004** | "Revenue or Income Certificates submitted past their statutory validity (typically one financial year under state revenue rules)" | `README.md` ("The Problem" & Rules Table) | **Qualified** | Clarified that income certificate validity periods vary by state revenue department and issuing authority. One financial year is an operational heuristic evaluated by `RULE-EXP-01`, not a uniform national statutory mandate. | 2026-11-15 |
| **CLM-005** | `Deterministic & Explainable` | `README.md` ("Key Capabilities") | **Verified** | Core audit pipeline uses deterministic rule functions, Verhoeff checksum calculation, regex patterns, and deterministic date normalizers. Zero stochastic LLMs or generative AI in the decision path. Verified in `tests/test_validator.py` and `tests/test_normalizer.py`. | 2026-11-15 |
| **CLM-006** | `Visual Bounding Box Provenance` | `README.md` ("Key Capabilities") | **Verified** | All extracted candidate facts retain physical page numbers and bounding box coordinates (`[x0, y0, x1, y1]`). Verified by vector extraction tests in `tests/test_extractor.py` and UI visual overlays. | 2026-11-15 |
| **CLM-007** | `Calibrated Evidence Safety Layer` | `README.md` ("Calibration & Safety Layer") | **Verified** | 9-feature logistic regression calibrator scores evidence confidence ($P < 0.60 \rightarrow \text{UNCERTAIN}$) and automatically downgrades unproven rule violations to `NEEDS REVIEW`. Verified in `tests/test_evidence_calibration.py` and `tests/test_safety_layer.py`. | 2026-11-15 |
| **CLM-008** | `Interactive Single-Document Replacement (<1s re-audit)` | `README.md` ("Key Capabilities") | **Verified** | Single-document in-memory replacement and re-audit workflow validated in `tests/test_replacement_rerun.py`, executing sub-second audit recalculations without re-processing unaffected documents. | 2026-11-15 |
| **CLM-009** | Benchmark: 100.0% Exact Match on Standard 8 Synthetic Packets | `README.md` ("Verified Benchmarks") | **Qualified** | Performance is explicitly qualified as synthetic benchmark test performance on reference hardware across 48 synthetic PDFs; does not represent live portal field acceptance guarantees. | 2026-11-15 |
| **CLM-010** | Benchmark: 91.7% on Degraded Scans / 93.0% on Held-Out 100 | `README.md` ("Verified Benchmarks") | **Qualified** | Evaluated against controlled synthetic degradation datasets (`synthetic_data/realistic_corpus_60` and `synthetic_data/held_out_100`). Explicit disclaimer added that benchmark figures cite synthetic test datasets. | 2026-11-15 |
| **CLM-011** | `Pre-Submission Advisory Only / Not an Official Government Portal` | `README.md` ("Known Boundaries & Limitations") | **Verified** | Prominently displayed advisory disclaimer stating DocuReady is an assistive demographic linter and does not guarantee government approval or legal entitlement. | 2026-11-15 |

---

## 3. Prohibited Public Phrases

The following phrases are strictly prohibited across all public surfaces, documentation, marketing assets, and test fixtures:
1. `guaranteed approval`
2. `universal validity`
3. `100% accurate`
4. `statutory guarantee`
5. `official government approval`
6. `government-certified`

Automated regression coverage in `tests/contract/test_claims.py` enforces zero occurrences of these banned phrases across repository markdown files.
