# DocuReady Loop 32 Defect Register & Bug Discovery Report

**Programme:** DocuReady Product Excellence  
**Loop:** 32 Closeout Correction  
**Audit Scope:** Repository-Wide Subsystems (18 Domains)  
**Execution Date:** 2026-11-25  

---

## 1. Overview of Discoveries & Severity Calibration

During the Loop 32 comprehensive repository audit, every subsystem was systematically audited for defects, mathematical errors, regression risks, and architectural inconsistencies.

### Severity Calibration Summary
- **Critical Severity:** **0 defects** (No critical vulnerabilities, data corruption, or crash hazards in release artifacts)
- **High Severity:** **3 defects** (BUG-032-001, BUG-032-004, BUG-032-005)
- **Medium Severity:** **3 defects** (BUG-032-002, BUG-032-006, BUG-032-007)
- **Low / Policy Clarified:** **1 item** (BUG-032-003)
- **Reproduced Defects:** **4 defects** directly reproduced with automated tests in [test_loop32_defect_reproduction.py](file:///c:/Users/smara/Desktop/New%20folder/tests/test_loop32_defect_reproduction.py) and remediated.

---

## 2. Itemized Bug Registry

### `BUG-032-001`: AttributeError on Tuple Bounding Box in Vector Page Search
- **Severity:** High
- **Subsystem:** Ingest / PDF Vector Extraction (`src/docuready/ingest/extractor.py`)
- **Impact:** Crashes PDF ingestion when using pluggable or mock PDF backends whose `search_for` returns `(x0, y0, x1, y1)` tuples instead of `fitz.Rect` objects.
- **Root Cause:** Direct property access `r.x0`, `r.y0` without checking for tuple indexing fallback.
- **Remediation:** Added `hasattr(r, "x0")` conditional check.
- **Status:** **REPRODUCED & FIXED** (Verified by `test_bug_032_001_tuple_bounding_box_extraction`).
- **Residual Risk:** None.

### `BUG-032-002`: ISO Date Normalization & Calendar Validity Parity
- **Severity:** Medium
- **Subsystem:** Evidence / Cross-Document Normalization (`src/docuready/evidence/cross_document.py`)
- **Impact:** Cross-document verification previously flagged contradictions between identical dates in ISO (`YYYY-MM-DD`) and Indian/Commonwealth (`DD/MM/YYYY`) formats, and lacked calendar validity checking.
- **Root Cause:** Regex only matched `DD/MM/YYYY` without canonicalizing to standard ISO format, and did not validate leap years or days per month via `datetime.date`.
- **Remediation:** Canonicalized all valid dates to ISO `YYYY-MM-DD`; added `datetime.date` calendar validation (validating leap year `29/02/2024`, rejecting `29/02/2025`, `31/02/2026`, and `31/04/2026`); abstained on format-ambiguous representations (`05/06/2026` vs `06/05/2026`).
- **Status:** **REPRODUCED & FIXED** (Verified by 5 automated tests in `test_loop32_defect_reproduction.py`).
- **Residual Risk:** Low. Ambiguous dates without format context safely abstain.

### `BUG-032-003`: Measurement Unit Equivalence vs Evidence-Policy Conflict Separation
- **Severity:** Low / Architectural Policy Clarification
- **Subsystem:** Evidence / Cross-Document Verification (`src/docuready/evidence/cross_document.py`)
- **Impact:** Ambiguity between physical metric equivalence (`1 MT == 1000 KG`) and cross-document packet rejection.
- **Root Cause:** Conservative audit safety policy established in Loop 28: disparate legal units across independent documents constitute an evidence-policy conflict requiring manual review or an authorized conversion schedule. Conflating this with a physical contradiction created semantic ambiguity.
- **Remediation:** Confirmed physical metric conversion in `evaluate_semantic_claim_equivalence`; clarified rejection reason in `verify_cross_document_packet_claim` as an `"Evidence policy conflict: disparate measurement units across claims ... require explicit conversion schedule or manual verification under conservative compliance standards"`.
- **Status:** **POLICY CLARIFIED & DOCUMENTED** (Verified by `test_bug_032_003_metric_unit_cross_doc_verification`).
- **Residual Risk:** None.

### `BUG-032-004`: Silent Document Overwrite on Duplicate Filename Registration
- **Severity:** High
- **Subsystem:** Desktop Shell / Workspace Manager (`apps/desktop/src/main/workspace.ts`)
- **Impact:** When a user uploaded multiple documents sharing the same filename (e.g. `invoice.pdf` from two distinct vendors), `WorkspaceManager.createPacket` staged both to `path.join(packetDir, doc.name)`, causing the second document to silently overwrite the first.
- **Root Cause:** Hardcoded use of `doc.name` without collision detection or disambiguation.
- **Remediation:** Tracked `seenNames` and disambiguated colliding basenames using `${base}_${doc.id}${ext}` while keeping clean names intact when unique.
- **Status:** **REPRODUCED & FIXED** (Verified across 25 Electron desktop test cases).
- **Residual Risk:** None.

### `BUG-032-005`: Mathematically Corrupted Duplicate Verhoeff D/P Tables in normalizer.py
- **Severity:** High
- **Subsystem:** Normalization / Identity Checksum Parity (`src/docuready/normalize/normalizer.py`)
- **Impact:** Valid 12-digit Aadhaar identification numbers accepted by `identifier_validation.py` were rejected by `normalizer.py`.
- **Root Cause:** `normalizer.py` contained a corrupted duplicate copy of the ISO/IEC 7064 Verhoeff multiplication (`D_TABLE`) and permutation (`P_TABLE`) matrices. Rows 5-9 in `D_TABLE` were written using mod-10 addition instead of the dihedral group $D_5$, and row 4 of `P_TABLE` transposed digits 0 and 7.
- **Remediation:** Pointed `D_TABLE` and `P_TABLE` directly to the authoritative `VERHOEFF_D` and `VERHOEFF_P` in `identifier_validation.py`.
- **Status:** **REPRODUCED & FIXED** (Verified by `test_bug_032_005_verhoeff_table_parity`).
- **Residual Risk:** None.

### `BUG-032-006`: Hardcoded Portrait A4 Width in Region OCR Coordinate Scaling
- **Severity:** Medium
- **Subsystem:** Ingest / Region OCR (`src/docuready/ingest/region_ocr.py`)
- **Impact:** Region OCR assumed portrait orientation width 595.0 pt when calculating relative coordinates, causing bounding box offset distortion on landscape pages.
- **Status:** **DOCUMENTED AS TECHNICAL DEBT** for next loop geometry refactor.
- **Residual Risk:** Affects coordinate bounding box visualization on landscape documents.

### `BUG-032-007`: Fixed Pixel Column Gutter Threshold in Table Association
- **Severity:** Medium
- **Subsystem:** Ingest / Table Association (`src/docuready/ingest/table_association.py`)
- **Impact:** Fixed `min_internal_gap = 35` px threshold causes narrow-gutter financial tables to fail column separation.
- **Status:** **DOCUMENTED AS TECHNICAL DEBT** for next loop layout engine.
- **Residual Risk:** Affects dense multi-column tabular schedules.
