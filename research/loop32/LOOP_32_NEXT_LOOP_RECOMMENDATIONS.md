# DocuReady Loop 32 Next-Loop Recommendations

**Programme:** DocuReady Product Excellence  
**Target Milestone:** Loop 33  
**Recommended Theme:** Production Hardening, Adaptive Geometry & Full-Stack Packaging  
**Date:** 2026-11-25  

---

## 1. Core Recommendations for Loop 33

1. **Adopt Dynamic Page Geometry:**
   - Replace hardcoded 595.0 pt page width in `region_ocr.py` with dynamic aspect-ratio detection (`page.rect.width`, `page.rect.height`) to guarantee flawless coordinate transformation on landscape and arbitrary document dimensions.

2. **Implement Adaptive Table Gutters:**
   - Enhance `table_association.py` to calculate column gutters dynamically using median inter-word spacing rather than a fixed 35 px threshold.

3. **Multi-Unit Conversion Certificate Support:**
   - Expand `verify_cross_document_packet_claim` to allow explicit unit conversion rules (e.g. MT to KG) when the packet includes an authorized conversion schedule or when configured by policy.

4. **Continuous Packaging CI Pipeline:**
   - Add automated GitHub Actions workflow to verify the SHA-256 integrity of all release artifacts on every pull request.
