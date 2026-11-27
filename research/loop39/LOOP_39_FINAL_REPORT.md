# DOCUREADY — LOOP 39 FINAL REPORT

- **Branch:** `loop-39-ocr-probe-reuse-and-package-performance` | **Base:** `d66c8e5` | **Loop 10:** `bdc403a` (5/5 bit-exact)
- **Gate Summary:** 22 PASS, 3 FAIL (Gates O, P, W), 1 BLOCKED (Gate V).
- **Key Conclusions:**
  1. Thumbnail probe reuse for evidentiary extraction is **unsafe** and deliberately rejected.
  2. Hardened `adaptive_ocr.py` so probe timeouts/failures set `probe_uncertain=True` and route to `eng+hin+ori` instead of silently defaulting to `LATIN`.
  3. Adaptive `MONOLINGUAL_HIN` reduced Hindi CER by **37.2%** (`18.66%` -> `11.71%`).
  4. Paired alternating A/B trials proved Variant B (`-63.41 MB`) is functionally and statistically equivalent to Variant A (`27,447.14 ms` vs `27,288.26 ms`).
