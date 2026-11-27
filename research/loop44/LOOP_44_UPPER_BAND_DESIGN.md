# LOOP 44 — UPPER-BAND DESIGN (STRATEGY D)

## 1. Design Goal

Recover documents with an Indic header above the central probe strip (`y < 0.25`) and a blank lower half (`y > 0.52`), without triggering:
1. Unconditional 3-band probing latency (Strategy B failed at `952–1,968 ms`).
2. False-positive multilingual routing on English-only documents that contain logos, seals, or letterhead decorations in the upper band.

## 2. Strategy D Architecture (`src/docuready/ingest/adaptive_ocr.py`)

In `profile_document()`:
1. **Central probe** (`y = 0.25..0.45`, `x = 0.15..0.85`) runs first.
2. **Strategy C (Lower-body conditional probe)**: If central strip is monolingual `LATIN` and `not is_mixed`, probe `y = 0.52..0.85`.
   - If `lower_txt.strip()` is non-empty, append it and re-run `detect_unicode_script()`.
3. **Strategy D (Upper-band conditional probe)**: Only if `lower_txt.strip()` is **empty** (blank or below ink threshold `0.003`), probe `y = 0.05..0.22` via `_probe_band(0.05, 0.22)`.
   - Count genuine Indic letter codepoints using `RE_DEVANAGARI.findall(upper_txt)` and `RE_ODIA.findall(upper_txt)`.
   - **False-Positive Guard**: Only merge `upper_txt` and re-run `detect_unicode_script()` when `dev_count + ori_count >= 6`.
4. **Existing `>= 4` Indic Safeguard**: Preserved downstream so mixed Indic+Latin pages with `>= 4` Indic characters are never suppressed by majority-Latin ratios.

## 3. Cost & Risk Analysis

- **Zero overhead** on pure Indic documents (central probe is already non-Latin).
- **Zero overhead** on standard full-page English documents (lower body is non-empty, so upper band is skipped).
- **Bounded overhead** only on short/half-blank English documents (adds one 350 px thumbnail probe, well within `< 850 ms` L17 budget).
- **False-positive resistance**: Requires both `ink >= 0.003` (enforced by `_probe_band`) AND `>= 6` Devanagari/Odia Unicode codepoints in `0.05..0.22`.
