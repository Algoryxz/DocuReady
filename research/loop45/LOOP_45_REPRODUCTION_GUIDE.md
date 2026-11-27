# LOOP 45 — REPRODUCTION GUIDE

Run all commands from `c:\Users\smara\Desktop\New folder`:

```powershell
# 1. Verify branch & Loop 10 artifact hashes
git rev-parse HEAD
git merge-base --is-ancestor 02baae0 HEAD; echo $LASTEXITCODE
git merge-base --is-ancestor bdc403a HEAD; echo $LASTEXITCODE

# 2. Interleaved paired stage-timing & cold subprocess benchmarks (n=30 warm, n=5 cold)
python research/loop45/investigate_benchmark_boundary.py

# 3. Independent cohort validation, negative controls, threshold audit & evidence bounds
python research/loop45/run_loop45_validation.py

# 4. Full Python Loop regression suite
pytest (Get-ChildItem tests -Filter "test_loop*.py" | Sort-Object Name | ForEach-Object { $_.FullName }) -q

# 5. Full Electron desktop suite
npm --prefix apps/desktop test -- --run
```
