# Loop 22 — Proposed Next Experiments (Loop 23+)

**Research Roadmap:** Post-Loop 22 Directions for DocuReady  
**Current Baseline Commit:** Loop 22 (`HEAD`)

---

## 1. High-Value Directions

### A. Sub-Pixel Super-Resolution for Micro-Fonts (P0)
- *Motivation:* The only 3 remaining false verifications in Loop 22 are 8px tall micro-font crops (`DEC_01`, `DEC_02`) where 1px decimal dots touch adjacent character strokes.
- *Proposed Experiment:* Investigate lightweight $2\times$ lanczos / bicubic upsampling specifically for sub-10px numeric crops before dot morphology analysis.

### B. Adaptive Cell Boundary Shrinking for Borderless Tight Gutters (P1)
- *Motivation:* Borderless tables with gutters $< 10\text{ px}$ (e.g. `CHALL_05`, `ASSOC_03`) currently cause multi-token cell merges that trigger abstention.
- *Proposed Experiment:* Implement interior vertical projection splitting on candidate cells with width $> 1.5\times$ median cell width to resolve the individual numbers rather than abstaining.

### C. Multi-Page Continued Table Tracking (P2)
- *Motivation:* Current table grids operate on single pages.
- *Proposed Experiment:* Track repeated column headers across page breaks to bind multi-page ledgers into a single unified virtual grid.
