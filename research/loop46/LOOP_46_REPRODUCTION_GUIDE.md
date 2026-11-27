# LOOP 46 — REPRODUCTION GUIDE

Run all commands from `c:\Users\smara\Desktop\New folder`:

```powershell
# 1. Verify branch & Loop 10 artifact hashes
git rev-parse HEAD
git merge-base --is-ancestor c7ed04f HEAD; echo $LASTEXITCODE
git merge-base --is-ancestor bdc403a HEAD; echo $LASTEXITCODE

# 2. Failure reproduction & Strategy A-E calibration ablation
python research/loop46/reproduce_and_ablate.py

# 3. Full Loop 46 cohort, paired n=30 warm + n=5 cold performance & 6-lang TSV parity
python research/loop46/run_loop46_full_qualification.py

# 4. Loop 46 unit & raster tests
pytest tests/test_loop46_indic_header_latin_body.py -v

# 5. Full Python Loop regression suite & Electron desktop suite
pytest (Get-ChildItem tests -Filter "test_loop*.py" | Sort-Object Name | ForEach-Object { $_.FullName }) -q
npm --prefix apps/desktop test -- --run
```
