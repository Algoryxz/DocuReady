# LOOP 44 — TEST REPORT

## 1. Python Regression Suite (`tests/test_loop*.py`)

Executed after final edit to `src/docuready/ingest/adaptive_ocr.py` and `tests/test_loop44_upper_band.py`:

```powershell
pytest (Get-ChildItem tests -Filter "test_loop*.py" | Sort-Object Name | ForEach-Object { $_.FullName }) -q
```

- **Result**: **289 passed, 0 failed** (`311.90 s` / `0:05:11`)
- Includes `22 / 22` tests in `tests/test_loop44_upper_band.py` (20 unit/`native_text` tests + 2 real raster OCR tests for `BLIND44_IND_HDR_LAT_ID_RASTER` and `BLIND44_ENG_UPPER_SEAL_RASTER`).

## 2. Desktop Test Suite (`apps/desktop`)

```powershell
npm --prefix apps/desktop test -- --run
```

- **Result**: **25 passed, 0 failed** (`45.79 s`)

## 3. Combined Total

- **314 / 314 tests passing** (`289` Python + `25` Desktop), **0 failures**.
