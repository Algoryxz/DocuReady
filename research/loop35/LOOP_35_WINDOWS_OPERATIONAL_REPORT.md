# DOCUREADY — LOOP 35 WINDOWS OPERATIONAL QUALIFICATION REPORT

Evaluated frozen Loop 10 Windows artifacts without modification:
- **Frozen Sidecar Binary Health Handshake:** Executed `{"method": "health"}` against `docuready_sidecar.exe`.
  - Executed: `True`
  - Return code: `0`
  - Startup & health latency: `9877.01 ms`
  - Output: `{"protocol":1,"id":"health-35","ok":true,"result":{"sidecar":"docuready-python","protocol":1,"engine_version":"0.1.0","python":"3.12.10","pdf_backend":"pymupdf","ocr_available":true,"ocr_languages":["eng","hin","ori"],"ocr_source":"bundled_resource","is_bundled":true,"ocr_error":null,"tesseract_vers`
- **Packaged Desktop Parity:** Verified via Electron test `Packaged Sidecar Binary executes health and runs audit seamlessly` and `End-to-End Synthetic Packet Audit Parity`.
- **Installer/Uninstall Note:** Interactive GUI installer (`DocuReady-0.1.0-Setup.exe`) UI clicks and Defender SmartScreen prompts are not automated in headless CLI; binary integrity and portable sidecar execution are verified.
