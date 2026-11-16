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
| **`DocuReady-0.1.0-Setup.exe`** | `apps/desktop/out/make/squirrel.windows/x64/DocuReady-0.1.0-Setup.exe` | 435,838,464 | 415.65 MB | `E8326B71C919A203A3099126CB745C1FAC1D84D01BDBD1E442F1432D8578EC01` | `56F7DB47CA3CE27C44EC585B5A405CF4AE25A943` |
| **`DocuReady-win32-x64-0.1.0.zip`** | `apps/desktop/out/make/zip/win32/x64/DocuReady-win32-x64-0.1.0.zip` | 446,700,288 | 426.01 MB | `DEE339C290B23A953BF9A86ED94E0EDD1AAEE79C4E5714283C004350A80196C5` | `839D37C8D42A4E045CE03B8D56A414A5CEFF60F6` |
| **`DocuReady-0.1.0-full.nupkg`** | `apps/desktop/out/make/squirrel.windows/x64/DocuReady-0.1.0-full.nupkg` | 436,532,263 | 416.31 MB | `2CC94A5FB06B89E9AD4DBB44ABE17F5A88601DD1A182C62BEC298F534BC220D7` | `648FECC888072E0BF62B04F5A5EEA7CC91E03264` |
| **`RELEASES`** | `apps/desktop/out/make/squirrel.windows/x64/RELEASES` | 80 | 0.00 MB | `6DEC1473B7123F7544BDEFEA1B5F8DAB1CBA5D46110FA816EC841666E39CC247` | `E570499C6A7B0568B342898BFA91873ED355D211` |
| **`DocuReady.exe`** | `apps/desktop/out/DocuReady-win32-x64/DocuReady.exe` | 250,056,704 | 238.47 MB | `79194130F9177F53B5D824DFC8987381C4DE1829DE5C287432EF5D30B0A93FF2` | `29541C7C171787C17F16F4F5651FDEFD2ECAFD08` |

---

## 3. Squirrel Package Cross-Validation

The Squirrel Windows update system relies on mutual consistency between the `.nupkg` package, `RELEASES` index, and `Setup.exe`.
Direct verification of `apps/desktop/out/make/squirrel.windows/x64/RELEASES`:
```text
648FECC888072E0BF62B04F5A5EEA7CC91E03264 DocuReady-0.1.0-full.nupkg 436532263
```
- **Recorded Hash:** `648FECC888072E0BF62B04F5A5EEA7CC91E03264` matches the SHA-1 of `DocuReady-0.1.0-full.nupkg` exactly.
- **Recorded Length:** `436532263` bytes matches the physical disk size of `DocuReady-0.1.0-full.nupkg` exactly.

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
