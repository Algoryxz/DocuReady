# DocuReady Loop 32 Branch Inventory & Git Ref Audit

**Audit Date:** 2026-11-25  
**Current Branch:** `loop-32-repository-wide-bug-discovery`  
**Base Commit:** `3806d76`  
**Protected Competition Release:** Loop 10 (`bdc403a`)  

---

## 1. Executive Summary & Ref Reconciliation

A complete verification of actual local and remote branch listings in Git was conducted to reconcile against the historical "51-branch" directive description:
- **Actual Local Branches:** **39 local branches**
- **Actual Remote Branches:** **159 remote tracking branches** at `origin`
- **Total Unique Branch References:** **198 branch references**

All research loop branches (Loop 01 through Loop 32), feature branches, packaging branches, and remote governance refs are preserved bit-for-bit without deletion, squashing, or rebasing.

---

## 2. Complete Local Branch Registry (39 Branches)

### A. Mainline & Release Baseline (3 branches)
1. `main` (`a05954a` / `3806d76`) — Mainline research tracking branch
2. `loop-32-repository-wide-bug-discovery` (`3806d76`) — Active Loop 32 research branch
3. `loop-10-competition-demo-reliability-and-final-readiness` (`bdc403a`) — **Protected Frozen Competition Baseline**

### B. Desktop Shell & Packaging Foundations (4 branches)
4. `feat/electron-desktop-foundation` (`d9323ea`)
5. `feat/loop5-independent-validation-and-demo` (`22c75ef`)
6. `feat/loop6-release-integrity-and-reproducibility` (`360c3fb`)
7. `fix/final-desktop-release-stabilization` (`acd991e`)

### C. Foundational Research Loops 01–09 (9 branches)
8. `loop-01-osd-performance-analysis` (`fd22194`)
9. `loop-02-orientation-gate-assurance` (`cdf6a5e`)
10. `loop-03-skew-recovery-and-geometry` (`1e1c876`)
11. `loop-04-deskew-reliability-and-audit-integrity` (`ee195c5`)
12. `loop-05-extraction-normalization-and-cross-document-reliability` (`17c33ea`)
13. `loop-06-audit-decision-integrity-and-calibration` (`d1f0f0e`)
14. `loop-07-adversarial-corpus-and-decision-generalization` (`250093f`)
15. `loop-08-desktop-workflow-integrity-and-review-ux` (`bea7856`)
16. `loop-09-windows-release-integrity-and-deployment` (`9c2fb6d`)

### D. Benchmark & Generalization Loops 11–23 (15 branches)
17. `loop-11-independent-dataset-benchmark` (`e282e3b`)
18. `loop-12-benchmark-integrity-audit` (`756062b`)
19. `loop-13-column-aware-reading-order` (`0fa028d`)
20. `loop-14-india-document-corpus-and-multilingual-ocr` (`c50f4a2`)
21. `loop-15-region-aware-multilingual-ocr` (`f3ea5c7`)
22. `loop-16-adaptive-ocr-strategy` (`bbfa5ef`)
23. `loop-17-adaptive-ocr-efficiency-and-reliability` (`5c3e07f`)
24. `loop-18-independent-accuracy-and-critical-field-validation` (`011bc51`)
25. `loop-19-table-aware-evidence-and-field-association` (`52047ff`)
26. `loop-2-robustness` (`2854930`)
27. `loop-20-blind-generalization-and-verification-reliability` (`f56360c`)
28. `loop-21-header-fusion-and-decimal-integrity` (`82b49df`)
29. `loop-22-evidence-association-reliability` (`f668ba2`)
30. `loop-23-microfont-numeric-and-narrow-gutter` (`f668ba2`)
31. `loop-3-evidence-calibration` (`1e1c876`)

### E. Qualification, Integrity & Audit Loops 24–31 (8 branches)
32. `loop-24-independent-generalization-calibration` (`1623723`)
33. `loop-25-row-label-recovery-and-coverage` (`5d9e84e`)
34. `loop-26-independent-real-world-generalization` (`9509017`)
35. `loop-27-identifier-integrity-and-verification-safety` (`511ba82`)
36. `loop-28-cross-document-verification-reliability` (`ce0c9e7`)
37. `loop-29-calibration-cohort-integrity-and-generalization` (`e5fafd5`)
38. `loop-30-reproducibility-and-evaluation-integrity` (`626ad3c`)
39. `loop-31-independent-qualification-audit` (`a05954a`)

---

## 3. Remote Tracking Branches Summary (159 Branches)
At `origin`, 159 remote tracking branches cover historical PR reviews (`remotes/origin/pr/*`), governance tasks (`remotes/origin/task/*`), documentation syncs (`remotes/origin/docs/*`), and architectural migrations.

**Preservation Policy:** All 39 local and 159 remote branches remain intact. No remote changes or local pruning are permitted.
