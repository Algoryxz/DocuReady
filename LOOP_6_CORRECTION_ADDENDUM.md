# DOCUREADY — LOOP 6 INDEPENDENT CORRECTION ADDENDUM

**Date:** 2026-11-16  
**Repository:** Algoryxz/DocuReady  
**Branch:** feat/loop6-release-integrity-and-reproducibility  
**Reviewed commit:** 87f2534dbd7977c4591579ed0b378641c20bb1f1

## Purpose

This addendum corrects overstatements in the original Loop 6 qualification report after inspection of the committed scripts, telemetry JSON, and documentation. It supersedes any conflicting “approved,” “kernel-level,” “zero network traffic verified,” or “both distributions clean-machine verified” wording.

## Findings established from repository contents

### 1. Source provenance

GitHub comparison confirms that commit `87f2534dbd7977c4591579ed0b378641c20bb1f1` is one commit ahead of `22c75efecc162e058a7b4dd238f0d5eb8a0a6a82`. The comparison against the current remote `feat/electron-desktop-foundation` branch reports its tip as `e400e31832a9827052c084c8533f272f75f1d391`; therefore the older `d9323ea` label is not the current branch tip. A compare/create-PR URL is not evidence that a PR has been created.

### 2. Network audit scope

The committed monitor calls `psutil.Process.net_connections(kind="all")` in a 50ms polling loop. It is not kernel event tracing. The saved `network_audit_summary.json` reports zero observed connections, but its recorded runtime process tree contains only `DocuReady.exe`, and the listed PIDs do not identify the sidecar or Tesseract. Polling can miss short-lived connections. CSP `connect-src 'self'` applies to renderer requests and does not constrain every native/main-process capability.

**Approved wording:** “No network connections were observed in the recorded samples for the processes visible to the polling monitor.”  
**Withdrawn wording:** “Kernel-level zero network egress verified,” “zero network traffic verified,” and any universal system-wide guarantee.

### 3. Clean Windows validation

The checked-in PowerShell harness declares a `$SetupExe` parameter but never uses it. It extracts the Portable ZIP, directly tests the sidecar, and launches `DocuReady.exe` for a short process-liveness check. It does not install or uninstall the Squirrel package, and the short launch does not prove full UI rendering or end-to-end desktop interaction.

**Approved wording:** “Portable package and sidecar checks passed in a scrubbed PATH environment, according to the supplied test report.”  
**Not established:** Squirrel clean-machine install/uninstall, complete desktop UI workflow, or installer cleanup.

### 4. AGPLv3 licensing

The packaged sidecar includes PyMuPDF under AGPLv3. The project’s Apache-2.0 license does not relicense PyMuPDF. Stdio communication and process isolation do not, without legal analysis, establish that copyleft obligations are avoided. The PDFium adapter is incomplete because `get_words()` raises `NotImplementedError`.

**Status:** AGPLv3 is disclosed; legal distribution clearance remains open. This is an engineering record, not legal advice.

### 5. Unsupported prevalence and accuracy claims

- Withdraw “over 30% of scholarship applications” unless a primary, independently verifiable source is added.
- Describe 91.7% only as a result on the specific controlled degraded-scan test set. Do not call it field or real-world accuracy without corpus provenance.
- Keep synthetic exact-match claims explicitly scoped to the frozen synthetic baseline.

## Release disposition

**CONDITIONAL — NOT APPROVED FOR PRODUCTION DISTRIBUTION.**

The current evidence supports a competition demonstration candidate, not a production-certified release. Remaining release gates:

1. Run a clean Windows Squirrel install, full UI workflow, uninstall, and residual-file test.
2. Perform complete process-tree network capture using Windows Filtering Platform/ETW or equivalent event-based tooling.
3. Obtain qualified legal review of the packaged AGPLv3 component and distribution obligations.
4. Verify every statutory citation against primary official source documents and remove unsupported references.
5. Publish only artifacts built from the exact reviewed commit, with verified checksums and an actual release asset URL.


### 6. Evidence files absent from the reviewed branch

The report's evidence index names `docs/network_audit_logs/network_audit_raw.log` and `docs/clean_machine_validation.log`, but both paths return 404 when fetched from the reviewed branch. The summary JSON exists; the raw monitoring and clean-machine logs do not appear in the committed branch at those paths. Treat the numerical observations as claims in the report, not independently inspectable raw evidence, until the logs are committed or attached. The referenced Windows screenshots are also not listed among the changed files reviewed here.

### 7. Documentation corrections

The root README has been revised to remove the unsupported 30% prevalence statistic, narrow privacy language, distinguish project-authored Apache-2.0 code from AGPLv3 PyMuPDF, mark PDFium as incomplete, and qualify the statutory reference table as candidate mappings requiring scheme-specific verification. Aadhaar checksum validation and IFSC syntax checking are explicitly distinguished from identity or bank-registry verification.
