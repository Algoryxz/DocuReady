# LOOP 46 — TEST REPORT

## 1. Python Regression Suite (`tests/test_loop*.py`)

Executed after final edit to `src/docuready/ingest/adaptive_ocr.py` and `tests/test_loop46_indic_header_latin_body.py`:

```powershell
pytest (Get-ChildItem tests -Filter "test_loop*.py" | Sort-Object Name | ForEach-Object { $_.FullName }) -q
```

- **Result**: **294 passed, 0 failed, 0 skipped** (`284.36 s` / `0:04:44`)
- Includes `5 / 5` new raster recovery & negative-control tests in `tests/test_loop46_indic_header_latin_body.py`.

## 2. Electron Desktop Test Suite (`apps/desktop`)

```powershell
npm --prefix apps/desktop test -- --run
```

- **Result**: **25 passed, 0 failed, 0 skipped** (`29.32 s`)

## 3. Disjoint Test Accounting

- Python (`tests/test_loop*.py`) and Desktop (`apps/desktop/tests/**/*.test.ts`) are completely disjoint (`0` shared tests): **319 / 319 passing** (`294` Python + `25` Desktop).
