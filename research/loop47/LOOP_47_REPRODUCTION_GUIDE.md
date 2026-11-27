# LOOP 47 — REPRODUCTION GUIDE

Run all commands from `c:\Users\smara\Desktop\New folder`:

```powershell
# 1. Verify branch & Loop 10 artifact hashes
git rev-parse HEAD
git merge-base --is-ancestor a9d9b7f HEAD; echo $LASTEXITCODE
git merge-base --is-ancestor bdc403a HEAD; echo $LASTEXITCODE

# 2. Unchanged Strategy C evaluation, expanded negative controls, overhead decomp & n=30 benchmarks
python research/loop47/run_loop47_audit.py

# 3. Full Python Loop regression suite
pytest (Get-ChildItem tests -Filter "test_loop*.py" | Sort-Object Name | ForEach-Object { $_.FullName }) -q

# 4. Full Electron desktop suite
npm --prefix apps/desktop test -- --run
```
