# DocuReady V2 — Project Status

**Last reviewed:** 14 November 2026
**Canonical repository:** `Algoryxz/DocuReady`
**Status note:** This is the coordination snapshot based on verified GitHub repository, PR, and CI evidence. Refresh every branch, PR, CI result, and commit before acting; these values can go stale.

## Current gates

| Gate | State | Evidence / blocker |
|---|---|---|
| G0 — Baseline frozen | **BLOCKED** | In main CI run `43601998227` (triggered by PR #5 merge `7b55bf829cfba21ee7d277c9b3c933b702f92671` with `fail-fast: false`), all three supported matrix jobs ran to completion and failed: Python 3.10 (70 passed, 8 failed) due to PyMuPDF version conflict (`1.28.2` vs `2.1` bounding boxes caused by PyMuPDF 2.1 `Requires-Python: >=3.11`), while Python 3.11 and 3.12 (each 77 passed, 1 failed) failed on `PKT_07_UNREADABLE_DOC` due to Tesseract 5.5.0 extracting noise OCR text/confidence on Linux whereas baseline was captured on Windows without Tesseract. G0 baseline decision proposal documented in `docs/history/G0_BASELINE_DECISION.md` (`PENDING_DEEPTIMAN_DECISION`). Local 78-test pass is qualified on unsupported Python 3.14.7 without Tesseract. |
| G1 — Honest and clean | Not started | Begins after G0 acceptance. Claims register, no-network contract, licence decision and redaction work remain. |
| G2 — Safe outcomes | Not started | Track B prototype was merged at commit `1994f66af9217d720549124bf6d0e7b23998ac88`, but formal V2 Gate G2 acceptance requires T2.1–T2.4 completion, V2 status vocabulary, and property tests. |
| G3 — Engine equivalence | Not started | YAML schema/primitives and generic.demo port are future work. |
| G4 — Real pack | Not started | Subhadra pack must remain a sourced, dated demo snapshot. |
| G5 — Credible evaluation | Not started | Synthetic split/evaluation protocol not yet accepted. |
| G6 — Release | Not started | Requires G1–G5 evidence and T5.1–T5.3. |

## Task and PR tracker

| Task / work | Owner | State (`todo / doing / review / done / blocked`) | Branch / PR | Gate | Notes |
|---|---|---|---|---|---|
| PR #1 — package migration | Akriti (platform area) | **done** | `feature/g1-package-migration` / [PR #1](https://github.com/Algoryxz/DocuReady/pull/1) | G0 | Merged to `main`; source package and `pyproject.toml` now exist. Do not repeat migration. |
| PR #2 — Track B decision safety prototype | Susmita | **done (prototype only)** | `feature/prototype-decision-safety` / [PR #2](https://github.com/Algoryxz/DocuReady/pull/2) | G2 | Merged into `main` at commit `1994f66af9217d720549124bf6d0e7b23998ac88`. Implements prototype evidence-backed PASS. **Does NOT constitute V2 Gate G2 acceptance.** Formal V2 decision safety requires T2.1–T2.4. |
| PR #3 — Track A UI/privacy prototype | Akriti | **done (prototype only)** | `feature/prototype-ui-privacy` / [PR #3](https://github.com/Algoryxz/DocuReady/pull/3) | G1 | Merged into `main` at commit `6d1ea77e6e82eeccb3b69fa0a9120d416157c005`. Implements ephemeral upload sandbox, report redaction, safe rendering, and demo runbook. Follow-up items tracked in CODE_AUDIT_T0.md for T1.1, T1.2, T1.4. |
| PR #4 — V2 docs & team ownership integration | Deeptiman / Team | **done** | `docs/v2-architecture-team-ownership` / [PR #4](https://github.com/Algoryxz/DocuReady/pull/4) | Docs | Merged into `main` at commit `a93ace285cb5307f34e7a964ca635461fbaeebc1`. Integrated V2 architecture docs, team responsibilities, and claims qualification. |
| PR #5 — T0.1 baseline characterisation & test harness path canonicalization | Akriti / Team | **done (merged)** | `task/T0.1-characterise-current-behaviour` / [PR #5](https://github.com/Algoryxz/DocuReady/pull/5) | G0 | Merged into `main` at commit `7b55bf829cfba21ee7d277c9b3c933b702f92671`. Current open PR count: 0. Delivered path-only test harness canonicalization, recursive diff diagnostics, 4 comparison invariant unit tests, and environment diagnostics step (`fail-fast: false`). Main CI run `43601998227` failed: Python 3.10 (70 passed, 8 failed); Python 3.11 (77 passed, 1 failed); Python 3.12 (77 passed, 1 failed). |
| T0.1 — Characterise current behaviour | Deeptiman (lead/acceptance); Akriti (CI/baseline); Susmita (rules/citations) | **review (pending acceptance)** | `docs/post-merge-g0-state-correction` | G0 | Path-only harness canonicalization and recursive diff diagnostics merged; 4 comparison helper unit tests added (78 total tests); golden snapshot intact (SHA-256 verified); CODE_AUDIT_T0.md and G0_BASELINE_DECISION.md updated. T0.1 remains pending formal acceptance by Deeptiman; G0 remains BLOCKED pending baseline decision. |
| T0.2 — CI that exercises OCR | Akriti | **todo** | After T0.1 ACCEPT | G0 | Existing workflow has Python 3.10–3.12 and English Tesseract. Verify/add Odia and Hindi language data; prove OCR tests run. |
| T0.3 — Package contract verification | Akriti | **todo** | After T0.2 ACCEPT | G0 | Updated scope: validate current package/wheel/CLI. Package move already merged in PR #1; no relocation. |
| T1.1 — Claims register / honest claims | Deeptiman | todo | After G0 | G1 | Remove or source unsupported 80m, 18–32%, 30–45%, DPDP, zero-exfiltration, legal/accuracy/performance claims. |
| T1.2 — Telemetry off / no-network contract | Akriti | todo | After G0 | G1 | Commit telemetry config; adjust `.gitignore`; test full runtime path. |
| T1.3 — PDF backend / licence decision | Akriti | todo | After G0 | G1 | Compare exact package versions and all licences; preserve accuracy/false-pass threshold. |
| T1.4 — Redaction / safe logging | Akriti | todo | After G0 | G1 | Aadhaar/account/phone masking, no PII logs, temp-dir cleanup. |
| T1.5 — Citation audit / sources.yaml | Susmita | todo | After G0 | G1 | Primary sources only; unconfirmed sources remain UNVERIFIED. |
| T2.1 — Status vocabulary / symmetric resolver | Susmita | todo | After G1 prerequisites | G2 | One resolver; public vocabulary from V2 only. Deeptiman reviews product meaning. |
| T2.2 — Per-rule test matrix | Susmita | todo | After T2.1 | G2 | At least 60 applicable cases; every resolver branch exercised. |
| T2.3 — Match grades / injected clock | Susmita | todo | After T2.1 | G2 | Explicit exact/compatible/conflict/ambiguous grades and `as_of`. |
| T2.4 — Slot validation | Akriti | todo | After T2.1 | G2 | Wrong/missing/unreadable/wrong-language document slots. |
| T3.1 — Pack schema / loader / lint | Susmita | todo | After G2 | G3 | Closed primitive registry; schema/lint fixtures. |
| T3.2 — Primitives / generic.demo port | Susmita | todo | After T3.1 | G3 | Equivalence to approved goldens; no eval/exec. |
| T3.3 — odisha.subhadra demo snapshot | Susmita | todo | After T3.2 | G4 | Official sources, demo_snapshot label, closed-window disclosure. |
| T3.4 — Report v2 | Deeptiman | todo | After T3.3 | G4 | Canonical report, schema, source badges, disclaimer and redaction. |
| T4.1 — Evaluation harness v2 | Susmita | todo | After G4 | G5 | dev/calib/test split; false-pass rate first; bootstrap CI. |
| T4.2 — Indic OCR/numerals | Akriti | todo | After G4 | G5 | `eng+ori`/`eng+hin`, script-specific numeral normalization. |
| T4.3 — Generator v2 | Susmita | todo | After G4 | G5 | At least five layouts, at least three reserved for test. |
| T4.4 — Real-sample protocol | Susmita | todo | After G4 | G5 | Document-only protocol; no unconsented documents or real samples in public repo. |
| T5.1 — Container | Akriti | todo | After G5 | G6 | Non-root, read-only root, no-network run. |
| T5.2 — Supply chain | Akriti | todo | After G5 | G6 | Reproducible lock, pip-audit, SBOM, ruff/mypy. |
| T5.3 — Release | Deeptiman | todo | After G5 | G6 | Security/contribution docs, release notes, v1.0.0 only after gates. |

## Status update rules

- Update this file only from observed repository/CI/PR evidence.
- Use `UNVERIFIED` if evidence is unavailable; do not infer task completion from a PR description.
- Do not mark a task `done` until its acceptance criteria are demonstrated and the designated owner accepts the handoff.
- Keep each task on its own branch and PR. Do not begin a dependent task before the preceding task is explicitly accepted.
- Deeptiman owns final gate acceptance.
