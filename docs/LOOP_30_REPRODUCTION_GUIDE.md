# Loop 30 — Complete Reproduction Guide

## 1. Quick Start / One-Command Verification

To independently verify the entire Loop 30 qualification suite, execute the following commands in order:

```powershell
# 1. Verify Git Ancestry & Release Integrity
git rev-parse HEAD
# Output: e5fafd5614ec0646beca37e943439da000116311 (or Loop 30 commit)
python -m pytest tests/test_loop09_release_integrity.py -q
# Output: 9 passed

# 2. Run Multi-Loop Cohort & Field Accounting Reconciliation
python research/loop30/reconciliation/reconcile_all_cohorts.py
# Output: 221 docs, 791 fields, 344 exact, 0 false, 447 abstained (100% exact match)

# 3. Run Cohort M Provenance Audit
python research/loop30/corpus/audit_cohort_m_provenance.py
# Output: 30 packets, 103 claims, hash verified bit-exact

# 4. Run Calibration, 10-Bin Data, Bootstrap & Uncertainty Analysis
python research/loop30/calibration/reproduce_calibration.py
# Output: Candidate ECE: 46.93%, Verified ECE: 5.93%, Wilson Score CI: [91.62%, 100.0%]

# 5. Run Extended 10-Mode Ablations
python research/loop29/ablations/run_extended_ablations.py
# Output: 10 modes evaluated across L28 and Cohort M

# 6. Run Identity Adversarial Suite
python research/loop29/corpus/build_identity_adversarial_corpus.py
# Output: 20/20 cases PASSED

# 7. Run Performance & Determinism Benchmark
python research/loop29/benchmark/run_loop29_performance_benchmark.py
# Output: Mean latency: 0.18 ms, p95: 0.36 ms, 0 discrepancies

# 8. Run Complete Regression Test Suites
python -m pytest tests/test_loop28_cross_document.py tests/test_loop27_identifier_integrity.py tests/test_loop09_release_integrity.py -q
npm test --prefix apps/desktop
```

---

## 2. Generated Artifacts Reference
- Machine-Readable Ledger: `research/loop30/reconciliation/reconciliation_ledger.json`
- Cohort M Provenance: `research/loop30/corpus/cohort_m_provenance_audit.json`
- Calibration Bin CSV: `docs/LOOP_30_CALIBRATION_BIN_DATA.csv`
- Packet Metrics CSV: `docs/LOOP_30_PACKET_METRICS.csv`
- Uncertainty Summary: `research/loop30/results/packet_bootstrap_summary.json`
