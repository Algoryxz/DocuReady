# Loop 40 Failure Analysis

**Date:** 2026-11-27  
**Branch:** `loop-40-performance-multilingual-and-windows-qualification`

---

## 1. Worst CER Cases in the 35-Document Evaluation (`accuracy_results.json`)

1. **`DOC_EXT_01_MOSPI_NADA_GUIDE` (`CALIBRATION`, `English-only`, Adaptive CER `784.14%`, Global CER `786.90%`):**
   - **Why:** `DOC_EXT_01_MOSPI_NADA_GUIDE_gt.txt` contains only a 145-character (21-word) excerpt, whereas full-page OCR (`FAST_PATH_ENG` at 83.73 mean confidence) extracts the entire page (~1,280 chars). Both Adaptive (`7.84`) and Global (`7.87`) show identical length-mismatch inflation, skewing `English-only` and `CALIBRATION` macro CER.
2. **`DOC_HIN_03_TWO_COLUMN_GAZETTE` (`DEV`, `Hindi-only`, Adaptive CER `51.28%` vs Global CER `39.56%`):**
   - **Why:** `REGION_AWARE_ROUTING` (`selected_lang="auto"`) split the two-column Hindi gazette by its vertical gutter (`has_gutter=true`), whereas `eng+hin+ori` global pass produced lower character edit distance (`39.56%`) on this specific layout, though both had `70.73%` WER.
3. **`CHALLENGE_04_LOW_CONTRAST_UNREADABLE_STRESS` (`BLIND`, `Unreadable/Stress`, `ABSTAIN_UNREADABLE`):**
   - **Why:** Intentional abstention (`ocr_model_invocations=0`) on an unreadable low-contrast stress fixture, preventing hallucinated text.

---

## 2. Package A vs. Variant B Statistical Power Limitation

- In `ab_paired_trials.json` (`n = 10` pairs), Variant B saved `66,485,066` bytes (`63.40 MiB`) and averaged `-33.87 ms` faster than Variant A (`10/10` functional parity).
- However, the 95% CI `[-4584.03 ms, +4516.29 ms]` exceeded the predeclared `+1500.0 ms` non-inferiority bound due to `4.5–6.2 s` OS/subprocess jitter on a `16.4 s` multi-document OCR batch.

---

## 3. Blocked Windows Trust Gates

- Authenticode signing (`NotSigned` on all 3 Windows executables) and clean-VM SmartScreen verification remain `BLOCKED` due to absence of a code-signing certificate, `signtool.exe`, and clean Windows VM on this host.
