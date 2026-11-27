# LOOP 44 — REPRODUCTION GUIDE

Run all commands from `c:\Users\smara\Desktop\New folder`:

## 1. Verify Branch & Loop 10 Freeze Hashes
```powershell
git rev-parse HEAD
git merge-base --is-ancestor e5ba978 HEAD; echo $LASTEXITCODE
git merge-base --is-ancestor bdc403a HEAD; echo $LASTEXITCODE

$files = @(
  "apps\desktop\out\DocuReady-win32-x64\DocuReady.exe",
  "apps\desktop\out\DocuReady-win32-x64\resources\app.asar",
  "apps\desktop\out\DocuReady-win32-x64\resources\docuready_sidecar\docuready_sidecar.exe",
  "apps\desktop\out\make\squirrel.windows\x64\DocuReady-0.1.0-Setup.exe",
  "apps\desktop\out\make\zip\win32\x64\DocuReady-win32-x64-0.1.0.zip"
)
foreach ($f in $files) {
  $h = (Get-FileHash -Algorithm SHA256 $f).Hash.ToLower()
  $sz = (Get-Item $f).Length
  Write-Output "$f | $sz | $h"
}
```

## 2. Run Loop 44 Upper-Band Unit & Raster Tests
```powershell
pytest tests/test_loop44_upper_band.py -v
```

## 3. Run Raster Ablation, Cold Subprocess Benchmarks & TSV Parity
```powershell
python research/loop44/run_loop44_ablation_and_e2e.py
```

## 4. Run Warm Profile & E2E Benchmarks
```powershell
python research/loop44/scratch_reproduce_and_benchmark.py
```

## 5. Run Full Python & Desktop Test Suites
```powershell
pytest (Get-ChildItem tests -Filter "test_loop*.py" | Sort-Object Name | ForEach-Object { $_.FullName }) -q
npm --prefix apps/desktop test -- --run
```
