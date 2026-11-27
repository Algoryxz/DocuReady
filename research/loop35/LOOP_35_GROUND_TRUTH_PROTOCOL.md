# DOCUREADY — LOOP 35 GROUND-TRUTH PROTOCOL

- **Packet-Level Ground Truth:** Every test packet specifies expected readiness (`NO_ISSUES_FOUND`, `NEEDS_CHECKS`, `NOT_READY`), expected missing documents, wrong-slot flags, and expected cross-document verification outcomes.
- **Blind Freeze:** Partitions (DEV, CAL, BLIND) are SHA-256 hashed in `LOOP_35_BLIND_PARTITION_MANIFEST.json` prior to evaluation.
- **Licensing Carry-Forward (Loop 34):** FUNSD (IIT-CDIP research), CORD (CC-BY-SA 4.0), SROIE (ICDAR non-commercial), Indian Gazette (GODL / Sec 52(1)(q)), and Land Revenue restrictions remain explicitly tracked and are NOT bundled into production installers.
