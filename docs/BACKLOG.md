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
- **S4** No new dependency without recording its licence in `NOTICE`. No AGPL/GPL additions without a Claude-approved ADR.
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
| **G0** Baseline frozen | Safe to refactor | T0.1–T0.3 accepted; golden snapshots green; CI green on remote |
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

### Sprint 0 — Baseline (blocks everything)

#### T0.1 — Characterise the current behaviour
- **Why:** We reviewed docs, not code. Freeze reality before changing it.
- **Scope:** `tests/golden/`, `scripts/freeze_golden.py`, `docs/history/CODE_AUDIT_T0.md`.
- **Behaviour:** For each of the 8 packets in `synthetic_data/`, run the current pipeline and save the full finding list (rule id, severity, fields, evidence states) as JSON. Add a test that re-runs and diffs against the golden file. Also write a short audit listing: real module names, the actual rule ids/citations in `validator.py`, the thresholds in `calibrator.py`, and any network or file-write calls found by grep.
- **Acceptance:**
  - [ ] 8 golden files committed; test fails if any finding changes
  - [ ] Audit file lists every rule id with its current citation text, verbatim
  - [ ] Audit file lists every place that touches network, disk writes or `datetime.now()`
  - [ ] README's test-file tree compared to the real `tests/` and differences listed
- **Gate:** G0

#### T0.2 — CI that exercises OCR
- **Scope:** `.github/workflows/tests.yml`.
- **Behaviour:** Install `tesseract-ocr`, `tesseract-ocr-eng`, `tesseract-ocr-ori`, `tesseract-ocr-hin` in CI. Matrix 3.10/3.11/3.12. Cache pip. Fail on warnings from our own code.
- **Acceptance:**
  - [ ] Latest run on `main` is green and visible in the handoff (link or log tail)
  - [ ] A test that needs OCR is shown to have run (not skipped)
  - [ ] Badge in README reflects the real workflow status
- **Gate:** G0

#### T0.3 — Package layout (no behaviour change)
- **Depends on:** T0.1, T0.2.
- **Scope:** `pyproject.toml`, move `src/*.py` into `src/docuready/...` per ARCHITECTURE_V2 §10.
- **Behaviour:** Pure move + import fixes. Provide console script `docuready` (replaces `python src/cli.py`). Keep thin compatibility shims for old paths for one release. Move `requirements.txt` content into `pyproject.toml`; `pytest`/`pytest-cov` go to `[dev]`; Streamlit to `[ui]`; Tesseract wrapper to `[ocr]`.
- **Non-goals:** any logic change, any rename of rules or statuses.
- **Acceptance:**
  - [ ] Golden tests unchanged and green
  - [ ] `pip install -e .[ui,ocr,dev]` works in a clean venv
  - [ ] `docuready audit --packet synthetic_data/pkt_02_name_mismatch --output r.json` works
  - [ ] Zero edits to `tests/golden/*`
- **Gate:** G0

### WS1 — Trust and compliance

#### T1.1 — Claims register and honest-claims pass
- **Scope:** `docs/CLAIMS_REGISTER.md`, `README.md`, docs under `docs/01-PRODUCT`, `docs/03-RESEARCH`, `PUBLICATION_REPORT.md`, `tests/contract/test_claims.py`.
- **Behaviour:** Inventory every quantitative or absolute claim (80 million, 18–32%, "every finding cites an enacted statutory clause", "DPDP compliant", "zero exfiltration", "deterministic", accuracy and ECE tables, "under 1 second"). For each: find a real source, soften, or remove. Apply the positioning sentence from ARCHITECTURE_V2 §2. Label all benchmarks **synthetic**. Replace the static "50 passing" badge with the CI badge. Fix the README test tree. Unify "MANUAL REVIEW"/"NEEDS REVIEW".
- **Acceptance:**
  - [ ] Register has one row per claim with status verified / softened / removed
  - [ ] Every remaining statistic has a source URL and retrieval date, or is removed
  - [ ] No sentence in README says "legally", "guarantee", "official determination" or equivalent
  - [ ] Contract test fails if a banned phrase list appears in README/docs
  - [ ] README says benchmarks are synthetic, next to every benchmark table
- **Gate:** G1

#### T1.2 — Telemetry off and the no-network contract
- **Scope:** `.streamlit/config.toml`, `.gitignore`, `tests/contract/test_no_network.py`.
- **Behaviour:** Commit `.streamlit/config.toml` with `[browser] gatherUsageStats = false`. Change `.gitignore` to ignore only `.streamlit/secrets.toml`. Add a test that monkeypatches `socket.socket.connect` (and `getaddrinfo`) to raise, then runs the full pipeline on every demo packet and the replacement flow.
- **Acceptance:**
  - [ ] Config committed; test asserts `gatherUsageStats` is false
  - [ ] No-network test passes, and a deliberate `requests.get` added in a scratch branch makes it fail (show evidence)
  - [ ] `.gitignore` no longer ignores `.streamlit/` as a whole
- **Gate:** G1

#### T1.3 — PDF backend interface and licence decision (ADR-001)
- **Scope:** `ingest/pdf_backend/`, `docs/adr/ADR-001-pdf-backend.md`, `NOTICE`.
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
- **Behaviour:** Default-redact Aadhaar (last 4 visible), bank account (last 4), phone (last 2) in JSON, Markdown and UI. `--no-redact` requires explicit flag and prints a warning. Logs contain field keys, evidence states and rule ids, never raw values. Uploads use a `0700` temp dir deleted in a `finally`.
- **Acceptance:**
  - [ ] Test: exported JSON/MD for packets containing synthetic Aadhaar/account/phone never contains the full values by default
  - [ ] Log-capture test over a full run finds no document text values
  - [ ] Temp dir is empty after success and after an exception
- **Gate:** G1

#### T1.5 — Citation audit and `sources.yaml`
- **Scope:** `packs/generic.demo/sources.yaml`, `docs/CITATION_AUDIT.md`.
- **Behaviour:** For each of the 10 rules, locate the real governing document (scheme guideline, notification, manual). Record title, issuing body, URL, `retrieved_on`, the exact clause number, and whether the cited clause actually supports the rule. Where it does not, mark `placeholder` and propose either a correct citation or a rewording of the rule as a **document-consistency check** without a statutory claim.
- **Non-goals:** Do not paraphrase law from memory. If a source cannot be found, write `UNVERIFIED`.
- **Acceptance:**
  - [ ] 10 rows, each `verified` / `placeholder` / `unverified` with evidence
  - [ ] Every `verified` row has URL, retrieval date and a one-line quote-free summary of the clause
  - [ ] List of rules whose parameters (income cap, validity period, cutoffs) depend on the specific scheme or state
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
