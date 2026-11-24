# Loop 22 — Baseline Reproduction Report

**Loop:** 22  
**Baseline Target:** Loop 21 (`4a6a46e`)  
**Base Commit:** `4a6a46ed7d40b9a5e6381e92551c7a7e9790cbdc`  
**Working Branch:** `loop-22-evidence-association-reliability`  
**Target Platform:** Windows x64 Desktop (Python 3.12.10, Tesseract v5.5.0.20241111)  
**Sealed Release Target:** Loop 10 (`bdc403a`) — 100% Bit-Exact Match

---

## 1. Environment & Provenance Record

| Attribute | Recorded Value |
| :--- | :--- |
| **Operating System** | Windows 11 Enterprise x64 |
| **Python Runtime** | Python 3.12.10 (tags/v3.12.10:b27cf4f) |
| **OCR Engine** | Tesseract 5.5.0.20241111 (leptonica-1.84.1) |
| **Available Script Packs** | `eng`, `hin`, `ori`, `osd` |
| **Base Commit** | `4a6a46e` (feat(loop21): hierarchical header reconstruction and decimal integrity validation) |
| **Execution Command** | `python research/loop21/benchmark/run_loop21_benchmark.py` |

---

## 2. Frozen Release Invariance Audit

Prior to beginning Loop 22 research, all Loop 10 competition binary artifacts were verified via SHA-256 against their sealed baselines:

```powershell
Get-FileHash apps/desktop/out/DocuReady-win32-x64/DocuReady.exe, `
             apps/desktop/out/DocuReady-win32-x64/resources/app.asar, `
             apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar/docuready_sidecar.exe
```

- `DocuReady.exe`: `86339BA01C1E0E73B1A8E3CF799880C957F24E3691B0B4EE0717A861FCC5DCD2` (MATCH)
- `app.asar`: `D72882945989E468C76CE43840C16457AA94E59584DC6F953689A28A0014F27E` (MATCH)
- `docuready_sidecar.exe`: `5CF296943A640F41784B27786B59EE679C59DAA6BDA59CA2ACBEAE7621770B4C` (MATCH)

---

## 3. Independent Historical Baseline Reproduction

The Loop 21 benchmark suite was re-executed with zero modifications:

```bash
python research/loop21/benchmark/run_loop21_benchmark.py
```

### Aggregate Reproduction Figures
- **Total Evaluated Documents:** 40
- **Total Critical Fields:** 83
- **Spatial Exact Matches (SEM):** 62 (74.70%)
- **Verified Claims:** 73 (87.95% Coverage)
- **Verified Exact Matches:** 59
- **False Verifications:** 14 (19.18% False Verification Rate)
- **Abstentions:** 10 (12.05% Abstention Rate)
- **Critical Field Precision (CFP):** 80.82%
- **Mean Processing Latency:** 539.29 ms
- **Mean Table Grid Overhead:** 2.23 ms

### Cohort-by-Cohort Reproduction Verification

| Cohort | Documents | Fields | Verified | Exact Match | False Verifications | Abstentions | Cohort Precision |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A: Development** | 8 | 16 | 16 | 15 | 1 | 0 | 93.75% |
| **B: Validation** | 8 | 16 | 13 | 13 | 0 | 3 | 100.00% |
| **C: Blind Generalization** | 10 | 23 | 21 | 15 | 6 | 2 | 71.43% |
| **D: Challenge Adversarial** | 8 | 16 | 11 | 4 | 7 | 5 | 36.36% |
| **E: Hierarchical Headers** | 3 | 6 | 6 | 6 | 0 | 0 | 100.00% |
| **F: Decimal Integrity** | 3 | 6 | 6 | 6 | 0 | 0 | 100.00% |
| **TOTAL** | **40** | **83** | **73** | **59** | **14** | **10** | **80.82%** |

### Accounting Ledger Validation
- **Verified + Abstained:** $73 + 10 = 83$ ($100.00\%$)
- **Coverage + Abstention Rate:** $0.8795 + 0.1205 = 1.0000$
- **CFP + FVR:** $0.8082 + 0.1918 = 1.0000$

All reproduction figures matched the reported Loop 21 benchmark exactly, establishing an indisputable baseline for Loop 22.
