# LOOP 44 — BASELINE AUDIT

## 1. Repository & Branch State

| Field | Value |
|---|---|
| **Working Branch** | `loop-44-upper-band-mixed-script-and-e2e-integrity` |
| **Base Commit** | `e5ba978853b32fd37c3e6bbe5ddab456399f4fca` (Loop 43) |
| **Loop 43 Ancestor Check** | `git merge-base --is-ancestor e5ba978 HEAD` → `0` (PASS) |
| **Loop 10 Ancestor Check** | `git merge-base --is-ancestor bdc403a HEAD` → `0` (PASS) |
| **Protected Release** | `bdc403a` (Loop 10 — unmodified, unpromoted) |

## 2. Prior Loop Baseline Summary (Loops 41–43)

- **Loop 41 (`66d7c3f`)**: Introduced `_InProcessScriptProbe` (`recognize_gray()`), fallback parity guards (`_ORIG_PYTESSERACT_IMAGE_TO_STRING`), and tiny-image `ZeroDivisionError` guard (`w < 10 or h < 10`).
- **Loop 42 (`2849936`)**: Integrated `TessBaseAPIGetTsvText` (`recognize_tsv()`) and `_run_image_to_data()` into `execute_adaptive_ocr()` Stages 3/4, reducing warm E2E latency by 41.4% (L17) and 19.4% (L18).
- **Loop 43 (`e5ba978`)**: Implemented Strategy C adaptive 2-region probing (`0.25–0.45` central strip + conditional `0.52–0.85` lower body + `>= 4` Indic char safeguard). Resolved `BLIND43_LAT_HDR_HIN_BODY`, while leaving `BLIND43_IND_HDR_LAT_ID` (Indic header at `y < 0.25`, blank lower half) as an honest miss (Gate O = PARTIAL).

## 3. Pre-Existing Untracked Directories Preserved

`.agents/`, `docs/product/`, `hacknation-arena/`, `hacknation-arena-v2/`, `hacknation-arena-v3/`, `presentation/`, `sidecar/tessdata_extra/` — all preserved untouched.
