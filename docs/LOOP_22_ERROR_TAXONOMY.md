# Loop 22 — Error Taxonomy & Classification Framework

**Framework:** Hierarchical Root-Cause Taxonomy for Document Evidence Verification  
**Scope:** Spatial Association, Label Binding, OCR Candidate Generation, Contextual Consistency, Policy Gates, and Ground Truth Integrity

---

## 1. Six-Pillar Root-Cause Taxonomy

Every failure or anomaly encountered during evidence association and critical field verification is categorized under this mutually exclusive primary taxonomy:

```
                  ┌───────────────────────────────────────────────┐
                  │    CRITICAL FIELD ERROR TAXONOMY (6 PILLARS)   │
                  └───────────────────────┬───────────────────────┘
                                          │
       ┌───────────────┬──────────────────┼──────────────────┬────────────────┐
       ▼               ▼                  ▼                  ▼                ▼
   [A. Spatial]   [B. Label]      [C. OCR Candidate]   [D. Context]     [E. Policy]     [F. Ground Truth]
   - Column gutter- Collision     - Digit confusion    - Wrong entity   - Uncalibrated  - Annotation defect
   - Neighbor cell- Distance echo - Preprocessing dot  - Unit mismatch  - Gutter bleed  - Scoring defect
   - Overlap      - Missing label - Garble glyph       - Cross-doc clash- No conf floor - Ambiguous GT
```

---

## 2. Taxonomy Distribution in Loop 21 vs Loop 22

| Category | Primary Failure Mechanism | Loop 21 Count | Loop 22 Resolved | Loop 22 Remaining | Primary Mitigation |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **A. Spatial Association** | Neighboring column capture / gutter bleed | 3 | 2 | 1 | Multi-token check, header-path cross check |
| **B. Label Association** | Label-echo or label collision | 0 | 0 | 0 | Syntactic type gating, label-echo rejection |
| **C. OCR Candidate** | False decimal insertion from character crossbars | 8 | 8 | 0 | Strictly isolated baseline dot morphology |
| **C. OCR Candidate** | Missed decimal or character confusion in low-res | 1 | 0 | 1 | Inherent optical resolution boundary |
| **D. Context Consistency** | Unit / semantic category contradiction | 0 | 0 | 0 | Semantic header-to-type validation |
| **E. Verification Policy** | Permissive acceptance of low-conf garble / bleed | 1 | 1 | 0 | Confidence floor (60.0), syntax garble filter |
| **F. Ground Truth** | Annotation mismatch (col index vs column header) | 1 | 1 | 1 | Risk-calibrated abstention on contradiction |
| **TOTAL** | | **14** | **12** | **3** | |

---

## 3. Prioritization & Engineering Severity

1. **P0: False Decimal Insertion (Severity: Critical)**
   - *Frequency:* 8 / 14 failures (57.1%).
   - *Impact:* Substantive monetary or quantitative distortion (e.g. `640` turned into `64.0`, turning a valid integer into an incorrect float).
   - *Intervention:* Replaced crude 60% baseline heuristic with 4-sided isolation filter (0 ink on left, right, and top) and trailing zero integer guard.

2. **P1: Permissive Acceptance of Degraded Evidence (Severity: High)**
   - *Frequency:* 3 / 14 failures (21.4%).
   - *Impact:* Verifies illegible noise (`fe}` at conf 35.0) or gutter bleed (`15000 1500`).
   - *Intervention:* Confidence floor ($< 60.0$), multi-token whitespace split guard, and syntax noise filter.

3. **P2: Column-Header Contradiction (Severity: High)**
   - *Frequency:* 2 / 14 failures (14.3%).
   - *Impact:* Extracts cell from wrong column when column index conflicts with semantic intent (e.g. `Freight` vs `Weight`).
   - *Intervention:* Header semantic compatibility verification before claim validation.
