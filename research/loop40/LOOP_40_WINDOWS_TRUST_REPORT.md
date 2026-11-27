# Loop 40 Windows Release Trust Report

**Date:** 2026-11-27  
**Branch:** `loop-40-performance-multilingual-and-windows-qualification`  
**Protected Baseline:** Loop 10 (`bdc403a601f88008c43c0630f5e8c71ce22c9977`)

---

## 1. Authenticode Signature Verification

Executed `Get-AuthenticodeSignature` on the three Windows executable/installer artifacts in `apps/desktop/out/`:

| Artifact | Path | Status | SignerCertificate |
| :--- | :--- | :--- | :--- |
| Desktop App | `apps/desktop/out/DocuReady-win32-x64/DocuReady.exe` | `NotSigned` | None |
| Python Sidecar | `apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar/docuready_sidecar.exe` | `NotSigned` | None |
| Squirrel Installer | `apps/desktop/out/make/squirrel.windows/x64/DocuReady-0.1.0-Setup.exe` | `NotSigned` | None |

---

## 2. Signing Infrastructure & Clean-VM Gate Status

Checked host certificate stores (`Cert:\CurrentUser\My`, `Cert:\LocalMachine\My` with `-CodeSigningCert`) and `signtool` availability:
- **Code-Signing Certificates:** None installed (`0` certificates found).
- **`signtool.exe`:** Not present on `PATH`.
- **Clean-Machine / SmartScreen / Defender Qualification:** No isolated clean Windows VM is available on this host to measure SmartScreen reputation or fresh-OS install behavior.

| Gate | Status | Evidence / Reason |
| :--- | :--- | :--- |
| Authenticode signing of `DocuReady.exe`, `docuready_sidecar.exe`, `DocuReady-0.1.0-Setup.exe` | **BLOCKED** | `Get-AuthenticodeSignature` reports `NotSigned`; no code-signing certificate or `signtool` available on host. |
| Clean-VM install & Windows SmartScreen / Defender verification | **BLOCKED** | No clean Windows VM environment available on host. |
| Loop 10 frozen artifact SHA-256 integrity | **PASS** | All 5 Loop 10 artifacts recomputed via `Get-FileHash` and match bit-for-bit. |

---

## 3. Honest Release Posture

DocuReady Loop 10 and Loop 40 Windows binaries remain **unsigned** (`NotSigned`). Any external Windows distribution outside controlled local/offline evaluation requires a valid EV or organization Authenticode certificate, `signtool` timestamping, and clean-VM SmartScreen verification before public release.
