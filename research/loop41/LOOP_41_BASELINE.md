# DOCUREADY — LOOP 41 BASELINE & LOOP 10 FREEZE VERIFICATION

**Date:** 2026-11-27  
**Branch:** `loop-41-inprocess-ocr-reliability-and-release-qualification`  
**Base Commit (Loop 40):** `b487f03a9f1f36110c5ba9e17b7c6d93892c9001`  
**Protected Release (Loop 10):** `bdc403a601f88008c43c0630f5e8c71ce22c9977`

---

## 1. Git Ancestry & Working Tree Check

- `b487f03` is an ancestor of `HEAD` (`git merge-base --is-ancestor b487f03 HEAD` -> `0`).
- `bdc403a` is an ancestor of `HEAD` (`git merge-base --is-ancestor bdc403a HEAD` -> `0`).
- No tracked files were modified prior to Loop 41 investigation; pre-existing untracked directories (`.agents/`, `docs/product/`, `hacknation-arena*/`, `presentation/`, `sidecar/tessdata_extra/`) were present before Loop 41 and left untouched.

---

## 2. Loop 10 Immutable Release Hash Verification (Recomputed from Disk)

Recomputed directly via PowerShell `Get-FileHash -Algorithm SHA256` against `docs/04-VALIDATION/LOOP_10_FEATURE_FREEZE_RECORD.md`:

| Artifact | Disk Path | Freeze Size (B) | Recomputed Size (B) | Freeze SHA-256 | Recomputed SHA-256 | Status |
|---|---|---:|---:|---|---|---|
| `DocuReady.exe` | `apps\desktop\out\DocuReady-win32-x64\DocuReady.exe` | 250,056,704 | 250,056,704 | `86339ba01c1e0e73b1a8e3cf799880c957f24e3691b0b4ee0717a861fcc5dcd2` | `86339ba01c1e0e73b1a8e3cf799880c957f24e3691b0b4ee0717a861fcc5dcd2` | **PASS** |
| `app.asar` | `apps\desktop\out\DocuReady-win32-x64\resources\app.asar` | 3,239,787 | 3,239,787 | `d72882945989e468c76ce43840c16457aa94e59584dc6f953689a28a0014f27e` | `d72882945989e468c76ce43840c16457aa94e59584dc6f953689a28a0014f27e` | **PASS** |
| `docuready_sidecar.exe` | `apps\desktop\out\DocuReady-win32-x64\resources\docuready_sidecar\docuready_sidecar.exe` | 28,369,190 | 28,369,190 | `5cf296943a640f41784b27786b59ee679c59daa6bda59ca2acbeae7621770b4c` | `5cf296943a640f41784b27786b59ee679c59daa6bda59ca2acbeae7621770b4c` | **PASS** |
| `DocuReady-0.1.0-Setup.exe` | `apps\desktop\out\make\squirrel.windows\x64\DocuReady-0.1.0-Setup.exe` | 457,490,432 | 457,490,432 | `8dcd51c89d305c0d92503f93c7dc255c5f29c7eb18b6cabe866d01d30d8766ed` | `8dcd51c89d305c0d92503f93c7dc255c5f29c7eb18b6cabe866d01d30d8766ed` | **PASS** |
| `DocuReady-win32-x64-0.1.0.zip` | `apps\desktop\out\make\zip\win32\x64\DocuReady-win32-x64-0.1.0.zip` | 469,045,411 | 469,045,411 | `eb4cef9395e9fea1155b06afba7091521eb58b75d43e9dd51fa40fae6015e5c4` | `eb4cef9395e9fea1155b06afba7091521eb58b75d43e9dd51fa40fae6015e5c4` | **PASS** |

All 5 frozen Loop 10 artifacts match the original Loop 10 freeze record **5/5 bit-exact** (including `app.asar`). Loop 10 has not been modified, rebuilt, promoted, or merged.
