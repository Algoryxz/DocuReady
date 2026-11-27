# LOOP 17: Technical Boundaries, Limitations & Operational Scope

## 1. Scope & System Boundaries

Loop 17 achieved significant latency reduction and established 100% critical-field accuracy on structured documents. However, an honest engineering audit requires documenting explicit boundaries where the system reaches its limits.

---

## 2. Explicit Technical Limitations

### 2.1. Script & Language Coverage
- **Supported Scripts:** Latin (`eng`), Devanagari (`hin`), Odia (`ori`).
- **Unsupported Languages:** Other 19 official languages listed in the Eighth Schedule of the Indian Constitution (e.g., Bengali, Tamil, Telugu, Kannada, Malayalam, Gujarati, Marathi, Punjabi) are currently routed to English or compound fallback.
- **Minimum Glyph Threshold:** Script detection requires at least 5 recognizable characters in the central strip. Isolated single-character rubber stamps may not be detected.

### 2.2. Geometric Layout Assumptions
- **Two-Column Gutter Heuristic:** The column detector assumes a central vertical quiet gutter in the middle $35\%–65\%$ width band.
  - Three-column layouts (common in certain central gazettes) are currently treated as single-column layouts.
  - Non-Manhattan layouts (diagonal watermarks, circular emblem text, triangular text wraps) cannot be segmented by vertical projection.

### 2.3. Physical Scan Tilt & Affine Distortion
- **Skew Tolerance Limit ($\le 2.5^\circ$):** The system does not perform automatic affine deskewing. As demonstrated in `CHALLENGE_05_ROTATED_SKEW_GAZETTE` ($2.8^\circ$ tilt), tilted lines project into the gutter, degrading CER.
- **Perspective Distortion:** Documents photographed at an angle using mobile devices with keystone distortion will experience distorted projection profiles.

### 2.4. Embedded Bitmap Screenshots
- As observed in `DOC_EXT_01_MOSPI_NADA_GUIDE`, administrative user manuals that embed full browser screenshots result in high CER because the OCR recognizes all website navigation chrome and UI text, which is not present in standard narrative ground truth.

---

## 3. Environmental Dependencies

- **Local Execution:** Requires local `tesseract.exe` 5.x on Windows x64 with `eng.traineddata`, `hin.traineddata`, and `ori.traineddata`.
- **Offline Guarantee:** 100% local operation without external network, GPU, or cloud API calls.
