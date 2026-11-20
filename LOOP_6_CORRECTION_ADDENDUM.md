# DOCUREADY — LOOP 6 INDEPENDENT CORRECTION ADDENDUM

**Date:** 2026-11-16  
**Repository:** Algoryxz/DocuReady  
**Branch:** feat/loop6-release-integrity-and-reproducibility  
**Reviewed source commit:** 4d7127538b04401aafa52e9f9ede6704b1f7ee50
**Current report commit:** updated in the active qualification branch
**Pull request:** https://github.com/Algoryxz/DocuReady/pull/76

## Purpose

This addendum corrects overstatements in the original Loop 6 qualification report after inspection of the committed scripts, telemetry JSON, and documentation. It supersedes any conflicting “approved,” “kernel-level,” “zero network traffic verified,” or “both distributions clean-machine verified” wording.

## Findings established from repository contents

### 1. Source provenance

The active qualification branch descends from `22c75efecc162e058a7b4dd238f0d5eb8a0a6a82` and is proposed for review in draft PR #76 targeting `feat/loop5-independent-validation-and-demo`. The comparison against the current remote `feat/electron-desktop-foundation` branch reports its tip as `e400e31832a9827052c084c8533f272f75f1d391`; therefore the older `d9323ea` label is not the current branch tip. A compare/create-PR URL is not evidence that a PR has been created.

### 2. Network audit scope

The committed monitor calls `psutil.Process.net_connections(kind="all")` in a 50ms polling loop. It is not kernel event tracing. The saved `network_audit_summary.json` reports zero observed connections, but its recorded runtime process tree contains only `DocuReady.exe`, and the listed PIDs do not identify the sidecar or Tesseract. Polling can miss short-lived connections. CSP `connect-src 'self'` applies to renderer requests and does not constrain every native/main-process capability.

**Approved wording:** “No network connections were observed in the recorded samples for the processes visible to the polling monitor.”  
**Withdrawn wording:** “Kernel-level zero network egress verified,” “zero network traffic verified,” and any universal system-wide guarantee.

### 3. Clean Windows validation

The original harness had an unused `$SetupExe` parameter and did not install the Squirrel package. The current branch replaces it with a Windows qualification harness that is designed to test the portable ZIP, sidecar health, clean/degraded/conflict synthetic packet audits, visible app-window launch, Squirrel install, installed app launch, and uninstall. These are test steps in code, not passed results: the harness has not yet been run on Windows in this review.

**Current status:** Windows qualification is pending. The new harness must pass on a Windows runner before either distribution can be called verified.

### 4. AGPLv3 licensing

The packaged sidecar includes PyMuPDF under AGPLv3. The project’s Apache-2.0 license does not relicense PyMuPDF. Stdio communication and process isolation do not, without legal analysis, establish that copyleft obligations are avoided. The PDFium adapter is incomplete because `get_words()` raises `NotImplementedError`.

**Status:** AGPLv3 is disclosed; legal distribution clearance remains open. This is an engineering record, not legal advice.

### 5. Unsupported prevalence and accuracy claims

- Withdraw “over 30% of scholarship applications” unless a primary, independently verifiable source is added.
- Describe 91.7% only as a result on the specific controlled degraded-scan test set. Do not call it field or real-world accuracy without corpus provenance.
- Keep synthetic exact-match claims explicitly scoped to the frozen synthetic baseline.

## Release disposition

**CONDITIONAL — NOT APPROVED FOR PRODUCTION DISTRIBUTION.**

The current source branch includes startup fail-fast checks, a corrected PyInstaller source path, a Windows build/qualification workflow, and a stronger install/launch/uninstall harness. The Windows workflow result is not yet verified. The current evidence therefore supports neither a production-certified release nor a confirmed working EXE. Remaining release gates:

1. Obtain a green run of `.github/workflows/windows-release-qualification.yml` and independently smoke-test its generated installer and ZIP.
2. Perform complete process-tree network capture using Windows Filtering Platform/ETW or equivalent event-based tooling.
3. Obtain qualified legal review of the packaged AGPLv3 component and distribution obligations.
4. Verify every statutory citation against primary official source documents and remove unsupported references.
5. Publish only artifacts built from the exact reviewed commit, with verified checksums and an actual release asset URL.


### 6. Evidence files absent from the reviewed branch

The report's evidence index names `docs/network_audit_logs/network_audit_raw.log` and `docs/clean_machine_validation.log`, but both paths return 404 when fetched from the reviewed branch. The summary JSON exists; the raw monitoring and clean-machine logs do not appear in the committed branch at those paths. Treat the numerical observations as claims in the report, not independently inspectable raw evidence, until the logs are committed or attached. The referenced Windows screenshots are also not listed among the changed files reviewed here.

### 7. Documentation corrections

The root README has been revised to remove the unsupported 30% prevalence statistic, narrow privacy language, distinguish project-authored Apache-2.0 code from AGPLv3 PyMuPDF, mark PDFium as incomplete, and qualify the statutory reference table as candidate mappings requiring scheme-specific verification. Aadhaar checksum validation and IFSC syntax checking are explicitly distinguished from identity or bank-registry verification.


### 8. Windows packaging hardening added after the initial correction

- Packaged Electron builds no longer silently fall back to host Python when the sidecar executable is missing.
- Packaged startup now checks the sidecar health handshake and requires bundled OCR before presenting the UI as ready. Development mode can still use system OCR or operate without OCR.
- The PyInstaller spec now points to the repository-root Python package at `src/docuready`.
- The new Windows workflow builds the sidecar, stages Tesseract, runs tests, builds both Windows distributions, and invokes the clean-machine harness.
- The desktop README no longer claims system-wide offline operation or zero PII leakage.

These changes are source-level fixes. They do not prove the generated EXE works until the Windows workflow passes. Existing binary hashes in older reports are stale for this source branch.
