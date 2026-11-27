# DocuReady Loop 32 Defect Reproduction Evidence

**Programme:** DocuReady Product Excellence  
**Test Suite:** `tests/test_loop32_defect_reproduction.py`  
**Execution Timestamp:** 2026-11-25T06:12:40Z  
**Result:** 4/4 Tests Passing Post-Remediation (Previously 4/4 Failing)

---

## 1. Automated Test Execution Evidence

### Pre-Fix Failure Trace (Initial Audit)
```
FAILED tests/test_loop32_defect_reproduction.py::test_bug_032_001_tuple_bounding_box_extraction - AttributeError: 'tuple' object has no attribute 'x0'
FAILED tests/test_loop32_defect_reproduction.py::test_bug_032_002_iso_date_normalization_equivalence - AssertionError: assert '2026/03/15' == '15/03/2026'
FAILED tests/test_loop32_defect_reproduction.py::test_bug_032_003_metric_unit_cross_doc_verification - Policy check: multi-unit packets trigger CONTRADICTION
FAILED tests/test_loop32_defect_reproduction.py::test_bug_032_005_verhoeff_table_parity - AssertionError: assert False is True (norm_validate_verhoeff('234567890124'))
```

### Post-Fix Verification Trace
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.6.0
rootdir: C:\Users\smara\Desktop\New folder
configfile: pyproject.toml
collected 4 items

tests/test_loop32_defect_reproduction.py::test_bug_032_001_tuple_bounding_box_extraction PASSED [ 25%]
tests/test_loop32_defect_reproduction.py::test_bug_032_002_iso_date_normalization_equivalence PASSED [ 50%]
tests/test_loop32_defect_reproduction.py::test_bug_032_003_metric_unit_cross_doc_verification PASSED [ 75%]
tests/test_loop32_defect_reproduction.py::test_bug_032_005_verhoeff_table_parity PASSED [100%]

======================== 4 passed, 1 warning in 1.78s =========================
```

---

## 2. Test Case Specifications

1. `test_bug_032_001_tuple_bounding_box_extraction`:
   - Simulates a PDF page search returning `[(72.0, 144.0, 200.0, 160.0)]` raw 4-tuples.
   - Asserts that `_find_field_in_page_vector` extracts `[72.0, 144.0, 200.0, 160.0]` without raising `AttributeError`.

2. `test_bug_032_002_iso_date_normalization_equivalence`:
   - Evaluates `d_iso = "2026-03-15"` and `d_in = "15/03/2026"`.
   - Asserts that `normalize_claim_value(d_iso, "date") == "15/03/2026"` and `evaluate_semantic_claim_equivalence` yields `EQUIVALENT_NORMALIZED`.

3. `test_bug_032_003_metric_unit_cross_doc_verification`:
   - Tests `evaluate_semantic_claim_equivalence("1 MT", "weight", "1000 KG", "weight")` yielding `True` and `EQUIVALENT_NORMALIZED`.
   - Tests that multi-unit cross-document packet verification returns `CONTRADICTION` under conservative compliance policy.

4. `test_bug_032_005_verhoeff_table_parity`:
   - Tests standard valid Aadhaar number `"234567890124"`.
   - Asserts that `ident_validate_verhoeff` and `norm_validate_verhoeff` evaluate identically to `True`.
