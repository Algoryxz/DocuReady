# Loop 40 Test Execution Report

**Date:** 2026-11-27  
**Branch:** `loop-40-performance-multilingual-and-windows-qualification`

---

## 1. Python Regression & Security Suites

**Command:**
```powershell
pytest tests/test_loop09_release_integrity.py tests/test_loop10_demo_reliability.py tests/test_loop14_multilingual_ocr.py tests/test_loop15_region_aware_ocr.py tests/test_loop16_adaptive_ocr.py tests/test_loop17_adaptive_efficiency.py tests/test_loop18_accuracy_and_critical_fields.py tests/test_loop19_table_association.py tests/test_loop20_blind_generalization.py tests/test_loop27_identifier_integrity.py tests/test_loop28_cross_document.py tests/test_loop32_defect_reproduction.py tests/test_loop33_rule_adversarial.py tests/test_loop35_e2e_workflow.py tests/test_loop39_probe_hardening.py tests/test_redaction_safe_logging.py tests/test_ui_privacy.py tests/test_desktop_sidecar_protocol.py tests/test_evidence_provenance_contract.py tests/test_ocr_acceptance.py tests/test_ocr_integration.py -q
```

**Result:** **190 passed, 0 failed, 0 skipped** in **74.15s** (2 non-blocking deprecation warnings from `anyio`/`fitz`).

Targeted Adaptive OCR & Hardening run (`pytest ... -v` on Loops 16, 17, 18, 39):
- **29 passed, 0 failed** in **52.45s**.

---

## 2. Electron Desktop Test Suite & TypeScript Check

1. **TypeScript Typecheck (`apps/desktop`):**
   - Command: `npm run lint:types` (`tsc --noEmit`)
   - Result: **PASS** (exit code `0`, 0 errors)
2. **Desktop Unit & Sidecar Integration Tests (`apps/desktop`):**
   - Command: `npm test` (`node --experimental-strip-types --test --test-concurrency=1 tests/**/*.test.ts`)
   - Result: **25 passed, 0 failed, 0 skipped** in **39.30s**

---

## 3. Summary

| Suite | Passed | Failed | Skipped | Status |
| :--- | :---: | :---: | :---: | :--- |
| Python Core, Regression & Security (21 files) | 190 | 0 | 0 | **PASS** |
| Electron Desktop (`@docuready/desktop`) | 25 | 0 | 0 | **PASS** |
| TypeScript (`tsc --noEmit`) | — | 0 | — | **PASS** |
| **Total Executed Automated Tests** | **215** | **0** | **0** | **PASS** |
