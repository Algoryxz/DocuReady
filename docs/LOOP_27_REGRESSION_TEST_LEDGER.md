# DOCUREADY LOOP 27 — REGRESSION TEST LEDGER
## Comprehensive Test Execution Ledger & Pass/Fail Records

---

### 1. Test Suite Breakdown

| Test Suite File | Component / Focus | Tests | Status | Duration |
|---|---|---|---|---|
| `tests/test_loop27_identifier_integrity.py` | Identifier taxonomy, glyph confusables, Verhoeff, sanitization | 13 | **13 PASSED** | 2.1 s |
| `tests/test_loop09_release_integrity.py` | Frozen Loop 10 release SHA-256 signatures | 9 | **9 PASSED** | 15.2 s |
| `tests/test_loop19_table_association.py` | TableGrid assembly & spatial association | 8 | **8 PASSED** | 5.1 s |
| `tests/test_loop21_header_and_decimal.py` | Hierarchical headers & decimal morphology | 12 | **12 PASSED** | 4.8 s |
| `tests/test_loop22_evidence_association.py` | Evidence association & multi-token guards | 15 | **15 PASSED** | 6.2 s |
| `tests/test_loop23_microfont_and_narrow_gutter.py` | Micro-font decimals & narrow gutters | 14 | **14 PASSED** | 5.9 s |
| `tests/test_loop24_calibration_and_performance.py` | Uncertainty calibration & latency guards | 10 | **10 PASSED** | 4.3 s |
| `tests/test_loop25_row_label_recovery.py` | Evidence-guided row label recovery | 12 | **12 PASSED** | 5.0 s |
| `tests/test_decision_safety.py` | Verification policy & safety gates | 22 | **22 PASSED** | 3.5 s |
| `tests/test_uncertainty_safety.py` | Confidence thresholds & abstention policy | 18 | **18 PASSED** | 3.2 s |
| `apps/desktop tests/**/*.test.ts` | Electron desktop sidecar, IPC & UI workflow | 25 | **25 PASSED** | 20.4 s |
| **All Remaining Engine Tests** | Normalizers, extractors, schemas, packs | 700+ | **ALL PASSED** | — |

**Total Test Count:** $\ge 850$ passing tests across Python and TypeScript.
