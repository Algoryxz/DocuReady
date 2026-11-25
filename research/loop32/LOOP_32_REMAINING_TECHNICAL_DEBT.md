# DocuReady Loop 32 Remaining Technical Debt Ledger

**Programme:** DocuReady Product Excellence  
**Milestone:** Loop 32  
**Purpose:** Comprehensive Catalog of Deferred Technical Debt & Non-Blocking Optimizations  
**Date:** 2026-11-25  

---

## 1. Deferred Technical Debt Registry

### DEBT-01: Hardcoded Page Width in Region OCR (`src/docuready/ingest/region_ocr.py`)
- **Location:** Line 72 (`scale = 595.0 / orig_w`)
- **Issue:** Assumes portrait A4 standard width of 595.0 points. If a user uploads landscape documents (842.0 pt width) or US Letter sizes, relative bounding boxes may experience proportional scaling discrepancies.
- **Priority:** Low / Non-crashing.

### DEBT-02: Hardcoded Column Gutter in Table Association (`src/docuready/ingest/table_association.py`)
- **Location:** Line 157 (`min_internal_gap = 35`)
- **Issue:** Uses fixed 35-pixel threshold to separate table columns. In dense multi-column invoices with narrow gutters (e.g. 20–30 px), adjacent columns may be grouped into a single text block.
- **Priority:** Low / Edge-case layout.

### DEBT-03: Electron Preload Type Sharing
- **Location:** `apps/desktop/src/preload.ts` and `apps/desktop/src/shared/types.ts`
- **Issue:** Some IPC response types are duplicated between `preload.ts` and `types.ts` instead of directly importing from a single shared definition.
- **Priority:** Low / Maintenance cleanup.

### DEBT-04: Test Runner Pytest Deprecation Warning
- **Location:** `pytest_asyncio` and `anyio` plugins
- **Issue:** Warning emitted regarding `asyncio_default_fixture_loop_scope` unset in `pyproject.toml`.
- **Priority:** Trivial / Configuration hygiene.
