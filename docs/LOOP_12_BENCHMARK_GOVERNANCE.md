# DOCUREADY — LOOP 12 BENCHMARK GOVERNANCE
## Specification & Protocols for Benchmark Integrity

Please refer to the primary governance document: [DOCUREADY_BENCHMARK_GOVERNANCE.md](file:///c:/Users/smara/Desktop/New%20folder/docs/DOCUREADY_BENCHMARK_GOVERNANCE.md).

### Summary of Governing Mandates:
1. **Provenance Classification:** Every sample explicitly tagged (`VERIFIED_EXTERNAL_OFFICIAL`, `VERIFIED_EXTERNAL_DERIVED`, `VERIFIED_SYNTHETIC_MODEL`, `VERIFIED_INTERNAL_FIXTURE`).
2. **Strict Anti-Hardcoding Rule:** Hardcoded simulation of metrics (e.g. 0.85/0.92 IoU) is prohibited and guarded by automated tests.
3. **Target Alignment Rule:** Scope parity between reference and hypothesis strings in CER/WER calculations.
4. **Unicode NFC Normalization:** Mandatory canonical decomposition/composition.
5. **Real Geometric IoU:** Real bipartite bounding box matching.
6. **Denominator Audit:** Strict invariant check ensuring total evaluated equals total manifest count.
