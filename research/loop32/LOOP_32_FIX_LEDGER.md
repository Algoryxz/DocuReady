# DocuReady Loop 32 Fix Ledger

**Programme:** DocuReady Product Excellence  
**Engineering Policy:** Minimal, Localized, Evidence-Grounded Remediation  
**Net Diff:** +24 lines, -25 lines across 4 files  

---

## 1. Summary of Applied Fixes

| Bug ID | Subsystem | Target File | Nature of Fix |
| :--- | :--- | :--- | :--- |
| **BUG-032-001** | Ingest / Extractor | `src/docuready/ingest/extractor.py` | Duck-typing bounding box extraction (`hasattr(r, 'x0')`) |
| **BUG-032-002** | Evidence / Normalization | `src/docuready/evidence/cross_document.py` | ISO `YYYY-MM-DD` date canonicalization to `DD/MM/YYYY` |
| **BUG-032-004** | Desktop / Workspace | `apps/desktop/src/main/workspace.ts` | Collision-resistant document staging with `${doc.id}` suffix |
| **BUG-032-005** | Normalize / Checksum | `src/docuready/normalize/normalizer.py` | Import authoritative `VERHOEFF_D`/`VERHOEFF_P` tables |

All 4 fixes are verified by passing unit and regression tests without any regressions to existing benchmarks.
