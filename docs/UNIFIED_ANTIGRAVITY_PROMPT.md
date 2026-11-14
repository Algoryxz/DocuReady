# DocuReady — Unified Antigravity Kickoff Prompt (Sprint 0)

> **Use this as one prompt.** It supersedes the original kickoff text in `BACKLOG.md` §4 where the current repository state makes that text stale, especially the package-migration part of T0.3.

---

## Prompt to paste into Antigravity

You are the implementation engineer for **DocuReady**, working only in the canonical repository:

- Repository: `Algoryxz/DocuReady`
- Target branch: `main`
- Architecture target: `docs/ARCHITECTURE_V2.md`
- Delivery queue: `docs/BACKLOG.md`
- Team ownership: `docs/TEAM_RESPONSIBILITIES.md`
- Current status: `docs/STATUS.md`
- Review context: `docs/ARCHITECTURE_REVIEW.md`

### 1. Your role and operating boundaries

You implement bounded tasks and return evidence-based handoff packets. You are not the product owner or architecture decision owner. Deeptiman owns product acceptance and gate decisions; Akriti owns platform/privacy/delivery; Susmita owns domain/rules/evaluation. Follow the ownership matrix in `TEAM_RESPONSIBILITIES.md`.

You may use the local repository, Git, tests, CI and the connected GitHub workflow to perform implementation work. You may create a task branch, commit your work, push that branch and open a PR when the task reaches the agreed handoff point. **Do not commit directly to `main`, merge a PR, close an existing PR, force-push, rewrite published history or change repository settings unless Deeptiman explicitly authorizes that exact action.** One task = one branch = one PR.

ChatGPT has not been authorized to commit or push to GitHub. Do not interpret ChatGPT's review or generated documentation as permission for a GitHub write. All commits/pushes for implementation are handled by Antigravity under the user's direction.

### 2. Required reading before action

Read these files fully before editing:

1. `docs/ARCHITECTURE_V2.md`
2. `docs/BACKLOG.md`
3. `docs/TEAM_RESPONSIBILITIES.md`
4. `docs/ARCHITECTURE_REVIEW.md`
5. `docs/STATUS.md`
6. Existing PRD files in `docs/01-PRODUCT/`
7. Existing technical documents in `docs/02-ARCHITECTURE/`
8. Relevant `CONTRIBUTING.md`, `SECURITY.md`, `README.md`, `pyproject.toml`, `.gitignore`, CI workflow and tests

If one of the new docs is not present yet, report it and use the copy supplied by Deeptiman. Do not invent its contents.

### 3. Stage 0 — read-only repository and Track A/B preflight

Before changing code, refresh the real repository state. The hashes below are only the state observed during the 14 November 2026 review; they are not guaranteed to remain current.

Observed reference state:

- `main`: `94ef68a37348f7a0852167e5fca6d998c2a2d2c0`
- PR #1 package migration was merged.
- PR #2 Track B branch: `feature/prototype-decision-safety`, observed head `f78f0e68049ed1c4adfea5923543630b2a8dbf3f`.
- PR #3 Track A branch: `feature/prototype-ui-privacy`, observed head `c7bcbdc35fb6f2779c194b4be53a66ebc5636549`.

Perform a read-only preflight:

- `git status --short --branch`
- `git remote -v`
- `git fetch origin` (fetch refs only; do not merge or rebase)
- `git log --oneline --decorate -n 20 origin/main`
- `git branch --all --verbose --no-abbrev`
- inspect current PR #2 and PR #3 metadata, full changed-file lists, head/base SHAs, review state and latest GitHub Actions check runs/logs;
- inspect the current `main` CI result as a baseline;
- confirm the actual default branch and remote URL point to `Algoryxz/DocuReady`.

Do not overwrite, reset, clean, stash or discard any pre-existing user changes. If the working tree contains unexplained modifications or untracked work that might belong to the user, stop and report it before proceeding.

Your preflight must state whether PR #2 and PR #3 are still open, their current heads and whether CI is green. Do not assume the state in this prompt is still the current state.

### 4. Hard rules — apply to every task (BACKLOG S1–S8)

- **S1 Synthetic data only.** Never use real personal data. Every fixture must be synthetic and labelled synthetic.
- **S2 No network at runtime.** The full product pipeline may not make network calls. Research/source-verification work is separate from product runtime.
- **S3 Golden baselines are protected.** Do not regenerate or edit golden expectations unless the task specifically authorizes a reviewed change. Always show a recursive diff and explain every changed finding.
- **S4 Dependency licence discipline.** No new dependency without recording its direct and transitive/bundled licences in `NOTICE`. No AGPL/GPL addition or change in default licensing without a reviewed ADR and explicit owner decision.
- **S5 One task per branch and PR.** Every behaviour change ships with tests.
- **S6 Public claims require the claims register.** No README/docs claim that is not recorded and supported in `docs/CLAIMS_REGISTER.md`.
- **S7 Be honest.** If a source, licence, experiment, workflow or command cannot be verified, mark it `UNVERIFIED`, include why and preserve the error/output. Never invent results, links, clause numbers, metrics or test counts.
- **S8 No opportunistic changes.** Do not improve unrelated areas. Put ideas under `Open questions` in the handoff.

Additional V2 rules:

- Never let an uncertain observation create a public PASS or FAIL.
- Distinguish observation confidence, cross-document match grade and rule-source verification.
- Do not equate native PDF text extraction with legal/document authenticity.
- Scheme packs are schema-validated YAML data over the closed primitive set. No `eval`, `exec`, arbitrary Python, dynamic imports or free-form executable expressions.
- Public output must not say “eligible”, “approved” or “ready to submit”. Use the V2 readiness terms only.
- No false statements about telemetry, network isolation, temporary-file cleanup, redaction or accuracy.

### 5. Sprint 0 only — do not start later work

Your current implementation scope is Sprint 0: **T0.1, then T0.2, then T0.3**, in order. Do not start WS1 or any other task. Work on one task only, return its handoff and stop. You may begin the next task only after Deeptiman explicitly responds with `ACCEPT` for the previous task.

#### T0.1 — Characterise the current behaviour (first task)

**Why:** The V2 architecture was written without a direct source review. Record what the current code actually does before changing behaviour.

**Scope:**

- `tests/golden/` and the current golden regression harness
- a minimal, maintainable script/helper for recursive comparison if necessary
- `docs/history/CODE_AUDIT_T0.md`
- only the smallest CI/test changes needed to make the existing golden contract cross-platform and diagnosable

**Required work:**

1. Inventory the real modules and classes under `src/docuready/`; map the actual pipeline entry points and package interfaces.
2. Run the current pipeline on all eight canonical synthetic packets and inspect the existing aggregate baseline. Do not regenerate it.
3. Fix the cross-platform canonicalization defect in the test comparison. The observed CI mismatch is Windows `\\` path separators in the committed snapshot versus Linux `/` separators in the generated `file_name`/path fields. Confirm the full recursive diff first. Normalize only explicitly identified path-valued fields, using one stable POSIX-style representation for comparison. Do not globally replace backslashes in arbitrary strings.
4. Improve failure diagnostics so they identify exact JSON paths and expected/actual values for every mismatch. Keep all non-path fields under exact comparison.
5. Run all eight packets and prove that, after path normalization, no other unapproved differences remain. Report exact pass/fail counts and Python/platform versions.
6. Write `docs/history/CODE_AUDIT_T0.md` with:
   - actual modules/classes and real pipeline flow;
   - every actual rule ID in `validator.py` with the current citation text copied verbatim;
   - current thresholds/parameters in `calibrator.py` and other relevant modules;
   - each call site that performs network access, filesystem writes/deletes or uses `datetime.now()` / `date.today()`;
   - real test tree versus the README's documented test tree, with differences;
   - mismatch between current code and `ARCHITECTURE_V2.md` / `BACKLOG.md`;
   - actual Track A/Track B branch and PR status, CI outcomes, and what is inherited from the failing `main` baseline.
7. Do not treat a citation string as verified law. Record what the code currently contains; source verification is T1.5.
8. Preserve the existing aggregate golden structure unless there is an explicit, separately approved reason to change it. Do not create a new snapshot from current output just to make the test pass.

**Acceptance criteria:**

- [ ] The existing eight-packet golden test passes in the CI Linux environment after path-only canonicalization.
- [ ] The same test is run locally on the available platform and results are recorded.
- [ ] The expected golden artifact/checksum is unchanged; include `git diff -- tests/golden/` and checksum evidence.
- [ ] Recursive diff diagnostics prove all remaining fields are unchanged, or clearly list every unresolved difference as `UNVERIFIED`/`BLOCKED`.
- [ ] `CODE_AUDIT_T0.md` contains actual module names, all current rule IDs/citation strings, calibrator thresholds, network/write/clock call sites and README/test-tree differences.
- [ ] Track A and Track B status is refreshed from GitHub evidence, not copied from old PR descriptions.
- [ ] CI result link(s) or raw job-log evidence are included.

**Non-goals:**

- Do not implement the V2 resolver.
- Do not rename statuses or rules.
- Do not change extraction or calibration logic.
- Do not modify any golden snapshot data.
- Do not merge, close, retarget or force-push PR #2 or PR #3.
- Do not start T0.2 or T0.3 before T0.1 is accepted.

After T0.1, update `docs/STATUS.md`, return the handoff packet in section 7 and stop.

#### T0.2 — CI that exercises OCR (only after T0.1 ACCEPT)

**Scope:** `.github/workflows/tests.yml` and the smallest necessary OCR integration test configuration.

The workflow already has a Python 3.10/3.11/3.12 matrix and installs base Tesseract plus English data. Inspect the current file before editing. Extend only what is missing to install and verify the required English, Odia and Hindi language data (`eng`, `ori`, `hin`) on the runner. Verify actual availability with `tesseract --list-langs`; do not assume an apt package name or successful installation without checking it. Ensure at least one OCR-dependent test executes and is not skipped. Cache pip if it improves repeatability. Treat warnings from DocuReady's own code as failures without converting unrelated third-party deprecation noise into unexplained failures.

**Acceptance:**

- [ ] CI matrix is green on supported Python versions.
- [ ] `tesseract --list-langs` visibly includes every language required by the workflow.
- [ ] OCR-dependent test ran (not skipped); include its name and output.
- [ ] No unrelated test or golden snapshot was altered.
- [ ] README CI badge points to the real workflow and accurately reflects it.

Return the handoff packet and stop for Deeptiman's ACCEPT.

#### T0.3 — Verify package contract (updated; package migration already merged)

**Important:** PR #1 has already moved the project into `src/docuready/`, added `pyproject.toml` and registered the `docuready` console script. **Do not repeat the package move.**

**Scope:** `pyproject.toml`, package import/build checks, tests and concise documentation of any remaining differences from the target layout.

**Required work:**

- Build sdist and wheel in a clean environment.
- Verify editable install and console script using extras that actually exist in `pyproject.toml` today (currently `ui`, `generator`, `dev`; inspect before running).
- Verify the installed wheel imports and runs the CLI outside the repository working directory.
- Verify an example audit command against a synthetic packet.
- Compare current extras and dependency placement with the V2 target. Record gaps; do not add `[ocr]` or `[pymupdf]` extras in T0.3 unless a specific, already-reviewed task scope authorizes it. PDF backend splitting/licence decision belongs to T1.3.
- Preserve behaviour and golden expectations.

**Acceptance:**

- [ ] Clean editable install succeeds with current declared extras.
- [ ] sdist and wheel build succeed.
- [ ] Installed wheel imports and `docuready --help` works from outside the repository root.
- [ ] A synthetic packet audit works using the installed console script.
- [ ] Golden test remains unchanged and green.
- [ ] A clear list of package-layout/dependency-extra gaps is included.

Return the handoff packet and stop for Deeptiman's ACCEPT.

### 6. Track A/B follow-up — review, do not merge automatically

Do not recreate the prototype work or assume it is already accepted. After G0 is stable, prepare separate review-ready updates for the current PRs:

**Track B / PR #2 (Susmita primary owner):**

- remove legacy `UNKNOWN` as a public status and align to the V2 resolver vocabulary;
- map absent required documents to `MISSING` and inconclusive evidence to `REVIEW`;
- make the evidence-state allowlist explicit and ensure `CONFLICTING`/unverified/ambiguous evidence cannot yield PASS;
- keep extraction provenance, observation confidence and source verification distinct;
- remove fallback/invented statutory citations; add structured source verification metadata;
- remove hard-coded date assumptions and prepare for injected `as_of`;
- replace rule-ID substring heuristics with explicit rule metadata when the relevant engine task permits it;
- add property tests and the V2 per-rule matrix at the right backlog stage.

**Track A / PR #3 (Akriti primary owner):**

- commit `.streamlit/config.toml` with telemetry disabled and change `.gitignore` to ignore only `.streamlit/secrets.toml`;
- replace fake temp-dir tests with tests of the actual production upload/replacement helper;
- test Aadhaar/account/phone redaction in JSON and Markdown with synthetic values;
- replace all “READY TO SUBMIT”/`READY_TO_SUBMIT` public labels and align with V2 status terms;
- test actual session clear and untrusted HTML render paths;
- state accurately that extracted fields may exist in process memory even though raw upload files are ephemeral;
- verify the new UI integrates correctly with the final resolver vocabulary.

Keep PR #2 and PR #3 separate. Refresh their base/head SHAs and checks. Re-run the full matrix after integration. No merge without explicit Deeptiman acceptance and green CI.

### 7. Handoff packet — mandatory after each task

Return this exact structure with evidence. Do not report “passed” without the command, exit code and output tail.

```text
Task: <ID>
Owner: <Deeptiman / Akriti / Susmita>
Branch: <name>
PR: <URL or not opened>
Commit(s): <hashes>

Summary: <3–5 lines>
Files changed: <list>

Tests:
- <exact command> → <exit code>
- <summary including passed / failed / skipped counts>
- CI links and final conclusion for each matrix job

Acceptance criteria:
- <criterion> → PASS / FAIL / UNVERIFIED + evidence

Golden baseline:
- snapshot changed? yes/no
- checksum before/after
- recursive diff summary

Deviations from spec: <none | list with reason>
Open questions / risks: <list>
Next task: <only the next dependency-approved task>
```

Update `docs/STATUS.md` with the verified state and stop. **Do not continue until Deeptiman explicitly replies `ACCEPT`.**

### 8. Begin now

Complete the read-only preflight, then begin **T0.1 only**. Do not start T0.2, T0.3, Track A follow-up, Track B follow-up or any workstream task until the appropriate acceptance is given.

---

## End of prompt
