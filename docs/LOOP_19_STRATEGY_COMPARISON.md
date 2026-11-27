# LOOP 19: Strategy Trade-Offs: Global Multilingual, Adaptive & Table Association

## 1. Executive Summary

Loop 18 demonstrated that on the expanded 25-document corpus, Global Multilingual (`eng+hin+ori`) achieved slightly lower micro corpus error rates (23.78% CER vs 24.44% for Adaptive) and ran faster (1,763 ms vs 2,475 ms). However, Adaptive OCR dramatically outperformed Global Multilingual on documents with native PDF text streams (Macro CER 44.22% vs 434.94%).

In Loop 19, we investigated how **Table-Aware Spatial Association** alters these architectural trade-offs.

---

## 2. Quantitative Comparison of Extraction Approaches

| Approach | Latency (ms) | OCR Invocations | Bounding Box Precision | Tabular SEM Rate | Title Banner Integrity |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Naive Global OCR (Loop 17/18)** | 1,763 ms | 1 | Medium (Full page text) | 50.0% (`STRESS_03`) | Preserved |
| **Image-Splitting Region OCR** | 4,916 ms | 2 | Low (Split errors at gutter) | 50.0% (Mangled banner) | Sliced in half |
| **Table-Aware Post-OCR Association (Loop 19)** | **1,766 ms** | **1** | **High (2D Cell Coordinates)** | **88.33% (10 Fixtures)** | **100% Preserved** |

---

## 3. Key Architectural Takeaways

1. **Post-OCR Spatial Association Beats Pre-OCR Image Splitting**:
   - Splitting images into vertical crops prior to OCR is inherently hazardous: full-width banners are bisected, and background separator lines generate false script noise.
   - Running full-page OCR in a single pass followed by geometric 1D projection profiling over the resulting word bounding boxes achieves higher accuracy, preserves title banners, and adds **less than 3 ms of computation**.
2. **Strategy Routing Guidelines**:
   - For monolingual Latin/English tabular documents: `FAST_PATH_ENG` + `build_table_grid` provides optimal latency (< 600 ms) and 100% critical-field accuracy.
   - For bilingual administrative forms: `GLOBAL_MULTILINGUAL` + `build_table_grid` prevents micro-band process explosion.
