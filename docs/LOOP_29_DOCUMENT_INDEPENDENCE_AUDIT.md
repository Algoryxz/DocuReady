# Loop 29 Document Independence & Duplicate Detection Audit

## 1. Independence Invariants
- **Identical Content Hash**: Strictly `DUPLICATE`.
- **Identical Raw Text**: Strictly `DUPLICATE`.
- **Generic Filename Collisions**: `invoice.pdf` with distinct content hashes is recognized as `INDEPENDENT`.
- **Shared Standardized Templates (>96% similarity)**: Distinct content hashes on shared government form templates are recognized as `INDEPENDENT`.
