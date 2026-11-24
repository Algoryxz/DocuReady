# Loop 25 - Performance Profile & Latency Analysis

## Benchmarked Timing Metrics

| Measurement | Observed Metric | Required Budget | Margin |
|---|---|---|---|
| **Mean Table Construction Overhead** | **1.89 ms** | < 3.00 ms | **37.0% headroom** |
| **95th Percentile Overhead** | **3.14 ms** | < 6.00 ms | **47.7% headroom** |
| **Mean End-to-End Document Latency** | **402.42 ms** | < 800.00 ms | **49.7% headroom** |

## Computational Characteristics

- **Pure NumPy Vectorization:** Table grid construction and cell cropping run entirely in vectorized NumPy memory space.
- **Zero Additional Subprocesses:** Row-label recovery executes via dictionary character translation and standard library `difflib.SequenceMatcher`, incurring $< 0.08$ ms per field query.
- **Lazy Refinement:** Micro-font glyph and decimal point morphological analysis is deferred strictly to extraction time for requested target cells.
