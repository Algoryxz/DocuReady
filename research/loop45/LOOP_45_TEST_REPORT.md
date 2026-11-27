# LOOP 45 — TEST REPORT

## 1. Python Regression Suite (`tests/test_loop*.py`)

```powershell
pytest (Get-ChildItem tests -Filter "test_loop*.py" | Sort-Object Name | ForEach-Object { $_.FullName }) -q
```

- **Result**: **289 passed, 0 failed, 0 skipped** (`338.20 s` / `0:05:38`)
- **Scope**: All Loop 01–44 Python test modules (`tests/test_loop*.py`), including Loops 17–20 (table/spatial association, coordinate integrity), Loops 40–44 (in-process TessBaseAPI lifecycle, concurrency, TSV parity, Strategy C/D upper-band routing), and offline/privacy/recovery checks.

## 2. Electron Desktop Test Suite (`apps/desktop`)

```powershell
npm --prefix apps/desktop test -- --run
```

- **Result**: **25 passed, 0 failed, 0 skipped** (`35.16 s`)
- **Scope**: Disjoint TypeScript/Node test suite covering `WorkspaceManager`, `SidecarManager`, IPC security, CSP, bounding-box transforms, evidence provenance, and end-to-end synthetic packet audit parity.

## 3. Independent Validation & Benchmark Runs

- `research/loop45/investigate_benchmark_boundary.py`: `n=30` interleaved paired warm + `n=5` cold subprocess observations (`LOOP_45_BENCHMARK_BOUNDARIES.json`).
- `research/loop45/run_loop45_validation.py`: `18` real/corpus docs + `12` synthetic/negative-control docs + threshold/resolution audit + `4` evidence-bounds checks (`LOOP_45_VALIDATION_RAW.json`).

## 4. Disjoint Test Accounting

- Python (`tests/test_loop*.py`) and Desktop (`apps/desktop/tests/**/*.test.ts`) are disjoint (`0` shared test cases): **314 / 314 passing** (`289` Python + `25` Desktop), `0` skipped, `0` failed.
