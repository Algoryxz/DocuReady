# DOCUREADY — LOOP 42 BASELINE & LOOP 10 FREEZE VERIFICATION

**Date:** 2026-11-27  
**Branch:** `loop-42-e2e-ocr-performance-and-production-qualification`  
**Base Commit (Loop 41):** `66d7c3f502cb4a770273df990b6118544ef8c17e`  
**Protected Release (Loop 10):** `bdc403a601f88008c43c0630f5e8c71ce22c9977`

## 1. Git Ancestry

- `66d7c3f` (Loop 41) is an ancestor of `HEAD` (`0`).
- `bdc403a` (Loop 10) is an ancestor of `HEAD` (`0`).

## 2. Loop 10 Frozen Artifact Hashes (Recomputed from Disk)

| Artifact | Disk Path | Size (B) | Recomputed SHA-256 | Status |
|---|---|---:|---|---|
| `DocuReady.exe` | `apps\desktop\out\DocuReady-win32-x64\DocuReady.exe` | 250,056,704 | `86339ba01c1e0e73b1a8e3cf799880c957f24e3691b0b4ee0717a861fcc5dcd2` | **PASS** |
| `app.asar` | `apps\desktop\out\DocuReady-win32-x64\resources\app.asar` | 3,239,787 | `d72882945989e468c76ce43840c16457aa94e59584dc6f953689a28a0014f27e` | **PASS** |
| `docuready_sidecar.exe` | `apps\desktop\out\DocuReady-win32-x64\resources\docuready_sidecar\docuready_sidecar.exe` | 28,369,190 | `5cf296943a640f41784b27786b59ee679c59daa6bda59ca2acbeae7621770b4c` | **PASS** |
| `DocuReady-0.1.0-Setup.exe` | `apps\desktop\out\make\squirrel.windows\x64\DocuReady-0.1.0-Setup.exe` | 457,490,432 | `8dcd51c89d305c0d92503f93c7dc255c5f29c7eb18b6cabe866d01d30d8766ed` | **PASS** |
| `DocuReady-win32-x64-0.1.0.zip` | `apps\desktop\out\make\zip\win32\x64\DocuReady-win32-x64-0.1.0.zip` | 469,045,411 | `eb4cef9395e9fea1155b06afba7091521eb58b75d43e9dd51fa40fae6015e5c4` | **PASS** |

All 5 Loop 10 frozen artifacts match `docs/04-VALIDATION/LOOP_10_FEATURE_FREEZE_RECORD.md` **5/5 bit-exact**. Loop 10 has not been modified, rebuilt, promoted, or merged.
