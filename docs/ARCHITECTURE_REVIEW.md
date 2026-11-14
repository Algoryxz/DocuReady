# DocuReady V2 — Architecture and Track A/B Review

**Review date:** 14 November 2026
**Canonical repository:** `Algoryxz/DocuReady`
**Review basis:** supplied `ARCHITECTURE_V2.md` and `BACKLOG.md`; read-only inspection of the repository's `main` branch and open Track A/B pull requests.
**Scope boundary:** this is a review and execution plan, not a code change. No branch, commit, push, PR, merge, or repository setting was changed by ChatGPT.

---

## 1. Executive verdict

The V2 direction is sound and worth using as the target architecture. The strongest choices are:

1. DocuReady is an **applicant-side document-preparation aid**, not an eligibility checker or government decision system.
2. A finding must be a claim about evidence, not a verdict about a person.
3. Evidence abstention must be symmetric: weak evidence cannot create a hard failure **or** a reassuring pass.
4. Scheme rules should be declarative, versioned data over a closed Python primitive set. YAML must never become executable code.
5. Every rule/source needs traceability and an explicit human-verification state.
6. Privacy and runtime isolation should be demonstrated by tests rather than marketing claims.
7. A frozen baseline and staged gates should protect the migration from an uncontrolled rewrite.

**Important correction to the proposed backlog:** the package migration described by T0.3 is already present in `main` through merged PR #1. T0.3 must now verify and harden the package contract; it must not repeat the move from flat `src/*.py` files.

**Important correction to the Track A/B status:** the current GitHub PRs are the actual implementation records for the two tracks. Their descriptions report local test totals, but the latest visible GitHub Actions results for both PR heads contain failures. The same eight golden-test failures are also present on the current `main` workflow, so the visible failure is not proof that the Track A or Track B logic introduced eight behaviour regressions. The failure is consistent with a cross-platform path canonicalization defect in the existing golden test.

The correct next move is therefore **baseline repair and code characterization first**, then deliberate Track B/Track A review and integration. Do not merge either prototype solely on its PR description or local test count.

## 2. Repository and PR state observed

The following is a point-in-time snapshot from the read-only review on 14 November 2026. Antigravity must refresh it before acting; branch heads, CI and PR status may have changed.

| Item | Observed state | Review consequence |
|---|---|---|
| Canonical repo | `Algoryxz/DocuReady` (private) | Treat this as the only implementation repository. |
| `main` | `94ef68a37348f7a0852167e5fca6d998c2a2d2c0` | Refresh before creating any branch. |
| PR #1 — package migration | Merged; merge commit is current `main` | Package migration is already done. |
| PR #2 — Track B decision safety | Open; branch `feature/prototype-decision-safety`; head `f78f0e68049ed1c4adfea5923543630b2a8dbf3f` | Review and re-test; do not merge while CI is red or V2 semantics are unmet. |
| PR #3 — Track A UI/privacy | Open; branch `feature/prototype-ui-privacy`; head `c7bcbdc35fb6f2779c194b4be53a66ebc5636549` | Review and re-test; correct missing privacy config, weak lifecycle tests and legacy UI wording. |
| Package tree on `main` | `src/docuready/` package structure exists | Do not repeat a source-tree relocation. |
| Golden baseline | Existing aggregate JSON contains all eight packet baselines | Preserve the existing artifact unless a separate reviewed task explicitly changes its format. |

### 2.1 Baseline and CI failure

The committed golden test compares the complete serialized `AuditResult` and extracted-document structures. It currently normalizes the audit timestamp and execution latency, but does not normalize path separators.

The CI log shows at least this mismatch:

- Expected snapshot path: `synthetic_data/pkt_07_unreadable_doc\\income_cert.pdf`
- Linux CI path: `synthetic_data/pkt_07_unreadable_doc/income_cert.pdf`

The same pattern appears across the eight golden packet cases. The run summary on Track B was `8 failed, 60 passed`; Track A showed `8 failed, 56 passed` in the inspected Python jobs. The current `main` workflow also has a Python 3.11 failure, with other matrix jobs cancelled. The observed evidence points to a path-separator mismatch in the baseline harness.

**Required repair:** inspect the full recursive comparison for all eight packets, then normalize only fields whose schema meaning is a filesystem path (for example `file_name` / `file_path`) into one platform-neutral representation before comparison. Do not rewrite expected snapshots, ignore the entire `extracted_documents` section, weaken assertions, or silently regenerate goldens. Improve the diagnostic so it reports exact JSON paths for every mismatch. Confirm that no non-path fields drift after normalization.

The current repository stores the eight packet expectations in an aggregate `GOLDEN_BASELINE.json`, not eight separate per-packet JSON files. T0.1 should preserve this structure unless there is a separately reviewed reason to split it.

### 2.2 Package migration and T0.3

PR #1 already introduced `pyproject.toml`, `src/docuready/`, package imports, the `docuready` console script and golden-baseline tests. The current `pyproject.toml` has `ui`, `generator`, `dev` and `all` extras. It does **not** yet have the `[ocr]` and `[pymupdf]` extras described by the target layout, and PyMuPDF is currently a core dependency.

Therefore, re-scope T0.3 as:

- validate editable install, wheel/sdist build, console entry point and tests in a clean environment;
- compare the actual package tree and import graph with the target architecture;
- document remaining packaging/extra differences;
- make no behavioural change and do not repeat the package move;
- defer PDF backend extra split and the licence decision to T1.3.

For the currently declared extras, the verification command should use the extras that actually exist (for example `.[ui,generator,dev]`). Do not tell an engineer to run `.[ui,ocr,dev]` until an `[ocr]` extra has actually been added and reviewed.

## 3. Track B review — PR #2 (decision safety)

**What is good**

- It recognizes that the previous safety layer only intercepted `FAIL` and could leave weakly supported `PASS` findings untouched.
- It adds explicit pass-side checks for evidence provenance, cross-document source count, document presence/readability and field confidence.
- It retains fail-side checks for unverified references, single-source contradictions and uncertain OCR evidence.
- It adds adversarial tests and leaves the historical golden JSON unchanged.

**Issues to resolve before acceptance**

1. **Legacy outcome vocabulary:** the new layer emits `UNKNOWN`, but V2's canonical outcome vocabulary is `PASS`, `FAIL`, `WARN`, `REVIEW`, `MISSING`, `NOT_APPLICABLE`. `UNKNOWN` must not become a second public status. Map missing required documents to `MISSING`; map inadequate or ambiguous evidence to `REVIEW` with an explicit reason code.
2. **Negative-list evidence checking:** the pass-side logic blocks several weak states, but it should define an explicit, documented evidence-state mapping and only allow `PASS` when the effective state is positively verified. In particular, explicitly handle `CONFLICTING` and any OCR-derived states. Do not equate native PDF text extraction (`VERIFIED_TEXT`) with legal or scheme authenticity. The V2 evidence state is about confidence in the extracted observation, not proof that a government-issued document is authentic.
3. **Provenance is not source verification:** evidence bounding boxes and file provenance establish where a value was extracted; they do not prove that the governing scheme rule/citation is current or valid. Keep `source_verified` separate from observation provenance and OCR confidence.
4. **String-based statutory verification:** checking whether a citation string is empty or contains `UNVERIFIED` is not a human source audit. T1.5 should provide structured source metadata (`status`, URL, retrieval date, reviewer, clause, verification notes). A rule with an unverified source must be rendered as source-pending and must not be used for a FAIL-capable decision.
5. **Do not manufacture a legal fallback:** the current code inserts a constitutional citation string as a fallback when it downgrades a finding. Do not invent or imply a legal authority for a safety message. Preserve the actual source reference and mark it unverified/pending.
6. **Substring heuristics:** cross-document classification and relevant-field discovery currently rely on tokens in rule IDs or field strings. This is brittle. The pack/primitive model should eventually declare whether a rule is cross-document and its exact input facts/fields. Until that exists, keep the current implementation explicitly transitional and add negative tests for false classification.
7. **Hard-coded time assumptions:** expiry exceptions use year cutoffs such as 2022/2024 and comments tied to 2026. These must not survive into the V2 rule engine. Use the injected `as_of` date and pack-defined validity parameters.
8. **Mandatory-document semantics:** V2 calls for a missing required document to be `MISSING`, not a synthetic legal `FAIL`. Review the special case in the current Track B layer and align it with the V2 truth table.

**Acceptance recommendation:** keep PR #2 open until the baseline test passes in CI, the evidence allowlist/ mapping is explicit, no unsupported fallback citation remains, and the public status mapping is compatible with the V2 resolver. If the full resolver is intentionally deferred to T2.1, document the temporary adapter and its retirement task; do not present the prototype as already implementing the final V2 contract.

## 4. Track A review — PR #3 (UI, privacy and reports)

**What is good**

- Custom uploads and replacement files are written under temporary directories and the visible flows use `finally` cleanup.
- Extracted file paths are reduced to basenames before storing document objects in the UI session.
- JSON/Markdown export defaults to redaction and removes raw evidence snippets.
- External image CDN references were removed from the UI implementation.
- A demo runbook and UI/privacy test module were added.

**Issues to resolve before acceptance**

1. **The promised Streamlit config is absent from the PR diff:** the PR changed-file list does not include `.streamlit/config.toml` or `.gitignore`. On `main`, `.gitignore` ignores the entire `.streamlit/` directory. Add `.streamlit/config.toml` with `gatherUsageStats = false` and change the ignore rule to ignore only `.streamlit/secrets.toml`; add a test that reads and asserts the committed config.
2. **The temporary-directory test does not test production code:** the current test creates a temporary directory, executes `pass` (or raises a locally simulated exception), then deletes it. That proves Python's `finally` syntax, not DocuReady's upload or replacement lifecycle. Factor the file lifecycle into a testable helper/service and test the helper used by the real UI. Cover success, parse failure, write failure and replacement failure.
3. **Redaction coverage is incomplete for the stated V2 policy:** existing tests cover a sample name/currency and the raw snippet. V2 calls for Aadhaar, bank-account and phone masking by default. Add clearly synthetic test identifiers for each, including values appearing in messages, snippets, metadata and filenames where applicable. Verify both JSON and Markdown output and make `--no-redact` an explicit, warned opt-out only where such an option exists.
4. **Legacy prohibited language remains:** the UI and Markdown renderer still emit `READY TO SUBMIT` / `READY_TO_SUBMIT`. V2 expressly prohibits “eligible”, “approved” and “ready to submit”. These labels must be changed to the neutral readiness vocabulary and no-issues meaning from V2. Do not merely hide the text in one screen; test all rendered/exported formats.
5. **Clear-session claims need precise testing:** the session stores structured `AuditResult` and `ExtractedDocument` objects which can still contain extracted personal values in memory. That is different from disk persistence, but it is not the same as having no PII in memory. Test the actual clear-session path and ensure no raw uploaded bytes or temporary paths remain in session state. Describe the guarantee accurately.
6. **HTML test is not an integration test:** the current test calls `html.escape()` directly on a string. Test the rendering helper(s) that the application actually uses with hostile synthetic OCR values and confirm dynamic text is escaped at the HTML boundary. Keep CSS/static HTML separate from untrusted dynamic content.
7. **Terminology and positioning:** replace any remaining “statutory determination”, official-looking readiness certificate language and unqualified claims with the V2 applicant-side preparation-aid description. A privacy-redacted report must still state limitations and source-verification status.

**Acceptance recommendation:** Track A is useful as a foundation, but is not yet a complete V2 privacy contract. Keep PR #3 open until the above issues are addressed and the actual CI matrix is green.

## 5. Architecture clarifications to preserve

These are not reasons to discard V2. They are implementation guardrails to prevent common interpretation errors.

### 5.1 Separate three kinds of verification

Do not collapse these into one Boolean:

- **Observation confidence:** how trustworthy is the extraction of a field from a particular page/region?
- **Cross-document match grade:** do two or more observations agree exactly, agree compatibly, conflict, or remain ambiguous?
- **Rule-source verification:** has a human verified that the cited primary source and clause support this rule and its parameters?

A `VERIFIED` observation is not proof of document authenticity. A source-verified rule is not proof that OCR read a value correctly. A matching pair is not by itself a scheme eligibility finding.

### 5.2 Keep product status distinct from raw rule result

The architecture's raw outcomes and resolved statuses should remain separate. Only the outcome resolver assigns public statuses. UI, CLI and report renderers must import that one vocabulary; they must not implement their own mapping or reintroduce legacy values such as `UNKNOWN`, `READY_TO_SUBMIT`, `ACTION_REQUIRED` or `REJECT_PRECHECK` as V2 public statuses.

### 5.3 Rule packs are constrained data

YAML may declare only schema-validated parameters, doc slots, citations, remediation and registered primitive invocations. Do not support `eval`, `exec`, Jinja/Python interpolation, arbitrary expressions, dynamic imports or callable paths. Unknown primitive or unresolved `$param` must fail pack lint/load. A `verified` pack must have the human-review metadata required by the architecture.

### 5.4 Evaluation labels and claims

All current in-repository sample packets and benchmark corpora are synthetic unless a primary source establishes otherwise. A dataset with held-out examples from the same author/generator is not equivalent to independent real-world validation. Keep dev/calibration/test splits isolated and reserve test-only layouts as specified. False-pass rate should be the first reported metric, with the denominator and confidence interval stated.

### 5.5 No-network contract

The runtime path should not make network calls. The contract test must cover the complete pipeline over all demo packets and replacement flow, not just a selected helper. It should patch the relevant connection entry points and demonstrate that an intentional outbound call fails. Keep research/source retrieval separate from product runtime. A static scan is useful but does not replace the runtime contract.

## 6. Licensing review note — T1.3

The repository's `pyproject.toml` currently declares PyMuPDF as a core runtime dependency while the project metadata declares Apache-2.0. The official PyMuPDF licensing material describes dual licensing under AGPL-3.0 or a commercial Artifex licence. pypdfium2 has its own permissive licensing, and the PDFium component is BSD-style; the selected wheel/build and bundled components still need a complete NOTICE inventory. `pdfminer.six` is MIT-licensed. Sources reviewed on 14 November 2026:

- PyMuPDF licensing: <https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright> and <https://artifex.com/licensing>.
- pypdfium2 licensing: <https://pypi.org/project/pypdfium2/> and <https://github.com/pypdfium2-team/pypdfium2>.
- pdfminer.six licence: <https://pypi.org/project/pdfminer.six/> and <https://github.com/pdfminer/pdfminer.six/blob/master/LICENSE>.

This is a technical licence-inventory note, not legal advice. Do not assert that swapping to pypdfium2 automatically resolves every licensing obligation. Record each candidate's direct and bundled/transitive licences from the exact package version selected. Compare extraction quality, bbox quality, latency and false-pass impact before changing the default. If the alternative regresses beyond the ADR threshold, do not silently accept the regression: document the AGPL/commercial/relicensing decision for the project owners.

## 7. Updated execution order

### Stage 0 — read-only preflight

Antigravity refreshes `origin/main`, current PR heads, CI state and working-tree state. It must not overwrite uncommitted changes or assume the hashes in this review are still current. It reports any unmerged/dirty state before editing.

### Sprint 0 — G0 baseline

| Task | Updated scope | Proposed primary owner |
|---|---|---|
| T0.1 | Characterize current code; fix cross-platform golden comparison without changing the snapshots; write the actual code audit; compare README tree to the real repository. | Deeptiman (acceptance), Akriti (CI/baseline), Susmita (rule/citation inventory) |
| T0.2 | Extend CI's actual OCR coverage to the required languages, verify Tesseract language installation and ensure OCR tests are not skipped. | Akriti |
| T0.3 | Verify the already-migrated package layout, install/build/CLI/wheel contracts and document remaining package-extra differences; no source-tree re-migration and no behaviour change. | Akriti |

**One task, one branch, one PR at a time.** After each task, Antigravity returns the complete handoff packet and stops until Deeptiman explicitly accepts it. T0.2 cannot begin before T0.1 acceptance; T0.3 cannot begin before T0.2 acceptance.

### After G0 — prototype integration and V2 workstreams

1. Re-evaluate PR #2 against the now-green baseline; correct its safety semantics and tests, then review/merge through the team's normal human acceptance process.
2. Re-evaluate PR #3 after the core status contract is understood; correct privacy config, real lifecycle tests, redaction, and prohibited wording. Re-run the complete CI matrix after integration with Track B.
3. Proceed to WS1 (T1.x), then WS2, WS3, WS4 and WS5 as ordered in `BACKLOG.md`. The T1.x items may be parallelized after G0 only when their file ownership and interfaces do not overlap.
4. Maintain gates G0–G6; no task may skip a gate because the code appears to work locally.

## 8. Decisions and stop conditions

Stop and report `BLOCKED` rather than guessing when:

- repository state, base branch or current PR head differs from the expected state and the difference affects safety;
- a command fails, source cannot be verified, or a dependency licence cannot be established;
- a code change would require changing golden expectations or a V2 contract outside the task;
- evidence-state mapping or rule-source truth is unclear;
- a task acceptance criterion cannot be demonstrated;
- the working tree contains user changes that cannot be safely preserved.

Do not merge, close or force-push any existing PR as part of T0.1. Do not alter `ARCHITECTURE_V2.md` or change the meaning of a backlog acceptance criterion without a proposed ADR/decision and explicit owner approval.

## 9. Overall recommendation

Keep the V2 architecture as the proposed target. Do not start the full scheme-pack rewrite yet. First make the existing package and baseline reproducible across platforms, produce the real code audit, and get CI green. Then integrate the two prototype tracks as reviewed, bounded changes. This protects the work already done while preventing a promising prototype from being mistaken for a completed V2 safety and privacy contract.
