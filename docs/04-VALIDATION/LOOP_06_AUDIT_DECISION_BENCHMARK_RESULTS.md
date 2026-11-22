# DocuReady — Loop 06 Audit Decision Engine Benchmark Results

**Date:** 2026-11-22  
**Corpus Size:** 16 controlled packets  
**Status Accuracy:** 100.0%  
**False READY Rate:** **0.0%** (Target: 0.0%)  
**False NOT_READY Rate:** **0.0%**  
**Score Determinism:** 100.0%  

---

## 1. Decision Invariants Verification

| Invariant ID | Description | Result |
|---|---|---|
| `INV-1_HARD_CONFLICT_NEVER_READY` | A packet with a confirmed hard defect (Status.FAIL) must always resolve to NOT_READY | ✅ PASS |
| `INV-2_MISSING_DOC_NEVER_READY` | A packet with an absent mandatory document (Status.MISSING) must always resolve to NOT_READY | ✅ PASS |
| `INV-3_UNREADABLE_DOC_NEVER_READY` | An unreadable mandatory document (Status.REVIEW) must never resolve to NO_ISSUES_FOUND | ✅ PASS |
| `INV-4_AMBIGUITY_NEVER_FALSE_FAIL` | Ambiguous evidence or compatible variation must abstain to REVIEW/WARN and never emit false FAIL | ✅ PASS |
| `INV-5_SOFT_WARN_NEVER_FORCES_NOT_READY` | A packet with soft warnings (Status.WARN) and no hard failures must resolve to NEEDS_CHECKS | ✅ PASS |
| `INV-6_SCORE_CANNOT_DOWNGRADE_STATUS` | High residual readiness score (>= 75) cannot downgrade a confirmed hard defect to READY | ✅ PASS |
| `INV-7_DUPLICATE_FINDING_DEDUPLICATION` | Identical rule findings are unified; duplicate penalties are never double-deducted | ✅ PASS |
| `INV-8_ORDER_INVARIANCE` | Readiness status derivation is strictly order-invariant across all permutation orders | ✅ PASS |
| `INV-9_EMPTY_EXECUTION_FAILS_CLOSED` | Empty rule evaluation set returns NEEDS_CHECKS; never emits false green NO_ISSUES_FOUND | ✅ PASS |
| `INV-10_EXCEPTION_SAFETY_FAIL_CLOSED` | Rule execution exceptions fail closed to Status.REVIEW and ReasonCode.INSUFFICIENT_DATA | ✅ PASS |

---

## 2. Packet Evaluation Matrix (16 Packets)

| Packet ID | Category | Expected Status | Actual Status | Match | Score (Exp/Act) | Time (ms) |
|---|---|---|---|---|---|---|
| `PKT_01_CLEAN` | CLEAN | `NO_ISSUES_FOUND` | `NO_ISSUES_FOUND` | ✅ PASS | 100/100 | 100.3 |
| `PKT_02_NAME_MISMATCH` | DEFECTIVE | `NOT_READY` | `NOT_READY` | ✅ PASS | 75/75 | 83.2 |
| `PKT_03_DOB_MISMATCH` | DEFECTIVE | `NOT_READY` | `NOT_READY` | ✅ PASS | 75/75 | 90.1 |
| `PKT_04_INCOME_EXCEEDS_CEILING` | DEFECTIVE | `NOT_READY` | `NOT_READY` | ✅ PASS | 65/65 | 83.0 |
| `PKT_05_MISSING_MANDATORY_DOC` | DEFECTIVE | `NOT_READY` | `NOT_READY` | ✅ PASS | 65/65 | 63.1 |
| `PKT_06_UNREADABLE_MANDATORY_DOC` | UNCERTAIN | `NEEDS_CHECKS` | `NEEDS_CHECKS` | ✅ PASS | 75/75 | 2005.1 |
| `PKT_07_COMPATIBLE_NAME_VARIATION` | UNCERTAIN | `NEEDS_CHECKS` | `NEEDS_CHECKS` | ✅ PASS | 75/75 | 234.4 |
| `PKT_08_EXPIRED_CERTIFICATE` | DEFECTIVE | `NOT_READY` | `NOT_READY` | ✅ PASS | 75/75 | 228.4 |
| `PKT_09_DOMICILE_MISMATCH` | DEFECTIVE | `NOT_READY` | `NOT_READY` | ✅ PASS | 75/75 | 233.6 |
| `PKT_10_INTERACTION_NAME_CONFLICT_AND_MISSING_DOC` | INTERACTION | `NOT_READY` | `NOT_READY` | ✅ PASS | 40/40 | 176.6 |
| `PKT_11_INTERACTION_DOB_CONFLICT_AND_UNREADABLE_DOC` | INTERACTION | `NOT_READY` | `NOT_READY` | ✅ PASS | 50/50 | 2188.1 |
| `PKT_12_SLOT_MISMATCH` | UNCERTAIN | `NEEDS_CHECKS` | `NEEDS_CHECKS` | ✅ PASS | 90/90 | 183.2 |
| `PKT_13_CATEGORY_EXEMPTION_VERIFIED` | CLEAN | `NO_ISSUES_FOUND` | `NO_ISSUES_FOUND` | ✅ PASS | 100/100 | 223.1 |
| `PKT_14_CATEGORY_EXEMPTION_UNCERTAIN` | INTERACTION | `NOT_READY` | `NOT_READY` | ✅ PASS | 65/65 | 203.1 |
| `PKT_15_DUPLICATE_DOCUMENTS_CLEAN` | CLEAN | `NO_ISSUES_FOUND` | `NO_ISSUES_FOUND` | ✅ PASS | 100/100 | 177.8 |
| `PKT_16_EMPTY_PACKET_FAIL_CLOSED` | DEFECTIVE | `NOT_READY` | `NOT_READY` | ✅ PASS | 0/0 | 1.6 |

---

## 3. Status Confusion Matrix

| Expected Status | Actual: `NO_ISSUES_FOUND` | Actual: `NEEDS_CHECKS` | Actual: `NOT_READY` |
|---|---|---|---|
| `NO_ISSUES_FOUND` | 0 | 0 | 0 |
| `NEEDS_CHECKS` | 0 | 0 | 0 |
| `NOT_READY` | 0 | 0 | 0 |

---

## 4. Scoring Calibration & Determinism

- **Formula:** `Score = max(0, min(100, 100 - sum(finding_penalties)))`
- **FATAL (Missing Document):** -35 pts
- **CRITICAL (Hard Defect):** -25 pts
- **REVIEW (Uncertainty / Slot Mismatch):** -10 pts
- **WARNING (Compatible Variation):** -5 pts
- **INFO / EXEMPT:** 0 pts
- **Determinism across 5 repeated trials:** [100, 100, 100, 100, 100] (Variance: 0.0)
- **Observed Score Range:** 0 to 100

---

## 5. Evidence Provenance & Privacy Integrity

- **Bounding Box Geometry Valid:** True
- **Honest Missing Evidence (No Invented BBoxes):** True
- **Privacy PII Masking Verified:** True
- **Host Paths Scrubbed from Reports:** True
- **Offline Air-Gapped Operation:** True