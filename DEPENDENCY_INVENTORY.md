# DOCUREADY — COMPLETE DEPENDENCY INVENTORY

**Milestone:** Loop 6 — Release Integrity, Claims Audit & Independent Reproducibility  
**Date:** 2026-11-16  
**Auditor:** Antigravity Release Engineer / Independent Auditor  
**Repository:** `Algoryxz/DocuReady`  
**Distribution Target:** Windows x64 Native Executable & Sidecar Runtime  

---

## 1. Native Binaries & Bundled Runtime Engines

These binaries are bundled directly within the distribution at `resources/docuready_sidecar/tesseract/` and `resources/docuready_sidecar/`:

| Binary / Asset | Bundled Path | Version | Vendor / Upstream | Stated License | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`DocuReady.exe`** | `out/DocuReady-win32-x64/` | 0.1.0 | DocuReady Team / Electron | Apache 2.0 (App) / MIT (Shell) | Main application host executable. |
| **`docuready_sidecar.exe`** | `resources/docuready_sidecar/` | 0.1.0 | DocuReady Team / PyInstaller | Apache 2.0 (App) / GPL/Custom (PyInstaller bootloader) | Packaged Python sidecar executable. |
| **`tesseract.exe`** | `.../tesseract/` | 5.4.0.20240606 | Google LLC / UB-Mannheim | Apache 2.0 | Offline OCR command-line engine. |
| **`leptonica-1.84.1.dll`** | `.../tesseract/` | 1.84.1 | Dan Bloomberg | BSD 2-Clause | Image processing library for Tesseract. |
| **`libpng16.dll`** | `.../tesseract/` | 1.6.43 | PNG Development Group | PNG / zlib License | PNG decoding library. |
| **`libjpeg-62.dll`** | `.../tesseract/` | 6b / turbo | Independent JPEG Group | IJG License | JPEG decoding library. |
| **`libtiff-5.dll`** | `.../tesseract/` | 4.5.1 | Sam Leffler / Silicon Graphics | Libtiff (MIT-like) | TIFF raster decoding library. |
| **`libwebp-7.dll`** | `.../tesseract/` | 1.3.2 | Google LLC | BSD 3-Clause | WebP image format support. |
| **`zlib1.dll`** | `.../tesseract/` | 1.3.1 | Jean-loup Gailly & Mark Adler | zlib License | Deflate compression. |
| **`eng.traineddata`** | `.../tesseract/tessdata/` | 4.0.0 / 4.1.0 | Google LLC (tessdata_fast) | Apache 2.0 | English neural net OCR recognition model. |
| **`osd.traineddata`** | `.../tesseract/tessdata/` | 4.0.0 | Google LLC (tessdata_fast) | Apache 2.0 | Orientation and Script Detection model. |

---

## 2. Python Sidecar Package Dependencies

Extracted from `pyproject.toml` and bundled into `sidecar/dist/docuready_sidecar/`:

| Package Name | Pinned / Required Version | Resolved Version in Sidecar | License | Upstream Author / Project | Role in Architecture |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`pymupdf`** | `==2.1` | 1.24.1 / 1.24.10 (PyMuPDF) | **AGPLv3** | Artifex Software, Inc. | Core PDF parser, vector geometry extraction, bounding box coordinates, and raster page rendering. |
| **`pydantic`** | `>=2.0.0` | 2.10.4 | MIT | Samuel Colvin & Pydantic contributors | Typed domain models, JSON schema serialization, strict field validation. |
| **`pydantic-core`** | Transitive | 2.27.2 | MIT | Samuel Colvin & Pydantic contributors | Rust-accelerated core validation backend. |
| **`pillow`** | `>=10.0.0` | 11.1.0 | HPND / MIT-like | Alex Clark & Pillow contributors | Image loading, format conversion, and DPI scaling for OCR. |
| **`numpy`** | `>=1.24.0` | 2.2.1 | BSD 3-Clause | NumPy Developers | Numerical array representations for calibrator and vector distances. |
| **`pytesseract`** | `>=0.3.10` | 0.3.13 | Apache 2.0 | Samuel Hoffstaetter & contributors | Python wrapper invoking bundled `tesseract.exe` via stdio pipes. |
| **`typing-extensions`** | Transitive | 4.12.2 | PSF License | Python Software Foundation | Backward compatibility typing utilities. |
| **`annotated-types`** | Transitive | 0.7.0 | MIT | Pydantic contributors | Reusable constraint annotations. |

---

## 3. Desktop Application Dependencies (Node.js / npm)

Extracted from `apps/desktop/package.json` and bundled into `app.asar`:

### Production Runtime Dependencies:

| Package Name | Version | License | Upstream Maintainer | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **`pdfjs-dist`** | `^6.5.438` | Apache 2.0 | Mozilla Foundation | In-browser client-side PDF rendering, canvas rasterization, and coordinate translation. |

### Packaged Dev / Shell Dependencies:

| Package Name | Version | License | Upstream Maintainer | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **`electron`** | `45.3.2` | MIT | OpenJS Foundation / Electron | Desktop cross-platform shell (Chromium + Node.js). |
| **`react`** | `^19.2.0` | MIT | Meta Platforms, Inc. | Declarative user interface runtime. |
| **`react-dom`** | `^19.2.0` | MIT | Meta Platforms, Inc. | DOM renderer for React. |
| **`lucide-react`** | `^1.16.0` | ISC / MIT | Lucide Contributors | Local SVG icon library. |
| **`@electron-forge/cli`** | `8.0.1` | MIT | Electron Forge Team | Packaging and build orchestration CLI. |
| **`@electron-forge/maker-squirrel`** | `^8.0.1` | MIT | Electron Forge Team | Windows installer maker using Squirrel.Windows. |
| **`@electron-forge/maker-zip`** | `8.0.1` | MIT | Electron Forge Team | Standalone portable ZIP maker. |
| **`@electron-forge/plugin-vite`** | `8.0.1` | MIT | Electron Forge Team | Vite integration for Electron Main/Preload/Renderer. |
| **`vite`** | `^8.0.0` | MIT | Yuxi (Evan) You & Vite Contributors | Modern frontend build tool and bundler. |
| **`typescript`** | `^5.9.3` | Apache 2.0 | Microsoft Corporation | Static type checking and transpilation. |

---

## 4. Transitive Build & Distribution Dependencies

| Component | Source / Host | License | Impact on Distributed Binaries |
| :--- | :--- | :--- | :--- |
| **`Squirrel.exe`** | `electron-winstaller` vendor | MIT | Bundled as the setup stub for `DocuReady-0.1.0-Setup.exe`. |
| **`nuget.exe`** | `electron-winstaller` vendor | Apache 2.0 | Used at build time only to create the `.nupkg` package; not executed at runtime. |
| **`PyInstaller Bootloader`** | `pyinstaller 6.11.1` | GPLv2 with Special Exception | Provides the PE executable header for `docuready_sidecar.exe`. The PyInstaller exception permits distributing proprietary or differently licensed code without forcing the payload into GPL. |
