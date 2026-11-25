# DocuReady Loop 32 Branch Inventory

**Audit Date:** 2026-11-25  
**Current Branch:** `loop-32-repository-wide-bug-discovery`  
**Base Commit:** `a05954adcbdb706b98f401d2794b25e5e3aa2b85` (Loop 31)  
**Protected Competition Release:** Loop 10 (`bdc403a`)

---

## 1. Executive Summary

A comprehensive repository audit identified **51 branches** (50 local feature/loop branches and 1 remote tracking branch `origin/main`). Every research loop from Loop 01 through Loop 31 has an isolated, self-contained branch preserving its research artifacts, empirical datasets, and evaluation code.

---

## 2. Comprehensive Branch Categorization

### A. Core Release & Mainline Branches
| Branch Name | Head Commit | Description / Milestone | Status |
| :--- | :--- | :--- | :--- |
| `main` | `a05954a` | Primary trunk tracking Loop 31 sign-off | Active Trunk |
| `origin/main` | `a05954a` | Remote tracking branch at Algoryxz/DocuReady | Up-to-date |
| `loop-10-competition-demo-reliability-and-final-readiness` | `bdc403a` | **Frozen HackNation 2026 Competition Baseline** | Frozen & Protected |

### B. Product Excellence & Packaging Branches
| Branch Name | Head Commit | Description / Milestone |
| :--- | :--- | :--- |
| `feat/electron-desktop-foundation` | `d9323ea` | Initial Electron shell integration |
| `feat/loop5-independent-validation-and-demo` | `22c75ef` | Bundled OCR runtime & Windows packaging |
| `feat/loop6-release-integrity-and-reproducibility` | `360c3fb` | Electron startup crash fixes |
| `fix/final-desktop-release-stabilization` | `acd991e` | Squirrel lifecycle hooks & uninstaller polling |

### C. Foundational OCR & Geometry Loops (Loops 01–09)
| Branch Name | Head Commit | Focus |
| :--- | :--- | :--- |
| `loop-01-osd-performance-analysis` | `fd22194` | Elimination of redundant OSD |
| `loop-02-orientation-gate-assurance` | `cdf6a5e` | Two-tier OSD recovery & raster leak fix |
| `loop-03-skew-recovery-and-geometry` | `1e1c876` | Validated skew recovery & coordinate mapping |
| `loop-04-deskew-reliability-and-audit-integrity` | `ee195c5` | Deskew reliability & ambiguity resolution |
| `loop-05-extraction-normalization-and-cross-document-reliability` | `17c33ea` | Field normalization & cross-document intelligence |
| `loop-06-audit-decision-integrity-and-calibration` | `d1f0f0e` | Audit decision engine & 10 invariants |
| `loop-07-adversarial-corpus-and-decision-generalization` | `250093f` | Adversarial corpus expansion |
| `loop-08-desktop-workflow-integrity-and-review-ux` | `bea7856` | Desktop workflow recovery & human review UX |
| `loop-09-windows-release-integrity-and-deployment` | `9c2fb6d` | Packaged Windows runtime qualification |

### D. Empirical Benchmarking & Robustness Loops (Loops 11–23)
| Branch Name | Head Commit | Focus |
| :--- | :--- | :--- |
| `loop-11-independent-dataset-benchmark` | `e282e3b` | Independent OCR dataset benchmark |
| `loop-12-benchmark-integrity-audit` | `756062b` | Benchmark provenance & scoring integrity |
| `loop-13-column-aware-reading-order` | `0fa028d` | Column-aware reading order & layout |
| `loop-14-multilingual-indic-ocr-benchmarking` | `c50f4a2` | Multilingual Indic OCR benchmarking |
| `loop-15-region-aware-ocr-and-sparse-text-recovery` | `f3ea5c7` | Region-aware OCR & sparse text recovery |
| `loop-16-adaptive-image-preprocessing` | `bbfa5ef` | Adaptive image preprocessing |
| `loop-17-multi-engine-ocr-consensus` | `5c3e07f` | Multi-engine OCR consensus |
| `loop-18-table-structure-recognition` | `011bc51` | Table structure recognition |
| `loop-19-semi-structured-key-value-extraction` | `52047ff` | Semi-structured key-value extraction |
| `loop-20-document-classification-and-routing` | `2854930` | Document classification & routing |
| `loop-21-hierarchical-table-parsing` | `f56360c` | Hierarchical table parsing |
| `loop-22-complex-layout-generalization` | `82b49df` | Complex layout generalization |
| `loop-23-comprehensive-ocr-and-table-benchmark` | `f668ba2` | Comprehensive OCR & table benchmark |

### E. Qualification, Safety & Integrity Loops (Loops 24–32)
| Branch Name | Head Commit | Focus |
| :--- | :--- | :--- |
| `loop-24-independent-generalization-calibration` | `1623723` | Independent generalization calibration |
| `loop-25-row-label-recovery-and-coverage` | `5d9e84e` | Row-label recovery & coverage expansion |
| `loop-26-independent-real-world-generalization` | `9509017` | Independent real-world generalization |
| `loop-27-identifier-integrity-and-verification-safety` | `511ba82` | Identifier integrity & verification safety |
| `loop-28-cross-document-verification-reliability` | `ce0c9e7` | Cross-document verification reliability |
| `loop-29-calibration-cohort-integrity-and-generalization` | `e5fafd5` | Calibration integrity & cohort reconciliation |
| `loop-30-reproducibility-and-evaluation-integrity` | `626ad3c` | Reproducibility & evaluation integrity |
| `loop-31-independent-qualification-audit` | `a05954a` | Independent qualification audit & sign-off |
| `loop-32-repository-wide-bug-discovery` | `CURRENT` | Repository-wide bug discovery & technical debt |

---

## 3. Preservation Conclusion
No branch should be deleted or squashed. Every branch encapsulates valuable empirical data, regression tests, and research provenance essential for scientific audit and future development.
