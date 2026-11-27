# DOCUREADY — LOOP 41 WINDOWS RELEASE TRUST REPORT

**Verdict:** **`BLOCKED`** (Signing credentials and clean Windows VM unavailable in this environment).

## 1. Observed Authenticode Status (`Get-AuthenticodeSignature`)

| Binary | Status | Signer |
|---|---|---|
| `apps\desktop\out\DocuReady-win32-x64\DocuReady.exe` | `NotSigned` | None |
| `apps\desktop\out\DocuReady-win32-x64\resources\docuready_sidecar\docuready_sidecar.exe` | `NotSigned` | None |
| `apps\desktop\out\make\squirrel.windows\x64\DocuReady-0.1.0-Setup.exe` | `NotSigned` | None |

- **Certificate Store Check (`Cert:\CurrentUser\My`, `Cert:\LocalMachine\My`):** `CodeSigningCertCount = 0`.
- **SmartScreen & Clean-Machine Installation:** Cannot be cleared without a valid Authenticode certificate + RFC 3161 timestamp and an isolated clean Windows VM. Reported honestly as `BLOCKED`.
