# DOCUREADY — DETERMINISTIC DEMONSTRATION RESET PROCEDURE

**Milestone:** Loop 5 Phase 2 — Deterministic Demonstration Reset Procedure  
**Application Target:** DocuReady Desktop Application  
**Reset Script:** [`scripts/reset_demo_state.py`](file:///c:/Users/smara/Desktop/New%20folder/scripts/reset_demo_state.py)

---

## 1. Purpose & Guarantees

To ensure that every competition presentation and live judge evaluation begins from a pristine, predictable state, this reset procedure enforces:
1. **Zero Zombie Processes:** All background instances of `docuready_sidecar.exe` or `DocuReady.exe` are forcefully terminated.
2. **Zero Ephemeral Staging Files:** All temporary document caches in `%LOCALAPPDATA%\Temp\docuready-desktop\` and `%TEMP%` are deleted.
3. **Corpus Integrity Verification:** All 16 synthetic validation documents in `tests/validation_corpus/` are checked to ensure no accidental in-place modifications occurred during interactive exploration.
4. **Pristine Renderer Session:** Ensures Electron localStorage, session state, and document tables are unpolluted.

---

## 2. One-Command Quick Reset

Execute the following in the project root:

```powershell
python scripts/reset_demo_state.py
```

Expected output:
```text
=== Initiating DocuReady Demo Reset Procedure ===
1. Terminating any lingering sidecar or desktop processes...
2. Cleaning ephemeral workspace temp directories...
   Purged: C:\Users\<User>\AppData\Local\Temp\docuready-desktop
3. Verifying validation corpus files...
   Validation corpus intact (16 files present).
4. Verifying packaged sidecar binary...
   Sidecar binary verified: sidecar\dist\docuready_sidecar\docuready_sidecar.exe
=== Demo Reset Complete. Application ready for live scenario. ===
```

---

## 3. Manual Reset Checklist

If running a live demonstration without script execution:
1. Close the DocuReady window.
2. Open PowerShell and run:
   ```powershell
   Get-Process docuready_sidecar,DocuReady -ErrorAction SilentlyContinue | Stop-Process -Force
   Remove-Item -Recurse -Force "$env:TEMP\docuready-desktop" -ErrorAction SilentlyContinue
   ```
3. Launch `apps\desktop\out\DocuReady-win32-x64\DocuReady.exe`.
4. Confirm initial empty-state message appears.

---
*Procedure verified for HackNation 2026 Live Demonstration.*
