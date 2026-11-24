# Loop 26 - Reproduction Guide

## Verification Commands

```bash
# 1. Run Unit Regression Tests
python -m pytest tests/test_loop25_row_label_recovery.py tests/test_loop23_microfont_and_narrow_gutter.py -v

# 2. Run Desktop Test Suite
npm test --prefix apps/desktop

# 3. Run Release Binary Integrity Suite
python -m pytest tests/test_loop09_release_integrity.py -q

# 4. Run Normalization Collision Audit
python research/loop26/collision_audit/test_normalization_collisions.py

# 5. Run Cross-Document Verification Packets
python research/loop26/cross_doc/test_cross_document_packets.py

# 6. Execute Full Benchmark
python research/loop26/benchmark/run_loop26_benchmark.py
```
