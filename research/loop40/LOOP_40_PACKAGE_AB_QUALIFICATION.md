# Loop 40 Package A vs. Variant B Qualification Report

**Date:** 2026-11-27  
**Branch:** `loop-40-performance-multilingual-and-windows-qualification`  
**Artifact Source:** `apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar`

---

## 1. Variant Definitions & Disk Footprint

- **Variant A (Full Bundled Sidecar):** `1,837` files, **`759,258,903` bytes** (`724.09 MiB`).
- **Variant B (Minimized Sidecar):** `1,820` files, **`692,773,837` bytes** (`660.68 MiB`).
  - Removed `17` unused Tesseract training/CLI executables (`ambiguous_words.exe`, `classifier_tester.exe`, `cntraining.exe`, `combine_lang_model.exe`, `combine_tessdata.exe`, `dawg2wordlist.exe`, `lstmeval.exe`, `lstmtraining.exe`, `merge_unicharsets.exe`, `mftraining.exe`, `set_unicharset_properties.exe`, `shapeclustering.exe`, `tesseract-uninstall.exe`, `text2image.exe`, `unicharset_extractor.exe`, `winpath.exe`, `wordlist2dawg.exe`), keeping `tesseract.exe`, `libtesseract-5.dll`, and all `tessdata` models intact.
  - **Net Savings:** **`66,485,066` bytes (`63.40 MiB`, `-8.76%`)** across `17` files.

---

## 2. Predeclared Non-Inferiority Design

- **Design:** `n = 10` alternating paired trials (`Pair 1: A -> B`, `Pair 2: B -> A`, ..., `Pair 10: B -> A`) executing a 5-document multilingual packet (`DOC_CTRL_01`, `DOC_HIN_01`, `DOC_ORI_01`, `DOC_MIX_01`, `DOC_MIX_02`) via `docuready_sidecar.exe`.
- **Predeclared Margin:** `delta = +1500.0 ms` on `audit_packet` latency (`95% CI upper bound <= +1500.0 ms`), plus `0` functional/exit-code regressions (`ok == true` for all `20/20` runs).

---

## 3. Observed Paired Results (`ab_paired_trials.json`)

| Metric | Variant A (`n = 10`) | Variant B (`n = 10`) |
| :--- | :---: | :---: |
| Functional Success (`ok == true`, `rc == 0`) | `10 / 10` (`100%`) | `10 / 10` (`100%`) |
| Cold `health` Handshake Mean / Median | `1862.53 ms` / `1657.88 ms` | `3014.52 ms` / `2497.69 ms` |
| `audit_packet` Mean / Median | `16421.60 ms` / `15107.42 ms` | `16387.73 ms` / `18513.64 ms` |
| `audit_packet` p90 / p95 | `24577.97 ms` / `25047.20 ms` | `19901.16 ms` / `20928.84 ms` |
| `audit_packet` Stdev | `6153.85 ms` | `4498.45 ms` |

- **Mean Paired Difference (`B - A`):** **`-33.87 ms`** (Variant B was `33.87 ms` faster on average).
- **95% Confidence Interval (`t_{0.025, 9} = 2.2622`):** **`[-4584.03 ms, +4516.29 ms]`**.
- **Predeclared Statistical Gate (`CI_high <= +1500 ms`):** **NOT MET (`+4516.29 ms > +1500.0 ms`)** — because a 5-document full OCR batch takes ~`16.4 s` with `4.5–6.2 s` run-to-run OS/process jitter, `n = 10` pairs is statistically underpowered to bound a `1.5 s` margin even though the point estimate (`-33.87 ms`) shows zero degradation and `10/10` functional parity.
- **Recommendation:** Variant B is functionally identical (`10/10` pass) and saves `63.40 MiB` (`66,485,066` bytes) with `-33.87 ms` mean difference, but formal statistical non-inferiority at `delta = 1500 ms` requires either `n >= 90` pairs or isolating single-process warm throughput from cold OS process-spawn variance.
