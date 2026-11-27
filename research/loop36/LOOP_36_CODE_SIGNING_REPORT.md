# DOCUREADY — LOOP 36 CODE SIGNING & WINDOWS TRUST REPORT

- **Authenticode Check (`Get-AuthenticodeSignature`):**
  - `DocuReady.exe`: `NotSigned`
  - `docuready_sidecar.exe`: `NotSigned`
  - `DocuReady-0.1.0-Setup.exe`: `NotSigned`
- **Operational Implication (`BUG-036-001`):** Unsigned binaries will trigger Windows Defender SmartScreen warnings on clean end-user machines.
