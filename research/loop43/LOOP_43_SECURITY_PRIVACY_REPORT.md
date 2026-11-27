# DOCUREADY — LOOP 43 SECURITY & PRIVACY REPORT

- **Offline Operation:** `_InProcessScriptProbe` (`recognize_gray` & `recognize_tsv`) uses local `libtesseract-5.dll` and local `tessdata`; zero network calls.
- **Desktop Security & Isolation (`npm --prefix apps/desktop test -- --run`):** `25 / 25` passed in `34.99 s` (IPC sender validation, workspace isolation, session purge, sidecar crash & cancellation recovery).
- **Release Protection:** Loop 10 (`bdc403a`) verified `5/5` bit-exact and untouched.
