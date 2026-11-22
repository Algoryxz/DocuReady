# LOOP 19: Agentic Skills Research & Selection Report

## 1. Catalog Inspection & Background

Per the Loop 19 Engineering Directive, we surveyed candidate skills from the **Agentic Awesome Skills (AAS)** repository ([github.com/sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills)), focusing strictly on skills addressing:
- Document layout analysis and geometric segmentation
- Tabular bounding box alignment and cell association
- OCR spatial provenance and line/word clustering
- Computer vision heuristics for gridline and whitespace detection
- Testing, benchmarking, and reliability validation

---

## 2. Evaluation Matrix for Loop 19 Needs

| Candidate Domain / Skill Pattern | Relevance to Loop 19 Mission | Ponytail Alignment | Assessment & Adoption Decision |
| :--- | :--- | :--- | :--- |
| **Bounding Box Projection Profiling (Horizontal/Vertical)** | High: Core geometric primitive to detect row bands and column gutters without heavy neural networks. | High: Pure NumPy 1D projections and array thresholding. Zero external libraries. | **Adopted as Pattern**: Implemented in native pure Python with NumPy for projection profiles. |
| **Interval Intersection / R-Tree Spatial Indexing** | Medium: Fast lookup of word overlap with rectangular cell boundaries. | Medium-High: A full R-Tree library (`rtree` / `libspatialindex`) is external bloat. Simple interval intersection logic ($[x_1, x_2] \cap [c_1, c_2]$) in Python standard library achieves the same result in < 15 lines of code. | **Adopted as Pattern (Stdlib)**: 1D bounding box overlap computation without external C-extensions. |
| **Heavy Table Transformer / Vision Model (e.g. Table-Transformer, TATR, PaddleOCR Table)** | Low / Incompatible: Deep neural networks (PyTorch/ONNX models > 200MB) requiring GPU or multi-second inference. | Zero: Violates competition freeze, offline low-latency requirements, and zero-weight footprint constraints. | **Rejected**: Heavyweight ML dependencies violate Ponytail and desktop runtime boundaries. |
| **Gridline Morphological Kernel Filter** | High: Morphological horizontal and vertical line extraction for bordered tables. | High: Uses existing Pillow (`ImageFilter`) or simple NumPy binary array operations. | **Adopted as Pattern**: Geometric line scanning using NumPy array slicing. |
| **Header-Value Semantic Association** | High: Associating numeric cell tokens with corresponding column header strings. | High: Pure spatial proximity (top-to-bottom column alignment). | **Adopted as Pattern**: Spatial column index mapping. |

---

## 3. Skills Adoption Conclusion

In accordance with Ponytail minimalism:
- Zero third-party skills were directly installed into the repository or runtime environment.
- The **Geometric Projection Profiling & Interval Association Pattern** was adopted and implemented directly in `src/docuready/ingest/table_association.py`.
- The implementation relies exclusively on existing libraries (`numpy`, `PIL`) already present in DocuReady, adding zero bloat or new external dependencies.
