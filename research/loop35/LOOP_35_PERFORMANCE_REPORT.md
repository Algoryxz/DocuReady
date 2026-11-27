# DOCUREADY — LOOP 35 WORKFLOW PERFORMANCE REPORT

Measured across 30 full 6-document packet runs (kept separate from single-rule microbenchmarks):
- **Complete Packet Validation:** Mean = `1.928 ms`, Median = `1.817 ms`, p95 = `3.776 ms`
- **Report Export (JSON + Markdown + PII Redaction):** Mean = `3.966 ms`, Median = `4.002 ms`, p95 = `6.281 ms`
- **Frozen Sidecar Cold Startup + Health:** `9877.01 ms`
