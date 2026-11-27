# DOCUREADY — LOOP 37 PACKAGE MINIMIZATION (`BUG-036-002`)

Isolated temp-copy test removed 17 unnecessary Tesseract training/utility EXEs (`cntraining.exe`, `lstmtraining.exe`, etc.) while keeping `tesseract.exe`, all 122 DLLs, and `eng`/`hin`/`ori`/`osd` traineddata:
- Original sidecar: `759,258,903` bytes (724.09 MB)
- Minimized sidecar: `692,773,837` bytes (660.68 MB)
- **Saved:** `66,485,066` bytes (**63.41 MB**)
- Verified `docuready_sidecar.exe` health (`rc=0`) and `tesseract.exe --list-langs` (`eng`, `hin`, `ori`, `osd`).
