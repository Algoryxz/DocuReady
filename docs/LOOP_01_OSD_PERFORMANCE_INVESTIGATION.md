# DocuReady Loop 01 — OCR Orientation Detection Performance Investigation

**Branch:** `loop-01-osd-performance-analysis`
**Base:** `main` (release-qualified baseline)
**Status:** Investigation complete; implementation experiment pending local runtime access

## Objective

Reduce OCR page latency without losing orientation recovery, extraction quality, evidence-coordinate correctness, offline operation, or safe abstention.

## Repository inspection findings

- `src/docuready/ingest/extractor.py` currently calls `pytesseract.image_to_osd(img, timeout=OCR_TIMEOUT_SECONDS)` for every page that takes the OCR fallback path. The OSD input is the full rendered image.
- OSD failures are caught and ignored, after which token OCR proceeds on the unrotated image.
- Token OCR then runs `image_to_data` on the resulting image and maps token coordinates to PDF points through `PageOCRData`.
- The 200-DPI OSD pass is not currently skipped based on page metadata, text density, or a cheaper orientation heuristic.
- Existing benchmark documentation reports OSD at roughly 1.46 seconds full resolution and 1.27 seconds on a half-size image; token OCR is roughly 0.99 seconds and rendering roughly 0.21 seconds. The profile is historical and should be re-run on the current branch/hardware before treating it as a current baseline.
- The documented six-document mixed packet audit was about 9.68 seconds. That is historical benchmark evidence, not a new Loop 01 measurement.

## Primary bottleneck hypothesis

Orientation/script detection (OSD) is expensive and runs unconditionally on OCR pages. It appears to cost more than token OCR itself. Removing or gating OSD may improve latency, but any shortcut risks losing recovery for rotated pages.

## Experiment sequence

1. Re-run the existing pipeline benchmark on the current baseline; record OS, CPU, Python, Tesseract version, DPI, packet, page count, OCR pages, mean, median, and p95.
2. Add stage timing for render, OSD, token OCR, line clustering, and field parsing, using monotonic high-resolution timers. Ensure timing instrumentation is opt-in or low overhead and does not expose document contents.
3. Build a test matrix including unrotated clean scans, 90/180/270-degree rotations, slight skew, low DPI, sparse pages, blank pages, and OSD failure.
4. Compare candidate OSD strategies:
   - current full-resolution OSD baseline;
   - downsampled OSD input;
   - orientation metadata/rotation fast path, where supported and proven;
   - optional skip OSD only when a conservative orientation confidence/fast signal permits it.
5. Measure accuracy, extraction recall, false acceptance, abstention, page latency, packet latency, and evidence bbox alignment. Reject any speedup that harms orientation recovery or confidence safety.
6. Select one strategy only if the benchmark demonstrates a meaningful speedup with no regression on held-out rotated/ambiguous cases. Keep a safe fallback.
7. Run targeted OCR/extractor tests, the held-out extraction corpus, packet golden tests, zero-network contracts, and desktop tests as appropriate.
8. Document the result and next bottleneck. Do not merge/release from this branch until the local Windows runtime qualification is complete.

## Acceptance criteria

- Current baseline timings are reproducible and saved.
- Rotation test coverage includes 0, 90, 180, and 270 degrees plus skew/low-quality cases.
- OSD errors do not cause a crash or falsely mark OCR as successful.
- Candidate optimization has measured per-page and end-to-end improvement.
- No new false-positive extraction or loss of rotated-page recovery in the regression corpus.
- Bounding boxes remain aligned with original PDF coordinates after rotation.
- Offline/network contracts and existing golden packet outcomes remain unchanged.
- Full tests and Windows packaged qualification are run locally/CI; results are reported honestly.

## Risks and constraints

- Downsampling may lower orientation confidence for low-resolution pages.
- Skipping OSD may silently misread rotated pages and is unacceptable without evidence.
- Rotation changes image dimensions and coordinate transforms; bbox mapping must be tested.
- Historical performance reports differ in benchmark methodology; establish a current, repeatable baseline before claiming improvement.

## Scope decision

Loop 01 is narrowly scoped to OCR orientation-detection cost and its failure safety. It does not redesign the OCR engine, alter statutory rules, change score weights, or change the golden baseline.
