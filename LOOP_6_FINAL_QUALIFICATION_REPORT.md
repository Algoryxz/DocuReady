# DOCUREADY — LOOP 6 FINAL QUALIFICATION REPORT
## Release Integrity, Windows Packaging Hardening & Evidence Corrections

**Evaluation date:** 2026-11-16  
**Repository:** `Algoryxz/DocuReady`  
**Working branch:** `feat/loop6-release-integrity-and-reproducibility`  
**Latest reviewed commit:** `4d7127538b04401aafa52e9f9ede6704b1f7ee50`  
**Pull request:** [#76 — Windows desktop startup and release qualification](https://github.com/Algoryxz/DocuReady/pull/76)  
**PR target:** `feat/loop5-independent-validation-and-demo`  
**Starting commit:** `22c75efecc162e058a7b4dd238f0d5eb8a0a6a82`

## 1. Executive decision

**Status: DRAFT — WINDOWS BUILD AND QUALIFICATION REQUIRED. NOT APPROVED FOR PRODUCTION DISTRIBUTION.**

The repository has received code-level packaging and startup hardening. A Windows GitHub Actions workflow now builds the Python sidecar, stages Tesseract, type-checks and tests the Electron app, creates the Squirrel installer and portable ZIP, and invokes a clean-profile qualification script.

The workflow has not been independently observed completing successfully in this review. No new Windows executable has been built or verified here. Existing binary hashes in earlier reports refer to previous artifacts and must not be treated as hashes of this branch's updated source.

## 2. Code changes in this qualification branch

1. **Packaged sidecar enforcement — `apps/desktop/src/main/sidecar.ts`:** packaged builds now fail explicitly when the bundled sidecar executable is missing instead of silently falling back to host Python.
2. **Startup health gate — `apps/desktop/src/main.ts`:** the application checks the sidecar JSON-RPC health response before showing the UI. Packaged builds require available bundled OCR. Startup failures show an error dialog instead of leaving an apparently usable but nonfunctional application. Development builds may use system OCR or run without OCR.
3. **PyInstaller source path — `sidecar/docuready_sidecar.spec`:** corrected the analysis path to the canonical repository-root `src/docuready` package.
4. **Windows qualification harness — `scripts/verify_clean_windows_runtime.ps1`:** now exercises portable extraction, bundled sidecar health, clean/degraded/conflict synthetic packet audits, visible Electron window launch, Squirrel install, installed app launch, and uninstall. The harness must run on Windows before any pass claim is made.
5. **Windows build workflow — `.github/workflows/windows-release-qualification.yml`:** added a Windows 2022 build/test/qualification job, including Python tests, Electron type-checking and tests, installer/ZIP generation, and artifact capture.
6. **Network audit semantics — `scripts/network_privacy_audit.py`:** the output now describes sampled socket observations and records the final observed process tree. A zero sample count is not labelled proof of zero egress.
7. **Documentation:** removed unsupported offline-only and zero-PII guarantees from the desktop README.

## 3. Windows executable qualification

The new Windows workflow is the required release gate. It must prove all of the following on a Windows runner:

- PyInstaller produces `sidecar/dist/docuready_sidecar/docuready_sidecar.exe`.
- English and OSD Tesseract trained data are staged beside the sidecar.
- Python tests, Electron tests, and TypeScript checks pass.
- Electron Forge produces both expected distributions:
  - `apps/desktop/out/make/squirrel.windows/x64/DocuReady-0.1.0-Setup.exe`
  - `apps/desktop/out/make/zip/win32/x64/DocuReady-win32-x64-0.1.0.zip`
- The portable app opens a visible window and its bundled sidecar completes health and synthetic packet checks.
- The Squirrel installer installs the app, the installed app opens a visible window, the bundled sidecar passes its health check, and uninstall removes the installed executable and updater.

**Current result:** pending execution. The connected review environment does not provide Windows PowerShell or a Windows desktop runtime. Do not claim the EXE is working until the Windows workflow is green and the generated artifact is downloaded and smoke-tested.

## 4. Network and privacy evidence

The network monitor uses 50ms `psutil.Process.net_connections()` polling. It is not ETW, Windows Filtering Platform, kernel event tracing, or packet capture. Short-lived sockets can be missed, and unrelated system services and traffic outside the selected process tree are not covered.

Permitted statement: **no connections were visible in the recorded process samples.**

Prohibited statements: zero network egress, system-wide network isolation, air-gap operation, or guaranteed absence of outbound traffic.

Renderer CSP is a renderer security boundary, not a firewall for Electron main-process or native child-process traffic.

## 5. Licensing and compliance

- PyMuPDF remains bundled under AGPLv3. The repository's Apache-2.0 license does not relicense it.
- Process separation and stdio communication do not, by themselves, resolve AGPL obligations.
- The PDFium adapter is incomplete; its word extraction method is not implemented. A switch to PDFium is not currently a drop-in fix.
- **Legal distribution clearance remains unresolved.** Obtain qualified review of the combined application, notices, source obligations, and distribution model before public binary distribution.
- DPDP wording is a design-intent statement, not certification or a legal compliance determination.
- Statutory mappings are candidate references requiring scheme-specific validation, not legal advice.
- Aadhaar checksum validation does not authenticate identity or query UIDAI. IFSC syntax checks do not verify a live bank registry.

## 6. Historical metrics — attribution and limits

Earlier reports supplied these figures: 450 Python tests passed and 2 skipped; 21 desktop tests passed; 28/28 extracted fields matched an independent auditor; 10/10 demo cycles completed; 60.63ms vector audit; 191.39MB peak RSS in a 20-document OCR stress test; and 91.7% on a controlled degraded-scan set.

These are historical reported results, not results from the new Windows workflow. They have not been rerun against the current branch in this review. The 91.7% result is not established real-world accuracy. Synthetic corpus results must remain labelled synthetic.

The earlier 30% scholarship rejection/delay statistic remains withdrawn because a suitable primary source was not established.

## 7. Existing binary hashes

Previously reported installer, ZIP, nupkg, and unpacked EXE hashes are historical. They predate the latest source changes and are **not** provenance for the current branch. Generate new hashes from the successful Windows workflow artifact and record them with the workflow run ID and commit SHA.

## 8. Remaining release gates

1. Obtain a green run of the Windows release qualification workflow.
2. Download and independently launch the generated installer and portable ZIP on a clean Windows 10/11 x64 machine.
3. Capture the actual Windows qualification log, installer/ZIP hashes, workflow run URL, and tested commit SHA.
4. Resolve PyMuPDF AGPL distribution obligations with qualified legal review or replace it with a complete compatible backend.
5. Verify each statutory mapping against official primary sources.
6. Keep network claims limited to the exact scope and method of any future event-based audit.

## 9. Final recommendation

**Competition demo candidate after Windows qualification passes. Production distribution remains blocked by Windows verification and AGPL legal clearance.**

This report supersedes earlier Loop 6 wording that described production approval, kernel-level network verification, or completed Squirrel installer testing.
