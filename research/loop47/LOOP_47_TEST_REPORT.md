# LOOP 47 — TEST REPORT

## 1. Python Regression Suite (`tests/test_loop*.py`)

```powershell
pytest (Get-ChildItem tests -Filter "test_loop*.py" | Sort-Object Name | ForEach-Object { $_.FullName }) -q
```

- **Result**: **294 passed, 0 failed, 0 skipped** (`308.78 s` / `0:05:08`)
- **Scope**: All Loop 01–46 Python test modules (`tests/test_loop*.py`), covering Loops 17–20 (evidence/table association, coordinate integrity), Loops 40–46 (in-process TessBaseAPI lifecycle, concurrency, 6-lang TSV parity, Strategy C/D upper-band routing & negative controls), and offline/privacy/recovery checks.

## 2. Electron Desktop Test Suite (`apps/desktop`)

```powershell
npm --prefix apps/desktop test -- --run
```

- **Result**: **25 passed, 0 failed, 0 skipped** (`32.90 s`)
- **Scope**: Disjoint TypeScript/Node test suite (`WorkspaceManager`, `SidecarManager`, IPC security, CSP, bounding-box transforms, evidence provenance, and end-to-end synthetic packet audit parity).

## 3. Disjoint Test Accounting

- Python (`tests/test_loop*.py`) and Desktop (`apps/desktop/tests/**/*.test.ts`) are disjoint (`0` shared tests): **319 / 319 passing** (`294` Python + `25` Desktop), `0` skipped, `0` failed.
