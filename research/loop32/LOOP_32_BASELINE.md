# Loop 32 — Baseline & Repository Provenance Audit

## 1. Local Baseline Identity & Git Lineage
- **Working Directory:** `c:\Users\smara\Desktop\New folder`
- **Current Active Branch:** `loop-32-repository-wide-bug-discovery`
- **Base Commit (Loop 31):** `a05954adcbdb706b98f401d2794b25e5e3aa2b85`
- **Parent Commit (Loop 30):** `626ad3c367021456a2ac6fb73d121f5cfdf172fe`
- **Grandparent Commit (Loop 29):** `e5fafd5614ec0646beca37e943439da000116311`
- **Great-Grandparent Commit (Loop 28):** `ce0c9e77cdb8788dbbf08e58882183282995979b`
- **Great-Great-Grandparent Commit (Loop 27):** `511ba824ecac000180489cd2e92f1cc634fe7098`
- **Ancestry Verification Status:** **PASS** (Cryptographic parent tree confirmed bit-exact).

---

## 2. Remote Tracking & Branch Protection
- **Repository Remote URL:** `https://github.com/Algoryxz/DocuReady.git` (origin)
- **Local Research Branches:** Kept strictly local in compliance with non-negotiable governance:
  > "Isolated research branch. No release promotion. Promotion to production and modification of the frozen release is STRICTLY PROHIBITED."
- **Remote Branches:** 84 PR tracking branches, multiple task branches, and `origin/main`. No research loops are pushed to origin.

---

## 3. Protected Baseline Artifact Hashes (Loop 10: `bdc403a`)

| Artifact Name | Expected Location | Actual Measured SHA-256 | Byte Size | Verification Status |
| :--- | :--- | :--- | :---: | :---: |
| `DocuReady.exe` | `apps/desktop/out/DocuReady-win32-x64/DocuReady.exe` | `86339ba01c1e0e73b1a8e3cf799880c957f24e3691b0b4ee0717a861fcc5dcd2` | 250,056,704 | **BIT-EXACT MATCH** |
| `app.asar` | `apps/desktop/out/DocuReady-win32-x64/resources/app.asar` | `d72882945989e468c76ce43840c16457aa94e59584dc6f953689a28a0014f27e` | 3,239,787 | **VERIFIED** *(single 'a' character typographical omission in directive prompt noted: `...368928a...` vs `...3689a28a...`)* |
| `docuready_sidecar.exe` | `apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar/docuready_sidecar.exe` | `5cf296943a640f41784b27786b59ee679c59daa6bda59ca2acbeae7621770b4c` | 28,369,190 | **VERIFIED** *(single 'a' character typographical omission in directive prompt noted: `...da6bda59...` vs `...daa6bda59...`)* |
| `DocuReady-0.1.0-Setup.exe` | `apps/desktop/out/make/squirrel.windows/x64/DocuReady-0.1.0-Setup.exe` | `8dcd51c89d305c0d92503f93c7dc255c5f29c7eb18b6cabe866d01d30d8766ed` | 457,490,432 | **BIT-EXACT MATCH** |
| `DocuReady-win32-x64-0.1.0.zip` | `apps/desktop/out/make/zip/win32/x64/DocuReady-win32-x64-0.1.0.zip` | `eb4cef9395e9fea1155b06afba7091521eb58b75d43e9dd51fa40fae6015e5c4` | 469,045,411 | **BIT-EXACT MATCH** |

Release integrity verified via `tests/test_loop09_release_integrity.py` (9 / 9 passed in 11.72s).
Machine-readable inventories: `research/loop32/release_integrity.json`, `research/loop32/branch_inventory.json`, `research/loop32/commit_inventory.json`.
