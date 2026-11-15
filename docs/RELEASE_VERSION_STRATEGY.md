# DocuReady — Semantic Release Version Strategy & Milestone Progression

**Document Version:** 1.1.0
**Date:** 15 November 2026
**Status:** Proposed — Pending Product Owner Ratification
**Repository:** `Algoryxz/DocuReady`
**Product Owner:** Deeptiman
**Technical Leads:** Antigravity, Akriti, Susmita

---

## 1. Context & Governance Objective

Historical documentation across DocuReady contained unresolved references to upcoming release version tags:
- `pyproject.toml` declares `version = "0.1.0"` with PyPI classifier `Development Status :: 3 - Alpha`.
- `docs/BACKLOG.md` §2 and §T5.3 specify tagging `v1.0.0` upon completing Gate G6.
- Early project research notes and roadmap summaries occasionally mentioned `v0.2.0` or `v2.0` as targets for the V2 architecture rewrite.

This document presents a **proposed, coherent release mapping** adhering to [SemVer 2.0.0](https://semver.org/) and civic-tech open-source practices for Product Owner review and formal ratification.

> [!IMPORTANT]
> **Status Notice:** This strategy is **proposed** and subject to explicit review and ratification by Product Owner Deeptiman. It does not authorize package releases, task additions, or version modifications.

---

## 2. Proposed Version Mapping & Milestone Progression

The progression reconciles current Alpha development, a proposed community beta milestone, and the canonical production GA intent of Backlog T5.3:

```
[0.1.0] Current Alpha Baseline (Metadata declares 0.1.0; no prerelease suffix)
      │
      ▼ (Gates G2 through G6 completion; requires PO decision on beta release task)
[0.2.0] Proposed Technical / Community Beta Milestone (Synthetic-only, controlled environments)
      │
      ▼ (Separately authorized held-out field evaluation, real pack verification, PO GA sign-off)
[1.0.0] Proposed Production General Availability (GA) (Canonical T5.3 release)
```

### Phase 1: `0.1.0` — Current Alpha-Stage Development Baseline (Current State)
- **Scope:** Sprint 0 (G0) baseline freeze + WS1 (G1) Trust & Compliance closeout deliverables.
- **Package Declaration:** `version = "0.1.0"` in `pyproject.toml` (no prerelease suffix in package metadata).
- **Classifier:** `Development Status :: 3 - Alpha`.
- **Operational Reality:**
  - Fully local-first, zero-network, privacy-preserving verification engine.
  - Sourced citations and qualified claims register (`docs/CLAIMS_REGISTER.md`, CLM-001–CLM-011).
  - Synthetic test corpora only (Packets 1–8).
  - Web UI operable via local desktop and LAN on mobile browsers.
  - **Boundary:** Not authorized for public cloud hosting with arbitrary uploads, not authorized for real citizen documents, and not a provider of legal or official eligibility determinations.

### Phase 2: `0.2.0` — Proposed Technical / Community Beta Milestone (Target: Gate G6 Completion)
- **Scope:** Completion of technical gates G2 through G6:
  - **G2 (WS2):** Symmetric V2 resolver (`outcome/resolver.py`), truth-table property tests, slot validation, and injected clock.
  - **G3 (WS3):** Generic scheme-pack loader, schema validation, and linting.
  - **G4 (WS4):** Demo scheme snapshot (`odisha.subhadra`), canonical V2 report schema.
  - **G5 (WS5):** Synthetic evaluation harness, Indic numeral normalization, multi-layout synthetic generator.
  - **G6 (WS6):** Rootless read-only Docker container (`T5.1`), SBOM generation and `pip-audit` zero-CVE verification (`T5.2`).
- **Governance Alignment with Backlog T5.3:**
  - The existing backlog specifies tagging `v1.0.0` at task `T5.3`.
  - Proposing `0.2.0` as an intermediate community beta introduces a release milestone not currently detailed as an independent backlog task.
  - **Pending PO Decision:** The Product Owner must decide whether to:
    1. Define a specific intermediate beta release task (e.g., proposed `T5.1b` or splitting T5.3 into T5.3a Beta and T5.3b GA) with assigned ownership and acceptance criteria; or
    2. Retain `v1.0.0` as the sole release tag at G6, omitting `0.2.0`.
- **Beta Operational Constraints:**
  - Any hosted demo or beta deployment remains strictly **synthetic-only** (`DOCUREADY_SYNTHETIC_ONLY=1`).
  - Strictly prohibited from accepting real applicant identity documents, providing eligibility determinations, or replacing official portal checks.
  - Distributed as a developer/partner preview for civic-tech operators and non-profit partner evaluations in controlled settings.

### Phase 3: `1.0.0` — Proposed Production General Availability (GA Milestone)
- **Scope:** Final production general availability, fulfilling the full intent of Backlog `T5.3`:
  - **Protocol vs. Executed Field Evaluation:** `T4.4` in `docs/BACKLOG.md` produces a *document-only real-sample protocol* (`docs/REAL_SAMPLE_PROTOCOL.md`). It does **not** execute a field evaluation. Production GA requires:
    1. Formal approval and completion of the `T4.4` protocol;
    2. A **separately authorized follow-up execution task** (proposed `T4.5 — Executed Real-Sample Field Evaluation`, pending PO approval of ID, scope, and criteria) conducting consented, redacted, held-out empirical evaluations;
    3. Documented statistical evidence meeting ratified accuracy and safety thresholds;
    4. Independent third-party security, privacy, and accessibility audit;
    5. Final formal sign-off and release authorization by Product Owner Deeptiman.
- **Proposed Statistical Release Criteria (Pending PO Ratification):**
  - A proposed target such as `<0.1% false-pass rate` is an unverified design objective, not an established result.
  - Before treating any statistical threshold as a release gate, the project must define and ratify:
    - **Numerator:** Exact count of undetected disqualifying defects across the test corpus.
    - **Denominator:** Total evaluated applicant documents/packets in the held-out sample.
    - **Held-Out Test Corpus:** Source, stratification, and exclusion criteria of the evaluation corpus.
    - **Sample Size Rationale:** Minimum sample size required to provide statistical power (e.g., $N \ge 3{,}000$ packets to bound a 0.1% rate with 95% confidence).
    - **Confidence Bound Method:** Standard statistical method (e.g., Clopper-Pearson exact interval or Wilson score interval with upper bound $\le 0.1\%$).
  - These criteria remain **proposed** until formal empirical evaluation is authorized and conducted.

---

## 3. Governance Rules & Prohibitions

1. **No Premature Version Bumps:**
   The package version in `pyproject.toml` remains strictly at `0.1.0` during active development. It must **not** be bumped to `0.2.0` or `1.0.0` in routine feature PRs.
2. **Release Authorization Authority:**
   Cutting any release tag (`v0.2.0` or `v1.0.0`) is exclusively reserved for explicit written authorization by Product Owner Deeptiman.
3. **Mandatory Release Notes Structure:**
   Every formal release note must open with:
   - "What this tool does NOT do" (anti-overreach statement).
   - Traceable links to formal gate acceptance records.
   - Sourced citation and operational heuristic verification classifications.
