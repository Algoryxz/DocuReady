# DOCUREADY — LOOP 36 PACKAGING AUDIT

- **Electron Forge (`apps/desktop/forge.config.ts`):** Uses `asar: true`, `MakerSquirrel` (`DocuReady-0.1.0-Setup.exe`), `MakerZIP` (`win32`), `VitePlugin`, and `extraResource` bundling `sidecar/dist/docuready_sidecar`.
- **OCR Bundling:** Bundles `tesseract.exe`, `eng`, `hin`, `ori`, `osd` traineddata, plus 122 DLLs (`dependency_inventory.json`).
- **Finding (`BUG-036-002`):** Extra Tesseract training utilities (18 EXEs) are bundled unnecessarily.
