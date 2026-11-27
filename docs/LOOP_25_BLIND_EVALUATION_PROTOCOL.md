# Loop 25 - Independent Blind Evaluation Protocol

## Protocol Rules

1. **Strict Partition Isolation:** Algorithm development and threshold tuning were conducted exclusively on Development and Calibration cohorts (30 documents, 109 fields).
2. **Frozen Operating Policy:** The operating threshold $T^* = 70.0$ was frozen prior to running the Blind Evaluation partition.
3. **No Per-Document Heuristics:** Zero document-specific overrides, hard-coded bounding box coordinates, or document ID switches exist in the production source code.
4. **Deterministic Reproducibility:** The benchmark suite is executed twice in succession; any discrepancy between Run 1 and Run 2 constitutes an immediate qualification failure.
