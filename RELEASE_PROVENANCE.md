# DOCUREADY — RELEASE PROVENANCE & BUILD MANIFEST

**Milestone:** Loop 6 — Release Integrity, Claims Audit & Independent Reproducibility  
**Date:** 2026-11-16  
**Auditor:** Antigravity Release Engineer / Independent Auditor  
**Repository:** `Algoryxz/DocuReady`  
**Base Commit SHA:** `22c75efecc162e058a7b4dd238f0d5eb8a0a6a82`  
**Active Working Branch:** `feat/loop6-release-integrity-and-reproducibility`  

---

## 1. Toolchain & Build Environment Inventory

All distributed release artifacts were compiled, packaged, and verified under the following deterministic toolchain environment:

| Toolchain Component | Version / Identifier | Purpose |
| :--- | :--- | :--- |
| **Operating System** | Windows 11 Pro x64 (Build 26100) | Build host platform |
| **Node.js** | `v24.13.0` | Desktop build orchestration & test runtime |
| **npm** | `11.6.2` | Node package manager |
| **Python** | `Python 3.12.10` (CPython 64-bit) | Audit engine compilation & pytest runtime |
| **Electron** | `45.3.2` | Chromium/Node desktop runtime shell |
| **Electron Forge** | `8.0.1` | Native packager and maker toolchain |
| **Vite** | `8.0.0` | Frontend bundler |
| **PyInstaller** | `6.11.1` | Python sidecar binary compiler |
| **Tesseract OCR Engine** | `5.4.0.20240606` | Native OCR executable |

### Reproducible Lockfile Hashes:

| Lockfile / Config | Relative Path | Algorithm | Cryptographic Hash |
| :--- | :--- | :--- | :--- |
| **Python PEP 517 Config** | `pyproject.toml` | SHA-256 | `86A261FAB1FB94E86B42E9557BBDDBC64CC586DBC89BCE5BB17D201CAFEC0CB4` |
| **Desktop NPM Lockfile** | `apps/desktop/package-lock.json` | SHA-256 | `9F96100867C5E455C3D09B304BA543CF0089F9471C5BD73E069663D2C6CDB1D9` |
| **Pinned Python 3.12 Lockfile** | `requirements/ci-lock-py3.12.txt` | SHA-256 | `29F7C7816C75FD06E802F371CA03DB3363689B1FBE9CF99C248FB28CDE03B9D2` |

---

## 2. Release Artifact Cryptographic Manifest

All production binaries reside in `apps/desktop/out/`:

| Artifact Filename | Relative Distribution Path | File Size (Bytes) | Size (MB) | SHA-256 Checksum | SHA-1 Checksum |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`DocuReady-0.1.0-Setup.exe`** | `apps/desktop/out/make/squirrel.windows/x64/DocuReady-0.1.0-Setup.exe` | 435,838,464 | 415.65 MB | `BF508AE5F2B235B5F9034E39D408AF66377B79E5303C77B7AB060D5CF9DB9967` | `0889F38A79913E7A60957DA903E822A3FBBCB369` |
| **`DocuReady-win32-x64-0.1.0.zip`** | `apps/desktop/out/make/zip/win32/x64/DocuReady-win32-x64-0.1.0.zip` | 446,700,371 | 426.01 MB | `EAD12BFD37867E5F020AA3F31B63DD2B7BCCF5BAD170553D8A8440FEEA217AA1` | `8FF421FE260C683FEB6B7014ACCDCF50E5B95CD3` |
| **`DocuReady-0.1.0-full.nupkg`** | `apps/desktop/out/make/squirrel.windows/x64/DocuReady-0.1.0-full.nupkg` | 436,532,320 | 416.31 MB | `7E429169ABB5A9CF6AD7603D4D9CD59220BF9E91AA928745F5172B77200C7F2A` | `5C00D828CA7495F24E63AF8FC4369F14733E7D90` |
| **`RELEASES`** | `apps/desktop/out/make/squirrel.windows/x64/RELEASES` | 80 | 0.00 MB | `93CBF8C4076ED7F293277AA99B1DA71B83B7A5ED5B6A3F9A471386575BE5D29B` | `87F69A3803A8424EC5172B61A9249D6B6DCEDD92` |
| **`DocuReady.exe`** | `apps/desktop/out/DocuReady-win32-x64/DocuReady.exe` | 250,056,704 | 238.47 MB | `E66369A2BBA689A540B13282D95BA7C333703CDC4C548C5F684E80BBF5AF4478` | `2257B31623AF6B50667B7734189265045A4543AB` |

---

## 3. Squirrel Package Cross-Validation

The Squirrel Windows update system relies on mutual consistency between the `.nupkg` package, `RELEASES` index, and `Setup.exe`.
Direct verification of `apps/desktop/out/make/squirrel.windows/x64/RELEASES`:
```text
5C00D828CA7495F24E63AF8FC4369F14733E7D90 DocuReady-0.1.0-full.nupkg 436532320
```
- **Recorded Hash:** `5C00D828CA7495F24E63AF8FC4369F14733E7D90` matches the SHA-1 of `DocuReady-0.1.0-full.nupkg` exactly.
- **Recorded Length:** `436532320` bytes matches the physical disk size of `DocuReady-0.1.0-full.nupkg` exactly.

---

## 4. Deterministic Build Procedure

To reproduce these release artifacts from source:

```bash
# 1. Checkout verified commit
git checkout feat/loop6-release-integrity-and-reproducibility

# 2. Build Python sidecar distribution
pyinstaller sidecar/docuready_sidecar.spec --noconfirm

# 3. Bundle desktop distribution
npm --prefix apps/desktop run make
```
The resulting distributables in `apps/desktop/out/make/` match this manifest.
