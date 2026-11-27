# DOCUREADY — LOOP 15 NEXT EXPERIMENTS
## Strategic Roadmap for Post-Loop 15 Multilingual & Vision-Language Research

**Project:** DocuReady — HackNation 2026  
**Engineering Loop:** 15  
**Date:** November 2026  
**Status:** PROPOSED & PRIORITIZED  

---

## 1. Prioritized Experimental Matrix

Based on Loop 15 findings, the following research directions represent the highest-yield engineering investigations for subsequent development cycles:

| Priority | Initiative | Technical Description | Expected Impact |
| :--- | :--- | :--- | :--- |
| **P1** | **Parallel Sub-Image Threading** | Fan out sub-image Tesseract CLI calls across Python `ThreadPoolExecutor` workers. | **$2.5\times$ to $3.5\times$ latency reduction** on multi-region documents. |
| **P2** | **Composite Region Mosaic Tiling** | Pack isolated sub-image crops into a single consolidated canvas with whitespace gutters and run one unified OCR call. | Eliminates subprocess spawn overhead for dense tables. |
| **P3** | **Script Expansion (Bengali, Tamil, Telugu)** | Add traineddata models and Unicode regex ranges for eastern and southern Indian state documents. | Extends national coverage from 3 to 6 major Indian scripts. |
| **P4** | **Hybrid Vision-Language Verification** | Explore lightweight quantized on-device SLMs (e.g., SmolVLM-256M / Moondream2 ONNX) for semantic field validation. | Resolves complex cursive handwriting and low-contrast stamps. |
| **P5** | **Morphological Shirorekha Binarization** | Adaptive local binarization tuned specifically to preserve top horizontal headline continuity in degraded Devanagari scans. | Reduces Devanagari CER on noisy scans by ~15%. |

---

## 2. Methodology & Guardrail Protocols

All future experimental iterations must strictly adhere to the qualification invariants proven in Loops 01 through 15:
1. **Zero Regression on Sealed Baselines:** Golden baseline bit-exact tests (22/22) must pass without modification.
2. **Offline Local Execution:** No cloud APIs, telemetry, or external network connections during verification.
3. **Provable Provenance:** All training or benchmark data must be tracked with SHA-256 checksums in official manifests under authorized public licenses.
