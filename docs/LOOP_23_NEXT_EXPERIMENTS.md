# Loop 23 Roadmap & Next Experiments (Loop 24)

## 1. Candidate Research Directions for Loop 24

Building upon Loop 23's achievement of **0.00% False Verification Rate** and **100.00% Critical Field Precision**, the next research horizon focuses on safely expanding verified coverage without compromising precision.

### Priority 1: Sub-Cell Character Boundary Segmentation for Fused Narrow Columns
- **Context:** In `COHORT_H_03`, when two columns have zero whitespace gutter ($< 5\text{ px}$), Tesseract merges the numbers into a single 9-digit string (`125001250`).
- **Research Question:** Can localized character pitch analysis or digit width frequency modeling cleanly segment fused numeric strings into their component sub-column values, converting safe abstentions into verified exact matches?
- **Safety Gate:** Must maintain 100% precision and abstain if split ambiguity exceeds $5\%$.

### Priority 2: Multi-Page Spanning Table Header Propagation
- **Context:** Large financial ledgers or tax registers frequently span multiple pages, where page 2 and page 3 omit column headers.
- **Research Question:** Can cross-page table context pass column geometry and semantic headers from page 1 to subsequent pages while validating that page geometry has not shifted?

### Priority 3: Adaptive Binarization for Degraded Carbon Copies
- **Context:** Physical document scans often exhibit non-uniform illumination or carbon copy bleed.
- **Research Question:** Can localized Sauvola or Niblack binarization on candidate table crops improve character extraction in sub-10px fonts without increasing document latency beyond $600\text{ ms}$?
