# DOCUREADY — LOOP 15 ARCHITECTURAL LIMITATIONS
## Known Boundaries, Assumptions & Scope Constraints of Region-Aware OCR

**Project:** DocuReady — HackNation 2026  
**Engineering Loop:** 15  
**Date:** November 2026  
**Status:** FORMALLY DOCUMENTED  

---

## 1. Scope & Architectural Boundaries

Loop 15 proved that spatial region-aware script routing significantly improves OCR accuracy on mixed-script Indian administrative documents. However, several inherent architectural boundaries must be explicitly stated:

### 1.1 Non-Rectilinear / Irregular Layouts
- **Current Limitation:** The region decomposition algorithm relies on axis-aligned bounding boxes (AABBs) derived from horizontal and vertical projection profiles.
- **Impact:** Irregularly wrapped text (e.g. text curving around circular departmental seals or watermarks) cannot be partitioned cleanly with horizontal projection slices. In such cases, bounding boxes may include partial seal fragments.

### 1.2 Fine-Grained Intra-Word Script Mixing
- **Current Limitation:** When a word itself contains characters from multiple scripts (e.g. Hindi roots with English alphanumeric suffixes like `योजना-2026` or `DBT-खाता`), Tesseract must rely on compound language models (`eng+hin`) for that specific token.
- **Impact:** If `eng` or `hin` alone is applied to a composite token, one half of the token suffers substitution errors.

### 1.3 Small Crop OSD Failures
- **Current Limitation:** Tesseract's built-in Orientation and Script Detection (`image_to_osd`) requires at least 15–20 characters to reliably determine script. Calling OSD on very small sub-crops (e.g. a 3-character serial number cell) raises `Too few characters. Skipping this page`.
- **Mitigation:** DocuReady guards all OSD calls with character count thresholds and falls back gracefully to Unicode codepoint inspection and standard language priors.

### 1.4 High Table Cell Counts and Subprocess Overhead
- **Current Limitation:** Each detected region currently spawns an independent Tesseract CLI subprocess. On complex tables with 15+ cells, subprocess startup latency accumulates to several seconds.
- **Future Direction:** Integrating in-process Tesseract C-API bindings (e.g. via `tesserocr`) or batching non-overlapping regions into a single composite mosaic canvas.

---

## 2. Platform & Hardware Constraints

- **Tessdata Dependencies:** Requires `eng.traineddata`, `hin.traineddata`, and `ori.traineddata` to be co-located or unified via `get_unified_tessdata_dir`. If an Indic traineddata model is absent, the engine gracefully falls back to `eng`.
- **Host CPU Dependency:** As an offline, local desktop application, recognition speed depends entirely on host CPU single-thread IPC. No GPU acceleration is assumed or required.
