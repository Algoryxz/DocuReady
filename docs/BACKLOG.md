# DocuReady — Delivery Backlog (V2)

Companion to `ARCHITECTURE_V2.md`. Copy this file to `docs/BACKLOG.md` in the repo.

**Team Model:**
- **Deeptiman** — Product Owner, Architecture Coordination & Integration Lead
- **Akriti** — Technical Engineering, Platform, Privacy & Delivery Lead
- **Susmita** — Domain Engineering, Validation Rules & Evaluation Lead

See [TEAM_RESPONSIBILITIES.md](TEAM_RESPONSIBILITIES.md) for full role definitions, PRD/TRD allocations, and individual workspace agreements.

**AI Tooling Roles:**
- **Claude** = Architecture authoring, task specification refinement, and independent code review.
- **ChatGPT** = Team coordination, queue sequencing, status tracking (`docs/STATUS.md`), and teammate context priming.
- **Antigravity** = Implementation agent executing bounded tasks per workspace on task-specific branches.

---

## 1. Operating protocol

### 1.1 The loop (one task at a time)

1. **Task Assignment & Spec Refinement**: Each backlog task has one named primary owner (Deeptiman, Akriti, or Susmita) per `docs/TEAM_RESPONSIBILITIES.md` §4. Task specifications (with acceptance criteria) are authored/refined in alignment with `ARCHITECTURE_V2.md`.
2. **Queue Sequencing & Handoff**: The primary owner coordinates task sequencing (via ChatGPT tracking `docs/STATUS.md`) and primes their Antigravity workspace with the task specification and relevant PRD/TRD context.
3. **Bounded Implementation**: Antigravity implements the task on branch `task/<ID>-<slug>` (or track branch), executes required tests locally and in CI, and returns the structured handoff packet (§1.3).
4. **Independent Review**: The implementation is reviewed against the acceptance criteria (by peer teammates and Claude) yielding `ACCEPT`, `ACCEPT-WITH-NITS`, or `REWORK` with concrete evidence.
5. **Acceptance & Merge**: PR merge occurs only upon formal acceptance (signed off by Deeptiman as integration lead and the technical lead for that domain). Update `docs/STATUS.md`.

### 1.2 Standing rules for Antigravity (apply to every task)

- **S1** Never use real personal data. All fixtures are synthetic and labelled so.
- **S2** The runtime pipeline makes no network calls. Research tasks may use the network; product code may not.
- **S3** Golden snapshots change only when the task spec says so, and the diff is shown in the handoff.
- **S4** Dependency licence discipline. No new dependency without recording its direct and transitive/bundled licences in `NOTICE`. No AGPL/GPL additions, default licence changes, or copyleft dependencies without a reviewed ADR, rigorous direct and transitive/bundled licence investigation, Akriti's technical/platform review, explicit human owner approval, and Deeptiman's final acceptance of the project-level decision. Claude may provide independent technical/licensing review, but has no decision or approval authority.
- **S5** One task per branch and PR. Every behaviour change ships with tests.
- **S6** No claim in README or docs that is not in `docs/CLAIMS_REGISTER.md`.
- **S7** If something cannot be verified (a source, a licence, an experiment), write `UNVERIFIED` and say why. Never invent results, URLs, clause numbers or metrics.
- **S8** Do not "improve" things outside the task. Put ideas under *Open questions* in the handoff.

### 1.3 Handoff packet (what Antigravity returns)

```
Task: <ID>   Branch: <name>   Commit(s): <hashes>
Summary: <3-5 lines>
Files changed: <list>
Tests: <command> → <tail of output, incl. counts>
Acceptance criteria: <each criterion → PASS / FAIL / UNVERIFIED + evidence>
Deviations from spec: <none | list with reason>
Open questions: <list>
```

### 1.4 Task spec template

```
ID / Title / Workstream / Depends on
Why (1-2 lines)
Scope (files/modules)         Non-goals
Behaviour (precise)
Acceptance criteria (checkboxes, testable)
Tests required
Gate it contributes to
```

### 1.5 `docs/STATUS.md` (ChatGPT maintains)

| Task | Owner | State (todo / doing / review / done / blocked) | Branch/PR | Gate | Notes |
|---|---|---|---|---|---|

---

## 2. Gates

| Gate | Meaning | Passed when |
|---|---|---|
| **G0** Baseline frozen | Safe to refactor | **PASSED (Accepted 15 Nov 2026)**: T0.1–T0.3 accepted; golden snapshots green; remote CI green on main (runs 43630377408, 43636186644) |
| **G1** Honest and clean | Public claims match reality | T1.1–T1.5 accepted; claims register complete; no-network test green; licence decision recorded |
| **G2** Safe outcomes | No false assurance | T2.1–T2.4 accepted; per-rule test matrix green |
| **G3** Engine equivalence | Rules as data, same behaviour | T3.1–T3.2 accepted; `generic.demo` reproduces golden snapshots except the changes approved in T2.x |
| **G4** Real pack | First scheme pack with sources | T3.3 accepted; pack lint passes; status is `demo_snapshot` or `verified` truthfully |
| **G5** Credible evaluation | Numbers mean something | T4.1–T4.3 accepted; `eval/EVAL_CARD.md` published; regression gate in CI |
| **G6** Release | Tag `v1.0.0` | G1–G5 passed; T5.1–T5.3 accepted |

---

## 3. Task list

Order: **Sprint 0 (T0.x)** → **WS1 (T1.x, parallel)** → **WS2** → **WS3** → **WS4** → **WS5**.
T1.x tasks are independent of each other and can run in parallel once G0 passes.

### Sprint 0 — Baseline (PASSED — Formally accepted by Deeptiman on 15 November 2026)

#### T0.1 — Characterise current behaviour
- **Why:** The V2 architecture was written without a direct source review. Record what the current code actually does before changing behaviour.
- **Scope:** `tests/golden/` and the current golden regression harness; a minimal, maintainable script/helper for recursive comparison if necessary; `docs/history/CODE_AUDIT_T0.md`; only the smallest CI/test changes needed to make the existing golden contract cross-platform and diagnosable.
- **Behaviour:**
  1. Inventory real modules and classes under `src/docuready/`; map actual pipeline entry points and package interfaces.
  2. Use the existing eight canonical synthetic packets and existing aggregate golden baseline (`GOLDEN_BASELINE.json`). Do not regenerate, replace or modify golden snapshots.
  3. Fix the cross-platform canonicalization defect in the test comparison. The observed CI mismatch is Windows `\\` path separators in the committed snapshot versus Linux `/` separators in the generated `file_name`/path fields. Confirm the full recursive diff first. Normalize only explicitly identified path-valued fields in the test comparison, using one stable POSIX-style representation. Do not globally replace backslashes in arbitrary strings.
  4. Preserve exact comparison for all non-path fields. Add exact JSON-path mismatch diagnostics showing expected and actual values for every difference.
  5. Run all eight packets and prove that, after path normalization, no other unapproved differences remain. Report exact pass/fail counts and Python/platform versions.
  6. Write `docs/history/CODE_AUDIT_T0.md` detailing:
     - actual modules/classes and real pipeline flow;
     - every actual rule ID in `validator.py` with current citation text copied verbatim (noting that citation strings are not verified law until T1.5);
     - current thresholds/parameters in `calibrator.py` and other relevant modules;
     - each call site that performs network access, filesystem writes/deletes, or uses `datetime.now()` / `date.today()`;
     - real test tree versus the README's documented test tree, with differences listed;
     - gaps between current code and `ARCHITECTURE_V2.md` / `BACKLOG.md`;
     - actual Track A/Track B branch and PR status, CI outcomes, and what is inherited from the baseline.
  7. Record the baseline checksum and prove that golden artifacts remain unchanged (`git diff -- tests/golden/`).
- **Acceptance:** *(Formally accepted by Deeptiman on 14 November 2026; PR #13 merged at `9ae7cb18366424932aa363983a15e44424c293e1`)*
  - [x] Golden regression tests pass in the CI Linux environment: 7 exact native vector packets (Packets 1–6 and 8) assert 100% bit-for-bit parity after path-only canonicalization, and Packet 7 asserts semantic unreadable-document contracts without brittle OCR text/confidence matching.
  - [x] The same test is run locally on the available platform and results are recorded.
  - [x] The expected golden artifact/checksum is unchanged; include `git diff -- tests/golden/` and checksum evidence.
  - [x] Recursive diff diagnostics prove all remaining fields are unchanged, or clearly list every unresolved difference as `UNVERIFIED`/`BLOCKED`.
  - [x] `docs/history/CODE_AUDIT_T0.md` contains actual module names, all current rule IDs/citation strings, calibrator thresholds, network/write/clock call sites, README/test-tree differences, and code-versus-architecture gaps.
  - [x] Track A and Track B status is refreshed from GitHub evidence, not copied from old PR descriptions.
  - [x] CI result link(s) or raw job-log evidence are included.
- **Non-goals:**
  - Do not implement the V2 resolver.
  - Do not rename statuses or rules.
  - Do not change extraction or calibration logic.
  - Do not modify any golden snapshot data or regenerate golden files.
  - Do not merge, close, retarget or force-push PR #2 or PR #3.
  - Do not start T0.2 or T0.3 before T0.1 is accepted.
- **Gate:** G0

#### G0.1 — Runtime support, PDF baseline & golden/OCR contract modernization
- **Why:** T0.1 characterised baseline behaviour and resolved path discrepancies, but exposed that Python 3.10 cannot install PyMuPDF 2.1 (due to PyPI `Requires-Python: >=3.11` wheel metadata) and that Linux CI with Tesseract 5.5.0 produces non-empty OCR output on Packet 7 compared to historical empty snapshot values.
- **Scope:** `pyproject.toml`, `.github/workflows/tests.yml`, `requirements/ci-lock-py*.txt`, `requirements/README.md`, `tests/test_golden_baseline.py`, `docs/history/G0_BASELINE_DECISION.md`.
- **Behaviour:**
  1. Retire Python 3.10 (EOL 1 October 2026); modernize declared Python support to `>=3.11,<3.15`.
  2. Pin provisional technical baseline PDF engine to `pymupdf==2.1` to maintain vector geometry reproducibility (final backend/licensing review under T1.3 / ADR-001).
  3. Defer Python 3.15 due to upstream `onnxruntime` binary wheel availability on PyPI, subject to explicit reintroduction criteria.
  4. Generate and commit canonical hash-checked per-Python lock files for Linux x86_64 across Python 3.11–3.14 (`requirements/ci-lock-py3.11.txt` through `ci-lock-py3.14.txt`) from `pyproject.toml` and the `all` extra.
  5. Update CI workflow (`.github/workflows/tests.yml`) to run the blocking 4-version matrix (`3.11`, `3.12`, `3.13`, `3.14`) pinned to `ubuntu-24.04` with `fail-fast: false` and install via matching lockfiles before building distribution packages with `--no-isolation`.
  6. Modernize golden test harness (`tests/test_golden_baseline.py`): enforce 100% bit-for-bit parity on native vector packets (Packets 1–6 and 8), and assert stable semantic unreadable document contracts for Packet 7 (`PKT_07_UNREADABLE_DOC`), comparing all deterministic fields of `INCOME_CERT` exactly while excluding only the OCR-derived fields `raw_text` and `mean_ocr_confidence`.
- **Acceptance:**
  - [x] Python 3.10 retired and `requires-python = ">=3.11,<3.15"` declared in `pyproject.toml`.
  - [x] Provisional technical baseline pinned to `pymupdf==2.1` in `dependencies`.
  - [x] Canonical hash-checked CI lock files generated and committed for Python 3.11–3.14.
  - [x] CI workflow updated to 4-version blocking matrix on `ubuntu-24.04` installing from lock files.
  - [x] Golden harness enforces 100% bit-for-bit vector parity on Packets 1–6 & 8, and exact deterministic field comparison on Packet 7 (excluding only `raw_text` and `mean_ocr_confidence`).
  - [x] Full test suite (79 tests) passes locally under Python 3.11+.
  - [x] All four matrix jobs (3.11–3.14) pass in GitHub Actions CI (Run 43614550313 and Run 43615814990 passed across Python 3.11, 3.12, 3.13, 3.14 with 79 tests per job, build with `--no-isolation`, CLI benchmark/audit, and lock-based isolated wheel verification with `pip check`).
  - [x] Decision record `docs/history/G0_BASELINE_DECISION.md` updated with Deeptiman's 14 November 2026 approval and amendment.
- **Gate:** G0

#### T0.2 — CI that exercises OCR
- **Scope:** `.github/workflows/tests.yml`, `tests/test_ocr_integration.py`, `tests/test_warning_policy.py`, `pyproject.toml`.
- **Status note:** **Formally accepted by Product Owner Deeptiman on 15 November 2026.** Implementation merged across PR #14 (`28d8a858d72e72aefbae2144a089704b61922dcf`) and PR #18 (`1fbc3b69fac63249da66be24b69653bc09822766`). Remote CI on `main` passed all 88 tests across Python 3.11–3.14 with 0 skips (run 43630377408). Language support boundary: current application uses default English OCR configuration; installed Odia and Hindi resources provide CI presence, not application-level multilingual OCR.
- **Behaviour:** Install `tesseract-ocr`, `tesseract-ocr-eng`, `tesseract-ocr-ori`, `tesseract-ocr-hin` in CI. Matrix 3.11/3.12/3.13/3.14. Cache pip. Fail on warnings from our own code. Execute genuine OCR recognition proof against image-only raster PDF.
- **Acceptance:** *(Formally accepted by Deeptiman on 15 November 2026)*
  - [x] Latest run on `main` is green and visible in the handoff (run 43630377408 passed all 4 matrix jobs with 88 tests passed, 0 skips)
  - [x] A test that needs OCR is shown to have run (not skipped) (`tests/test_ocr_integration.py` ran and passed in CI; confirmed distinctive synthetic token recognized via real `LOCAL_OCR` route)
  - [x] Badge in README reflects the real workflow status (reconciled to 88 passing tests in PR #20)
- **Gate:** G0

#### T0.3 — Package contract verification
- **Depends on:** T0.1, T0.2 (Start only after T0.2 ACCEPT).
- **Status note:** **Formally accepted by Product Owner Deeptiman on 15 November 2026.** Implementation was merged in PR #17 (`40d2338acbca9ccf0a27f75ebe3413ae25d22cd5`). The historical merge sequencing deviation (PR #17 merged out of order prior to PR #18) was explicitly reviewed, ratified, and accepted by Deeptiman.
- **Context:** PR #1 has already moved the project into `src/docuready/`, added `pyproject.toml`, and registered the `docuready` console script. **Do not repeat or reorganize the package move.**
- **Scope:** `pyproject.toml`, package import/build checks, tests, and documentation of remaining gaps from target layout.
- **Behaviour:**
  1. Verify clean editable installation using extras that actually exist in `pyproject.toml` today (currently `ui`, `generator`, `dev`; inspect before running).
  2. Build sdist and wheel in a clean environment.
  3. Verify the installed wheel imports and `docuready --help` executes cleanly from outside the repository working directory.
  4. Verify an example audit command against a synthetic packet using the installed console script.
  5. Compare current extras and dependency placement with the V2 target. Record gaps; do not add `[ocr]` or `[pymupdf]` extras in T0.3 unless authorized by a separate reviewed scope (PDF backend splitting belongs to T1.3).
  6. Preserve existing runtime behaviour and golden baseline expectations.
- **Acceptance:** *(Formally accepted by Deeptiman on 15 November 2026)*
  - [x] Clean editable install succeeds with current declared extras (`ui`, `generator`, `dev`).
  - [x] sdist and wheel build succeed without errors.
  - [x] Installed wheel imports and `docuready --help` runs from outside the repository root.
  - [x] A synthetic packet audit works using the installed console script from outside repo root.
  - [x] Golden regression tests remain unchanged and green.
  - [x] A clear inventory of remaining package-layout and dependency-extra gaps is committed (`docs/history/PACKAGE_GAP_INVENTORY_T0.md`).
- **Gate:** G0

### WS1 — Trust and compliance

#### T1.1 — Claims register and honest-claims pass
- **Scope:** `docs/CLAIMS_REGISTER.md`, `README.md`, docs under `docs/01-PRODUCT`, `docs/03-RESEARCH`, `PUBLICATION_REPORT.md`, `tests/contract/test_claims.py`.
- **Status note (15 November 2026):** Implementation merged into `main` at commit `1341540911eccebfe702d051f1b320a9dfc37f07` via PR #34. Delivered `docs/CLAIMS_REGISTER.md` (cataloguing claims CLM-001 through CLM-011 with verified/softened/removed classifications), sanitized `README.md` (re-labeled local verified privacy badge, scheme requirement rules engine, qualified 1-year validity heuristics, added prominent advisory disclaimer, removed static 88-test badge), sanitized public research documents (`PUBLICATION_REPORT.md`, `COMPETITOR_ANALYSIS.md`, `HACKNATION_IDEA_SELECTION.md`), and implemented `tests/contract/test_claims.py` (prohibiting banned phrases, enforcing disclaimer, and asserting synthetic benchmark qualification). PR #26 was reopened at Deeptiman's instruction; incorrect closure comment was corrected. Formal task acceptance pending Deeptiman's review.
- **Behaviour:** Inventory every quantitative or absolute claim (80 million, 18–32%, "every finding cites an enacted statutory clause", "DPDP compliant", "zero exfiltration", "deterministic", accuracy and ECE tables, "under 1 second"). For each: find a real source, soften, or remove. Apply the positioning sentence from ARCHITECTURE_V2 §2. Label all benchmarks **synthetic**. Replace the static "50 passing" badge with the CI badge. Fix the README test tree. Unify "MANUAL REVIEW"/"NEEDS REVIEW".
- **Acceptance:**
  - [x] Register has one row per claim with status verified / softened / removed (`docs/CLAIMS_REGISTER.md` cataloguing CLM-001 through CLM-011)
  - [x] Every remaining statistic has a source URL and retrieval date, or is removed
  - [x] No sentence in README says "legally", "guarantee", "official determination" or equivalent
  - [x] Contract test fails if a banned phrase list appears in README/docs (`tests/contract/test_claims.py`)
  - [x] README says benchmarks are synthetic, next to every benchmark table
- **Gate:** G1

#### T1.2 — Telemetry off and the no-network contract
- **Scope:** `.streamlit/config.toml`, `.gitignore`, `tests/contract/test_no_network.py`.
- **Status note (15 November 2026):** Implementation merged into `main` at commit `90b88718b24adfc97fa5b828e6c332a98a6ddc48` via PR #24. Remote CI on `main` passed across all four Python matrix jobs (3.11–3.14, run [43687049948](https://github.com/Algoryxz/DocuReady/actions/runs/43687049948) and PR run [43686824562](https://github.com/Algoryxz/DocuReady/actions/runs/43686824562)) with 100 passing tests and zero skips (12 contract tests in `tests/contract/test_no_network.py`). Exact negative proof verified locally: injecting deliberate `requests.get` into `AuditPipeline.load_and_audit_packet` immediately fails with `NetworkAccessBlockedError` intercepted at `socket.getaddrinfo`. Formal task acceptance pending Deeptiman's review.
- **Behaviour:** Commit `.streamlit/config.toml` with `[browser] gatherUsageStats = false`. Change `.gitignore` to ignore only `.streamlit/secrets.toml`. Add a test that monkeypatches `socket.socket.connect` (and `getaddrinfo`) to raise, then runs the full pipeline on every demo packet and the replacement flow.
- **Acceptance:**
  - [x] Config committed; test asserts `gatherUsageStats` is false
  - [x] No-network test passes, and a deliberate `requests.get` added in a scratch branch makes it fail (show evidence)
  - [x] `.gitignore` no longer ignores `.streamlit/` as a whole
- **Gate:** G1

#### T1.3 — PDF backend interface and licence decision (ADR-001)
- **Scope:** `ingest/pdf_backend/`, `docs/adr/ADR-001-pdf-backend.md`, `NOTICE`.
- **Status note (15 November 2026):** Initial implementation merged into `main` at commit `3250aea87c716d10db9f4e24efab2330ce9b7ce7` via PR #27; corrective implementation merged at commit `f3da08ba14affa71c02ca85cbef7958b098faeb9` via PR #35. Introduced `PDFDocumentBackend` interface (`PyMuPDFDocumentBackend`, prototype `PdfiumDocumentBackend`), eliminated dummy coordinates in PDFium backend, routed extractor through backend abstraction, enhanced `docs/adr/ADR-001-pdf-backend.md` with commercial migration pathway and `scripts/evaluate_pdf_backends.py` benchmark harness, and updated `NOTICE` dependency attribution. However, acceptance evidence is incomplete: comparative evaluation report `eval/reports/backend_comparison.md` across 8 canonical packets, 60-document, and 100-document corpora remains pending, empirical side-by-side benchmarking remains uncommitted, and `pypdfium2` is not installed by default. Task status is `review (implementation merged; empirical comparative evidence gaps and formal acceptance pending)`. Acceptance criteria remain unchecked pending empirical evaluation.
- **Behaviour:** Define `PdfBackend` (open, page count, page text with word/char bboxes, render page to image). Implement `PyMuPdfBackend` (current behaviour) and `PdfiumBackend` (`pypdfium2`; `pdfminer.six` for text bboxes if needed). Select via config, default to Pdfium **only if** the corpus comparison passes. Run the 8 packets, the 60 and 100 corpora on both backends and record: field accuracy, false-pass/false-fail counts, latency. Record each new dependency's licence from its own repository or package metadata.
- **Decision rule:** if Pdfium stays within 1 percentage point on field accuracy and shows no increase in false-pass, make it the default and move PyMuPDF to optional `[pymupdf]`. Otherwise keep PyMuPDF as default and add an AGPL notice to README/NOTICE and flag to Claude for a relicensing discussion.
- **Acceptance:**
  - [ ] Both backends pass the golden tests (or differences are listed and explained)
  - [ ] Comparison table committed under `eval/reports/backend_comparison.md`
  - [ ] ADR-001 states the outcome, the evidence, and the licence of every candidate
  - [ ] `NOTICE` lists all runtime dependencies with licences
- **Gate:** G1

#### T1.4 — Redaction and safe logging
- **Scope:** `report/redact.py`, exporters, CLI flags, logging setup.
- **Status note (15 November 2026):** Initial implementation merged into `main` at commit `a7fd1db4f61f51cb3e6e8bb5440fc7aa4aa7a876` via PR #29; corrective implementation merged at commit `72b20a7efb0bb99fe2fbffbc2e82f5b9d31dca21` via PR #33. Delivered PII masking helpers in `src/docuready/report/redact.py`, hardened `SafeLogFilter` with eager string formatting and args clearing, secure temporary upload directory context manager (`0700` permission and audited cleanup), `--no-redact` CLI flag with warning, pipeline execution safe logging, and unit tests in `tests/test_redaction_safe_logging.py`. However, verification gaps remain: a full-pipeline log capture integration test verifying that zero raw document text or PII is emitted to logs during packet auditing is missing, and end-to-end report assertion proving that synthetic Aadhaar/account/phone values are absent from default exports requires dedicated integration coverage. Task status is `review (implementation merged; verification gaps and formal acceptance pending)`. Acceptance criteria remain unchecked pending verification follow-up.
- **Behaviour:** Default-redact Aadhaar (last 4 visible), bank account (last 4), phone (last 2) in JSON, Markdown and UI. `--no-redact` requires explicit flag and prints a warning. Logs contain field keys, evidence states and rule ids, never raw values. Uploads use a `0700` temp dir deleted in a `finally`.
- **Acceptance:**
  - [ ] Test: exported JSON/MD for packets containing synthetic Aadhaar/account/phone never contains the full values by default
  - [ ] Log-capture test over a full run finds no document text values
  - [ ] Temp dir is empty after success and after an exception
- **Gate:** G1

#### T1.5 — Citation audit and `sources.yaml`
- **Scope:** `packs/generic.demo/sources.yaml`, `docs/CITATION_AUDIT.md`.
- **Status note (15 November 2026):** Initial implementation merged into `main` at commit `bf77012ff2f261f18c6faca362cb84782aacfd6d` via PR #30; corrective implementation merged at commit `ace9e5d4cb058e0a29486c31bfad770020bc8209` via PR #32. Corrected statutory citations, mapped 10 validator rule groups to sources, and explicitly corrected the previous overclaim that all 13 rules were verified: strictly 5 rules possess verified statutory or official scheme guideline citations, while 8 rules function as operational heuristics and are classified as unverified. Delivered `docs/CITATION_AUDIT.md` (statutory and administrative citation matrix, scheme/state parameter analysis), `packs/generic.demo/sources.yaml` (with issuing bodies, official URLs, retrieval dates, and scheme parameters), and enforced PyYAML schema validation in `tests/test_citation_sources.py`. Remote CI on `main` passed across all four Python matrix jobs (3.11–3.14). Formal task acceptance pending explicit review by Deeptiman.
- **Behaviour:** For each of the 10 rules, locate the real governing document (scheme guideline, notification, manual). Record title, issuing body, URL, `retrieved_on`, the exact clause number, and whether the cited clause actually supports the rule. Where it does not, mark `placeholder` and propose either a correct citation or a rewording of the rule as a **document-consistency check** without a statutory claim.
- **Non-goals:** Do not paraphrase law from memory. If a source cannot be found, write `UNVERIFIED`.
- **Acceptance:**
  - [x] 10 rows, each `verified` / `placeholder` / `unverified` with evidence (13 rows across all 10 core rule groups in `docs/CITATION_AUDIT.md` and `packs/generic.demo/sources.yaml`: exactly 5 verified statutory rules and 8 unverified operational heuristics)
  - [x] Every `verified` row has URL, retrieval date and a one-line quote-free summary of the clause (documented with official portal/gazette URLs, retrieval dates, and clause summaries)
  - [x] List of rules whose parameters (income cap, validity period, cutoffs) depend on the specific scheme or state (detailed in §3 of `docs/CITATION_AUDIT.md` and in YAML `scheme_dependent_params`)
- **Gate:** G1

### WS2 — Correctness

#### T2.1 — Status vocabulary and symmetric resolver
- **Depends on:** G0, T1.1.
- **Scope:** `domain/enums.py`, `outcome/resolver.py`, report/UI/CLI usage.
- **Behaviour:** Implement ARCHITECTURE_V2 §6 exactly: `Status`, `Raw`, reason codes, readiness, `max_severity` cap, `NOT_APPLICABLE` for exemptions (shown, not dropped), CLI exit codes 0/1/2/64.
- **Acceptance:**
  - [ ] Truth-table test covers every row of the §6 matrix
  - [ ] SATISFIED + non-VERIFIED evidence never yields PASS (property test)
  - [ ] Readiness never yields the words "eligible", "approved" or "ready to submit"
  - [ ] Golden diffs reviewed: every changed finding is explained as "was PASS, now REVIEW (CANNOT_CONFIRM)" or similar
- **Gate:** G2

#### T2.2 — Per-rule test matrix
- **Scope:** `tests/unit/test_rules_matrix.py`.
- **Behaviour:** For each of the 10 rules, parametrised cases: satisfied/verified, violated/verified, violated/provisional, violated/uncertain, indeterminate, document missing, exempt (where applicable).
- **Acceptance:**
  - [ ] ≥ 60 cases, each rule covered for every applicable row
  - [ ] Coverage report shows every branch of `outcome/resolver.py` hit
- **Gate:** G2

#### T2.3 — Match grades and the injected clock
- **Scope:** `normalize/names.py`, `dates.py`, `ids.py`, `rules/` callers, `pipeline.py`.
- **Behaviour:** Implement the §4.2 grade table. `A. Sharma` vs `Aarav Sharma` → `COMPATIBLE` (WARN at most). Ambiguous `dd/mm` vs `mm/dd` → `AMBIGUOUS`. Failed Verhoeff on Aadhaar → treat as extraction doubt, not a conflict. Remove every `datetime.now()` from rule/validation code; pipeline takes `as_of: date` (default today, always recorded in the report).
- **Acceptance:**
  - [ ] Grade tests including initials, token reorder, diacritics, common-name collisions, ambiguous dates
  - [ ] `grep` finds no `datetime.now/today` inside `rules/`, `outcome/`, `normalize/`
  - [ ] Replaying a saved packet with the same `as_of` gives identical report bodies
- **Gate:** G2

#### T2.4 — Slot validation
- **Scope:** `extract/classify.py`, pipeline intake.
- **Behaviour:** Each upload belongs to a slot. Anchor-keyword check per doc type; mismatch → `REVIEW` with `WRONG_DOCUMENT_TYPE`; unreadable → `REVIEW`.
- **Acceptance:**
  - [ ] Tests: swapped documents, blank page, wrong-language page
  - [ ] No exception for any malformed input; result is a finding
- **Gate:** G2

### WS3 — Scheme-pack engine

#### T3.1 — Pack schema, loader and lint
- **Scope:** `rules/schema.py`, `loader.py`, `lint.py`, `docuready packs lint`.
- **Behaviour:** Pydantic models for `pack.yaml` and `sources.yaml` per ARCHITECTURE_V2 §7. Lint rules: verified requires url/retrieved_on/reviewed_by; every rule has citation, remediation, max_severity; `$param` references resolve; unknown primitive is an error; `draft` rejected without `--allow-draft`.
- **Acceptance:**
  - [ ] Valid and invalid fixture packs; each lint rule has a failing fixture
  - [ ] CI runs `docuready packs lint` on all packs
- **Gate:** G3

#### T3.2 — Primitives and the `generic.demo` port
- **Depends on:** T2.1–T2.3, T3.1, T1.5.
- **Behaviour:** Implement the closed primitive set. Re-express the 10 existing rules as `packs/generic.demo/pack.yaml`. Delete the hardcoded rule logic only after equivalence passes.
- **Acceptance:**
  - [ ] All golden snapshots reproduced by the pack-driven engine (diffs only where T2.x approved changes)
  - [ ] Per-rule matrix (T2.2) runs against the pack-driven engine
  - [ ] A new rule can be added by editing YAML only (demonstrate with one example in the handoff)
  - [ ] No `eval`/`exec` in `rules/`
- **Gate:** G3

#### T3.3 — First real pack: `odisha.subhadra` (demo snapshot)
- **Behaviour:** Build from primary sources only (the scheme guidelines and official notices). Record the application window, age reference date, exclusion conditions, and required documents with their URLs and retrieval dates. Mark `status: demo_snapshot` and set `effective` to the intake window, which has closed, so reports say so plainly. Reuse any structure from the earlier standalone bundle only after checking each rule against a source.
- **Acceptance:**
  - [ ] Every parameter traces to a `sources.yaml` entry; anything unconfirmed is `UNVERIFIED` and excluded from FAIL-capable rules
  - [ ] Synthetic good/defective packets with expected findings are committed and tested
  - [ ] Report header shows "demo snapshot — intake window closed" for this pack
- **Gate:** G4

#### T3.4 — Report v2
- **Behaviour:** Implement `AuditReport` per ARCHITECTURE_V2 §4.1: `report_id` over the canonical body, `engine_manifest`, `pack` block, `as_of`, readiness, limitations, data label. Markdown renderer shows pack status, source verification badges, and the positioning disclaimer.
- **Acceptance:**
  - [ ] Same inputs → same `report_id`
  - [ ] JSON validates against a published JSON Schema committed under `docs/schema/`
  - [ ] Disclaimer present in every rendered format
- **Gate:** G4

### WS4 — Real-world readiness

#### T4.1 — Evaluation harness v2
- **Scope:** `eval/`.
- **Behaviour:** Implement §9: dev/calib/test splits with test layouts unseen in dev, headline metrics in the stated order, perturbation matrix, negative controls, bootstrap CIs, `baseline.json`, regression gate in CI, `EVAL_CARD.md` with limitations in plain language.
- **Acceptance:**
  - [ ] Calibrator fitted on `calib` only; reported numbers come from `test` only
  - [ ] ECE reported with CI and bin counts
  - [ ] False-pass rate is the first number in every summary
  - [ ] CI fails when false-pass rate worsens beyond tolerance
- **Gate:** G5

#### T4.2 — Indic OCR and numerals
- **Behaviour:** Per-slot `ocr_langs` from the pack (`eng+ori`, `eng+hin`). Normalise Odia (୦–୯) and Devanagari (०–९) digits in dates, amounts and IDs. Record language in provenance. Measure the effect on the synthetic bilingual set (T4.3) and report honestly.
- **Acceptance:**
  - [ ] Digit-normalisation unit tests for both scripts, incl. mixed scripts
  - [ ] Eval report with and without Indic languages
  - [ ] Name matching across scripts returns `AMBIGUOUS`, not `CONFLICT` (documented limitation)
- **Gate:** G5

#### T4.3 — Generator v2 (realistic synthetic documents)
- **Behaviour:** Bilingual layouts, stamps/seals overlapping text, signature blocks, varied fonts, scan artefacts. Use **new templates** for the `test` split. All output is watermarked or manifest-labelled synthetic.
- **Acceptance:**
  - [ ] ≥ 5 layouts, ≥ 3 reserved for `test`
  - [ ] Ground-truth manifest per document; generator is seeded and deterministic
- **Gate:** G5

#### T4.4 — Real-sample protocol (document only)
- **Behaviour:** Write `docs/REAL_SAMPLE_PROTOCOL.md`: start with official specimen/format certificates published by government portals, then voluntary, consented, redacted donations. Define consent text, redaction steps, storage (never in the public repo), and how results from real samples may be reported.
- **Acceptance:**
  - [ ] Protocol states what is forbidden (scraping, unconsented documents, committing real documents)
  - [ ] Lists exactly which claims become allowed once real samples are evaluated
- **Gate:** G5

### WS5 — Packaging and delivery

#### T5.1 — Container
- **Behaviour:** `Dockerfile` with pinned Tesseract and language packs, non-root user, read-only root filesystem, no network required (`docker run --network none` documented and tested in CI).
- **Acceptance:**
  - [ ] Image audits a demo packet with `--network none`
  - [ ] `engine_manifest` inside the image shows pinned versions
- **Gate:** G6

#### T5.2 — Supply chain
- **Behaviour:** Generate `requirements.lock`, run `pip-audit` in CI, generate a CycloneDX SBOM as a release asset, add `ruff` and `mypy` pre-commit/CI checks.
- **Acceptance:**
  - [ ] Lock file reproducible; CI fails on known high-severity vulnerabilities
  - [ ] SBOM attached to the release draft
- **Gate:** G6

#### T5.3 — Release
- **Behaviour:** Update `SECURITY.md` (private vulnerability reporting + email fallback), `CONTRIBUTING.md` (task protocol, claims register rule, packs), tag `v1.0.0`, write release notes that state limitations first.
- **Acceptance:**
  - [ ] G1–G5 evidence linked from the release notes
  - [ ] Release notes open with "what this tool does not do"
- **Gate:** G6

---

## 4. Kickoff prompt for Antigravity (Sprint 0) [SUPERSEDED]

> [!WARNING]
> **SUPERSEDED BY `docs/UNIFIED_ANTIGRAVITY_PROMPT.md`**
>
> The prompt below was the initial single-agent kickoff instruction and has been **superseded** for active execution.
>
> All team members (Deeptiman, Akriti, Susmita) and agent sessions should follow the three-person ownership model in [TEAM_RESPONSIBILITIES.md](TEAM_RESPONSIBILITIES.md) and execute initial verification via [UNIFIED_ANTIGRAVITY_PROMPT.md](UNIFIED_ANTIGRAVITY_PROMPT.md).
>
> The historical prompt is retained below for audit and traceability purposes only:

<details>
<summary>Archived Kickoff Prompt (Historical Reference Only)</summary>

```
You are the implementation engineer on DocuReady (repo: Algoryxz/DocuReady, branch main).
Architecture owner: Claude. Coordinator: ChatGPT. Specs are in docs/ARCHITECTURE_V2.md
and docs/BACKLOG.md. Follow the Standing Rules S1-S8 in BACKLOG.md §1.2.

Your job now is Sprint 0 only: T0.1, then T0.2, then T0.3, in that order, one branch
and one PR each. Do not start any other task.

Before writing code:
1. Read ARCHITECTURE_V2.md and BACKLOG.md fully.
2. Inspect the real repo. Where the docs disagree with the code, the code wins; list the
   differences in docs/history/CODE_AUDIT_T0.md (T0.1).

Hard constraints:
- No behaviour change in T0.3. Golden snapshots must stay byte-identical.
- Never invent results. If a command fails or cannot run, report it as UNVERIFIED with the error.
- No real personal data anywhere.
- Return the handoff packet (BACKLOG.md §1.3) after each task and stop for review.
  Do not proceed to the next task until I confirm ACCEPT.

Begin with T0.1.
```

</details>

---

## 5. Definition of done (every task)

- Acceptance criteria all checked, each with evidence in the handoff.
- Tests added or updated; full suite green locally and in CI.
- No new unexplained golden diffs.
- Docs touched are consistent with `CLAIMS_REGISTER.md`.
- Dependencies, if any, recorded in `NOTICE` with licence.
