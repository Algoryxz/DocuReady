# Loop 29 Reproduction Guide

```bash
git checkout loop-29-calibration-cohort-integrity-and-generalization
python research/loop29/reconciliation/build_cohort_reconciliation.py
python research/loop29/calibration/calibration_forensics.py
python research/loop29/calibration/packet_clustered_statistics.py
python research/loop29/corpus/build_identity_adversarial_corpus.py
python research/loop29/corpus/build_cohort_m_corpus.py
python research/loop29/ablations/run_extended_ablations.py
python research/loop29/benchmark/run_loop29_performance_benchmark.py
pytest tests/test_loop28_cross_document.py tests/test_loop27_identifier_integrity.py tests/test_loop09_release_integrity.py -q
npm test --prefix apps/desktop
```
