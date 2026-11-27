# LOOP 19: Prioritized Roadmap for Future Research (Loop 20)

## 1. Executive Summary

Based on the empirical findings and operational boundaries documented in Loop 19, we recommend four prioritized engineering experiments for subsequent loops.

---

## 2. Prioritized Experiment Backlog for Loop 20

### Experiment 1: Dual-Mode Morphological Line Detection
- **Motivation**: While 1D projection profiling works well on borderless tables, tables with explicit gridlines (`TAB_01`, `TAB_08`) have physical line pixels that can be detected directly.
- **Hypothesis**: Using morphological horizontal and vertical line extraction (via NumPy array slicing or Pillow filters) will provide exact pixel coordinates for cell corners, increasing cell F1 on bordered tables to $> 98\%$.
- **Target Metric**: Cell boundary precision and recall.

### Experiment 2: Pre-Profiling Radon / Hough Deskew Normalization
- **Motivation**: `TAB_10` demonstrated that a 2.2° tilt reduces cell extraction precision.
- **Hypothesis**: Adding a lightweight, sub-50ms deskew rotation step before running projection profiling will eliminate baseline wander and restore 100% cell accuracy on tilted scans.
- **Target Metric**: SEM on tilted fixtures > 90%.

### Experiment 3: 2-Tier Header Tree Assembly
- **Motivation**: `TAB_07` showed that parent super-headers (`ASSESSED TAX`) are flattened into leaf columns.
- **Hypothesis**: Constructing a parent-child relationship between super-headers in Row 0 and leaf headers in Row 1 will allow queries like `Assessed Tax -> Property Cess` without ambiguity.
- **Target Metric**: Merged-header field extraction F1 > 95%.

### Experiment 4: Sidecar IPC Native Table Packet Protocol
- **Motivation**: The desktop application currently receives flat findings.
- **Hypothesis**: Exposing structured `table_grid` arrays with row/col coordinates in sidecar JSON-RPC payloads will enable interactive table rendering in the desktop UI when the freeze is lifted.
- **Target Metric**: End-to-end IPC latency < 100 ms.
