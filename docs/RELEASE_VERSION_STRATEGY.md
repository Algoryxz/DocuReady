# DocuReady — Semantic Release Version Strategy & Milestone Progression

**Document Version:** 1.0.0
**Date:** 15 November 2026
**Status:** Canonical Governance Strategy
**Repository:** `Algoryxz/DocuReady`
**Product Owner:** Deeptiman
**Technical Leads:** Antigravity, Akriti, Susmita

---

## 1. Context & Problem Statement

Historical documentation across DocuReady contained conflicting references to upcoming release version tags:
- `pyproject.toml` declares `version = "0.1.0"` with PyPI classifier `Development Status :: 3 - Alpha`.
- `docs/BACKLOG.md` §2 and §T5.3 referenced tagging `v1.0.0` upon completing Gate G6.
- Early project research notes and roadmap summaries occasionally mentioned `v0.2.0` or `v2.0` as the target for the V2 architecture rewrite.

This document establishes a **single, consistent semantic versioning progression** adhering to [SemVer 2.0.0](https://semver.org/) and standard civic-tech open-source release practices.

---

## 2. Canonical Version Progression

The project adopts a three-phase progression aligned with gate milestones:

```
[0.1.0-alpha] (Current Baseline)
      │
      ▼ (Gates G2 through G6 completion: WS2 Correctness, WS3 Packs, WS5 Eval, WS6 Container)
[0.2.0] Milestone Release (First Public Community Beta)
      │
      ▼ (Held-out field evaluations, real scheme pack verification, external security review)
[1.0.0] Production General Availability (GA)
```

### Phase 1: `0.1.0-alpha` — Current Development & Trust Baseline (Current State)
- **Scope:** Sprint 0 (G0) baseline freeze + WS1 (G1) Trust & Compliance closeout.
- **Package Declaration:** `version = "0.1.0"` in `pyproject.toml`.
- **Classifier:** `Development Status :: 3 - Alpha`.
- **Operational Reality:**
  - Fully local-first, zero-network, privacy-preserving core.
  - Sourced citations and qualified claims register (CLM-001–CLM-011).
  - Synthetic test corpora only (Packets 1–8).
  - Web UI operable via local desktop and LAN on mobile browsers.
  - Not yet authorized for unrestricted public cloud deployment or field welfare applicant advice.

### Phase 2: `0.2.0` — Technical Architecture Milestone (Target: Gate G6 Completion)
- **Scope:** Completion of Gates G2 through G6:
  - **G2 (WS2):** Symmetric V2 resolver (`outcome/resolver.py`), truth-table property tests, slot validation, and injected clock.
  - **G3 (WS3):** Generic scheme-pack loader, schema validation, and linting.
  - **G4 (WS4):** Demo scheme snapshot (`odisha.subhadra`), canonical V2 report schema.
  - **G5 (WS5):** Held-out evaluation harness, Indic OCR/numeral normalization, multi-layout synthetic generator.
  - **G6 (WS6):** Rootless read-only Docker container (`T5.1`), SBOM generation and `pip-audit` zero-CVE verification (`T5.2`).
- **Package Declaration:** `version = "0.2.0"` in `pyproject.toml`.
- **Classifier:** `Development Status :: 4 - Beta`.
- **Release Assets:** Standalone reproducible wheel, Docker container image, CycloneDX SBOM, cryptographic SHA-256 manifest.
- **Operational Reality:** Fully feature-complete engine suitable for deployment by partner non-profits, student centers, and civic-tech operators in controlled environments.

### Phase 3: `1.0.0` — Production General Availability (Target: Post-G6 Field Verification)
- **Scope:** Formal production release following empirical field verification:
  - Held-out evaluation against real-world anonymized sample protocol (`T4.4`).
  - Empirical false-pass rate verified at <0.1% on field corpora.
  - Multi-lingual OCR support verified in field conditions (`eng+ori` and `eng+hin`).
  - Independent third-party security, privacy, and accessibility audit.
  - Formal sign-off and authorization by Product Owner Deeptiman.
- **Package Declaration:** `version = "1.0.0"` in `pyproject.toml`.
- **Classifier:** `Development Status :: 5 - Production/Stable`.
- **Operational Reality:** Production-grade civic utility with stable semantic public API and published scheme-pack registry.

---

## 3. Governance Rules & Prohibitions

1. **No Premature Version Bumps:**
   The package version in `pyproject.toml` remains strictly at `0.1.0` during active development. It must **not** be bumped to `0.2.0` or `1.0.0` in routine feature PRs.
2. **Release Authorization:**
   Cutting a milestone release (tagging `v0.2.0` or `v1.0.0`) is exclusively reserved for task `T5.3` and requires explicit written authorization from Product Owner Deeptiman.
3. **Changelog & Release Notes:**
   Every formal release note must open with:
   - "What this tool does NOT do" (anti-overreach statement).
   - Traceable link to gate acceptance records.
   - Sourced citation and heuristic verification status.
