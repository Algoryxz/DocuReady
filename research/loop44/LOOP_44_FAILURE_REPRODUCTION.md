# LOOP 44 — FAILURE REPRODUCTION (`BLIND43_IND_HDR_LAT_ID`)

## 1. Failure Description

In Loop 43, `BLIND43_IND_HDR_LAT_ID` (an Odia header at `y < 0.25`, a Latin ID block in the central region `y = 0.25..0.45`, and a blank lower half `y > 0.52`) was misrouted to `FAST_PATH_ENG` (`eng` only), yielding `44.55%` CER and `61.54%` WER.

## 2. Root Cause Trace (Strategy C)

1. `profile_document()` probed the central strip (`0.25..0.45`) → detected only Latin text (`GOVERNMENT IDENTITY RECORD / Name / ID`).
2. Because the central strip was monolingual `LATIN` and `not is_mixed`, Strategy C probed the lower body (`0.52..0.85`).
3. The lower body was blank (`ink_density = 0.0 < 0.003`), returning `""`.
4. Strategy C did **not** inspect the upper region (`0.05..0.22`).
5. Result: `primary_script = "LATIN"`, `is_mixed_script = False` → `FAST_PATH_ENG` (`eng`).

## 3. Secondary Discovery: Header Thumbnail Resolution Bottleneck

When implementing Strategy D (`_probe_band(0.05, 0.22)`), initial testing on the rasterized `BLIND44_IND_HDR_LAT_ID_RASTER.png` showed an unexpected failure at `350 px` max dimension:
- At `max_dim = 350`: strip `(840, 272)` downscaled to `(350, 113)` → Tesseract OCR took `775.6 ms` and recognized only **3 Odia characters** (below the `>= 6` guard threshold).
- At `max_dim = 500`: strip `(840, 272)` downscaled to `(500, 161)` → Tesseract OCR took **`578.5 ms`** (faster!) and recognized **37 Odia characters** (`>= 6` guard satisfied).

Downscaling a shallow header band (`17%` of page height) to `350 px` wide crushes vertical glyph height to `113 px`, degrading Indic diacritics and slowing LSTM decoding. Setting `max_dim = 500.0` for the conditional upper-band probe resolves both accuracy and latency.
