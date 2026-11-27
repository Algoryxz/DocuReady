# PHASE 1 — REPOSITORY STATE & TEAM SAFETY AUDIT

**Project:** `Algoryxz/DocuReady`  
**Audit Date:** 2026-11-27  
**Scope:** Read-only baseline inventory of all local branches, remote-tracking branches, PR refs, worktrees, stashes, tags, and untracked working-tree files.

---

## 1. Executive Summary & Critical Findings

- **Total refs inspected:** 213 (54 local branches, 77 remote-tracking non-PR branches/HEAD-alias, 82 `origin/pr/*` refs).
- **Active Worktree:** `C:/Users/smara/Desktop/New folder` checked out at `loop-47-independent-mixed-script-generalization` (`23a3e09`).
- **Tags:** None (`0` tags).
- **Stashes:** `1` stash (`stash@{0}` on `loop-3-evidence-calibration`: `temp-test-artifacts`, containing 12 cached `.pyc` and synthetic `.pdf` timestamp/byte diffs).
- **CRITICAL DISCOVERY — Dual Root Histories:**
  1. **Orphan / Legacy HackNation MVP Root (`22377d5`):** Local `main` (`22377d5`, `baseline: DocuReady Loop 1 verified MVP state`, 2026-11-13) has **no common ancestor** with `origin/main` (`392ce9a`, root `ba09593`, 2026-11-14). Two local-only branches (`loop-2-robustness` at `caec706`, `loop-3-evidence-calibration` at `73b4051`) descend from `22377d5`.
  2. **Active Mainline Root (`ba09593`):** `origin/main` (`392ce9a`, 316 commits from `ba09593`) and all `origin/*` branches, plus `fix/final-desktop-release-stabilization` (`acd991e`) and `loop-01` through `loop-47` (`23a3e09`), descend from `ba09593`.
- **Local `main` vs `origin/main`:** Completely diverged (unrelated histories: `1` commit on local `main` vs `316` commits on `origin/main`).
- **Loop 01–47 Chain:** Forms a single linear 50-commit chain on top of `origin/main` (`392ce9a`): `origin/main` -> `fix/final-desktop-release-stabilization` (2 commits, `acd991e`) -> `loop-01`..`loop-10` (10 commits, `bdc403a`) -> `loop-11`..`loop-47` (38 commits, `23a3e09`). None of these 50 commits are pushed to `origin`.

---

## 2. Working Tree, Worktree, Stash, and Remote State

### 2.1 Remotes
- `origin`: `https://github.com/Algoryxz/DocuReady.git` (fetch & push)

### 2.2 Worktrees
| Path | HEAD | Checked-out Branch | Dirty State |
|---|---|---|---|
| `C:/Users/smara/Desktop/New folder` | `23a3e09` | `loop-47-independent-mixed-script-generalization` | Clean tracked files; 33 untracked paths |

> **Safety Note:** No other active worktrees exist. All integration work will use an isolated Git worktree or clean branch without disturbing untracked files.

### 2.3 Untracked Files & Directories (Preserved)
- `.agents/`
- `docs/product/`
- `hacknation-arena-v2/`
- `hacknation-arena-v3/`
- `hacknation-arena/`
- `presentation/DocuReady_HackNation_2026_Final.pdf`
- `presentation/DocuReady_HackNation_2026_Final.pptx`
- `presentation/PRESENTATION_ASSET_MANIFEST.md`
- `presentation/PRESENTATION_RESEARCH_NOTES.md`
- `presentation/PRESENTATION_SOURCE_AUDIT.md`
- `presentation/assets/`
- `presentation/generate_deck.py`
- `presentation/slide_1.png`
- `presentation/slide_2.png`
- `presentation/slide_3.png`
- `presentation/slide_4.png`
- `presentation/slide_5.png`
- `presentation/slide_6.png`
- `research/loop44/BLIND44_ENG_UPPER_SEAL_RASTER.png`
- `research/loop44/BLIND44_IND_HDR_LAT_ID_RASTER.png`
- `research/loop44/BLIND44_LAT_HDR_HIN_BODY_RASTER.png`
- `research/loop44/run_loop44_ablation_and_e2e.py`
- `research/loop44/scratch_reproduce_and_benchmark.py`
- `research/loop45/investigate_benchmark_boundary.py`
- `research/loop45/run_loop45_validation.py`
- `research/loop45/synthetic_cohort/`
- `research/loop46/negative_controls/`
- `research/loop46/reproduce_and_ablate.py`
- `research/loop46/run_loop46_full_qualification.py`
- `research/loop47/negative_controls/`
- `research/loop47/run_loop47_audit.py`
- `research/loop47/synthetic_cohort/`
- `sidecar/tessdata_extra/`

### 2.4 Stashes
- `stash@{0}`: `On loop-3-evidence-calibration: temp-test-artifacts` — 12 files (`__pycache__/*.pyc` and `docuready-mvp/synthetic_data/adversarial_tmp/*.pdf`). Left untouched.

---

## 3. Local Branches Inventory (54 branches)

| Branch | HEAD | Root | Merge Base (`origin/main`) | Ahead/Behind (`origin/main`) | Ancestor of `origin/main`? | Ancestor of `loop-47`? | Author | Date |
|---|---|---|---|---|---|---|---|---|
| `feat/electron-desktop-foundation` | `d9323ea` | `ba09593` | `d9323ea` | 78 / 0 | Yes | Yes | DocuReady Auditor | 2026-11-16 |
| `feat/loop5-independent-validation-and-demo` | `22c75ef` | `ba09593` | `22c75ef` | 75 / 0 | Yes | Yes | DocuReady Auditor | 2026-11-16 |
| `feat/loop6-release-integrity-and-reproducibility` | `360c3fb` | `ba09593` | `360c3fb` | 41 / 0 | Yes | Yes | DocuReady Auditor | 2026-11-19 |
| `fix/final-desktop-release-stabilization` | `acd991e` | `ba09593` | `392ce9a` | 0 / 2 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-01-osd-performance-analysis` | `fd22194` | `ba09593` | `392ce9a` | 0 / 3 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-02-orientation-gate-assurance` | `cdf6a5e` | `ba09593` | `392ce9a` | 0 / 4 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-03-skew-recovery-and-geometry` | `1e1c876` | `ba09593` | `392ce9a` | 0 / 5 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-04-deskew-reliability-and-audit-integrity` | `ee195c5` | `ba09593` | `392ce9a` | 0 / 6 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-05-extraction-normalization-and-cross-document-reliability` | `17c33ea` | `ba09593` | `392ce9a` | 0 / 7 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-06-audit-decision-integrity-and-calibration` | `d1f0f0e` | `ba09593` | `392ce9a` | 0 / 8 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-07-adversarial-corpus-and-decision-generalization` | `250093f` | `ba09593` | `392ce9a` | 0 / 9 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-08-desktop-workflow-integrity-and-review-ux` | `bea7856` | `ba09593` | `392ce9a` | 0 / 10 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-09-windows-release-integrity-and-deployment` | `9c2fb6d` | `ba09593` | `392ce9a` | 0 / 11 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-10-competition-demo-reliability-and-final-readiness` | `bdc403a` | `ba09593` | `392ce9a` | 0 / 12 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-11-independent-dataset-benchmark` | `e282e3b` | `ba09593` | `392ce9a` | 0 / 13 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-12-benchmark-integrity-audit` | `756062b` | `ba09593` | `392ce9a` | 0 / 14 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-13-column-aware-reading-order` | `e601d11` | `ba09593` | `392ce9a` | 0 / 15 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-14-india-document-corpus-and-multilingual-ocr` | `ba3e306` | `ba09593` | `392ce9a` | 0 / 16 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-15-region-aware-multilingual-ocr` | `39cde88` | `ba09593` | `392ce9a` | 0 / 17 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-16-adaptive-ocr-strategy` | `de63549` | `ba09593` | `392ce9a` | 0 / 18 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-17-adaptive-ocr-efficiency-and-reliability` | `69addb5` | `ba09593` | `392ce9a` | 0 / 19 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-18-independent-accuracy-and-critical-field-validation` | `9360fd2` | `ba09593` | `392ce9a` | 0 / 20 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-19-table-aware-evidence-and-field-association` | `2d7aab5` | `ba09593` | `392ce9a` | 0 / 21 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-2-robustness` | `caec706` | `22377d5` | None | N/A (unrelated) | No | No | DocuReady Auditor | 2026-11-13 |
| `loop-20-blind-generalization-and-verification-reliability` | `1dcd69d` | `ba09593` | `392ce9a` | 0 / 22 | No | Yes | DocuReady Auditor | 2026-11-22 |
| `loop-21-header-fusion-and-decimal-integrity` | `4a6a46e` | `ba09593` | `392ce9a` | 0 / 23 | No | Yes | DocuReady Auditor | 2026-11-23 |
| `loop-22-evidence-association-reliability` | `0b7629d` | `ba09593` | `392ce9a` | 0 / 24 | No | Yes | DocuReady Auditor | 2026-11-24 |
| `loop-23-microfont-numeric-and-narrow-gutter` | `f668ba2` | `ba09593` | `392ce9a` | 0 / 25 | No | Yes | DocuReady Auditor | 2026-11-24 |
| `loop-24-independent-generalization-calibration` | `1623723` | `ba09593` | `392ce9a` | 0 / 26 | No | Yes | DocuReady Auditor | 2026-11-24 |
| `loop-25-row-label-recovery-and-coverage` | `5d9e84e` | `ba09593` | `392ce9a` | 0 / 27 | No | Yes | DocuReady Auditor | 2026-11-24 |
| `loop-26-independent-real-world-generalization` | `9509017` | `ba09593` | `392ce9a` | 0 / 28 | No | Yes | DocuReady Auditor | 2026-11-24 |
| `loop-27-identifier-integrity-and-verification-safety` | `511ba82` | `ba09593` | `392ce9a` | 0 / 29 | No | Yes | DocuReady Auditor | 2026-11-24 |
| `loop-28-cross-document-verification-reliability` | `ce0c9e7` | `ba09593` | `392ce9a` | 0 / 30 | No | Yes | DocuReady Auditor | 2026-11-24 |
| `loop-29-calibration-cohort-integrity-and-generalization` | `e5fafd5` | `ba09593` | `392ce9a` | 0 / 31 | No | Yes | DocuReady Auditor | 2026-11-24 |
| `loop-3-evidence-calibration` | `73b4051` | `22377d5` | None | N/A (unrelated) | No | No | DocuReady Auditor | 2026-11-13 |
| `loop-30-reproducibility-and-evaluation-integrity` | `626ad3c` | `ba09593` | `392ce9a` | 0 / 32 | No | Yes | DocuReady Auditor | 2026-11-25 |
| `loop-31-independent-qualification-audit` | `a05954a` | `ba09593` | `392ce9a` | 0 / 33 | No | Yes | DocuReady Auditor | 2026-11-25 |
| `loop-32-repository-wide-bug-discovery` | `12d6512` | `ba09593` | `392ce9a` | 0 / 35 | No | Yes | DocuReady Auditor | 2026-11-25 |
| `loop-33-domain-rules-and-decision-policy-audit` | `decce84` | `ba09593` | `392ce9a` | 0 / 36 | No | Yes | DocuReady Auditor | 2026-11-25 |
| `loop-34-independent-ocr-extraction-accuracy` | `fe7ce23` | `ba09593` | `392ce9a` | 0 / 37 | No | Yes | DocuReady Auditor | 2026-11-26 |
| `loop-35-end-to-end-workflow-reliability` | `3a7e55f` | `ba09593` | `392ce9a` | 0 / 38 | No | Yes | DocuReady Auditor | 2026-11-26 |
| `loop-36-windows-release-installation-recovery-qualification` | `071e34a` | `ba09593` | `392ce9a` | 0 / 39 | No | Yes | DocuReady Auditor | 2026-11-26 |
| `loop-37-windows-deployment-remediation` | `ea09c79` | `ba09593` | `392ce9a` | 0 / 40 | No | Yes | DocuReady Auditor | 2026-11-26 |
| `loop-38-multilingual-ocr-routing-and-package-qualification` | `d66c8e5` | `ba09593` | `392ce9a` | 0 / 41 | No | Yes | DocuReady Auditor | 2026-11-26 |
| `loop-39-ocr-probe-reuse-and-package-performance` | `77c1f57` | `ba09593` | `392ce9a` | 0 / 42 | No | Yes | DocuReady Auditor | 2026-11-27 |
| `loop-40-performance-multilingual-and-windows-qualification` | `b487f03` | `ba09593` | `392ce9a` | 0 / 43 | No | Yes | DocuReady Auditor | 2026-11-27 |
| `loop-41-inprocess-ocr-reliability-and-release-qualification` | `66d7c3f` | `ba09593` | `392ce9a` | 0 / 44 | No | Yes | DocuReady Auditor | 2026-11-27 |
| `loop-42-e2e-ocr-performance-and-production-qualification` | `2849936` | `ba09593` | `392ce9a` | 0 / 45 | No | Yes | DocuReady Auditor | 2026-11-27 |
| `loop-43-mixed-script-routing-and-regional-ocr` | `e5ba978` | `ba09593` | `392ce9a` | 0 / 46 | No | Yes | DocuReady Auditor | 2026-11-27 |
| `loop-44-upper-band-mixed-script-and-e2e-integrity` | `02baae0` | `ba09593` | `392ce9a` | 0 / 47 | No | Yes | DocuReady Auditor | 2026-11-27 |
| `loop-45-independent-upper-band-generalization` | `c7ed04f` | `ba09593` | `392ce9a` | 0 / 48 | No | Yes | DocuReady Auditor | 2026-11-27 |
| `loop-46-indic-header-latin-body-recovery` | `a9d9b7f` | `ba09593` | `392ce9a` | 0 / 49 | No | Yes | DocuReady Auditor | 2026-11-27 |
| `loop-47-independent-mixed-script-generalization` | `23a3e09` | `ba09593` | `392ce9a` | 0 / 50 | No | Yes | DocuReady Auditor | 2026-11-27 |
| `main` | `22377d5` | `22377d5` | None | N/A (unrelated) | No | No | DocuReady Auditor | 2026-11-13 |

---

## 4. Remote-Tracking Non-PR Branches Inventory (77 refs)

| Remote Ref | HEAD | Merge Base (`origin/main`) | Behind / Ahead (`origin/main`) | Ancestor of `origin/main`? | Author | Date |
|---|---|---|---|---|---|---|
| `origin` | `392ce9a` | `392ce9a` | 0 / 0 | Yes | Akriti Lohani | 2026-11-21 |
| `origin/branding/use-provided-logo` | `c0513c8` | `c0513c8` | 149 / 0 | Yes | Deeptiman Parida | 2026-11-15 |
| `origin/docs/g0-formal-acceptance` | `75eb2ac` | `75eb2ac` | 260 / 0 | Yes | Smarak Padhi | 2026-11-15 |
| `origin/docs/g1-status-reconciliation-pr30` | `bc6c0b3` | `bc6c0b3` | 245 / 0 | Yes | Akriti Lohani | 2026-11-15 |
| `origin/docs/post-g0-acceptance-reconciliation` | `cb60eab` | `cb60eab` | 258 / 0 | Yes | Akriti Lohani | 2026-11-15 |
| `origin/docs/post-g0.1-main-status-reconciliation` | `30513bd` | `c71a7e6` | 282 / 1 | No | Akriti Lohani | 2026-11-14 |
| `origin/docs/post-g2-merge-governance-accuracy` | `6f5ea68` | `6f5ea68` | 118 / 0 | Yes | Deeptiman Parida | 2026-11-16 |
| `origin/docs/post-merge-g0-state-correction` | `b9acafa` | `b9acafa` | 294 / 0 | Yes | Smarak Padhi | 2026-11-14 |
| `origin/docs/post-merge-g1-governance-reconciliation` | `1ce4d9f` | `e32825a` | 213 / 1 | No | Smarak Padhi | 2026-11-15 |
| `origin/docs/post-merge-t0-reconciliation` | `7b32ff7` | `7b32ff7` | 262 / 0 | Yes | Smarak Padhi | 2026-11-15 |
| `origin/docs/post-merge-t2.1-t2.2-governance-reconciliation` | `a31acbd` | `a31acbd` | 149 / 0 | Yes | Deeptiman Parida | 2026-11-15 |
| `origin/docs/post-pr53-governance-reconciliation` | `9b69d54` | `9b69d54` | 154 / 0 | Yes | Akriti Lohani | 2026-11-15 |
| `origin/docs/post-pr57-governance-reconciliation` | `d38cab8` | `d38cab8` | 142 / 0 | Yes | Akriti Lohani | 2026-11-15 |
| `origin/docs/post-pr6-status-reconciliation` | `e43d92f` | `e43d92f` | 292 / 0 | Yes | Smarak Padhi | 2026-11-14 |
| `origin/docs/post-pr61-governance-readme-sync` | `58e20b9` | `58e20b9` | 136 / 0 | Yes | Deeptiman Parida | 2026-11-15 |
| `origin/docs/post-pr62-governance-cleanup` | `f085770` | `f085770` | 134 / 0 | Yes | Deeptiman Parida | 2026-11-15 |
| `origin/docs/post-pr72-pr73-final-mainline-reconciliation` | `8dc1de2` | `8dc1de2` | 113 / 0 | Yes | Deeptiman Parida | 2026-11-16 |
| `origin/docs/post-t0.3-documentation-reconciliation` | `2d6fb26` | `1fbc3b6` | 263 / 1 | No | Akriti Lohani | 2026-11-15 |
| `origin/docs/post-t1.2-status-reconciliation` | `5272668` | `5272668` | 254 / 0 | Yes | Akriti Lohani | 2026-11-15 |
| `origin/docs/post-t1.5-g1-reconciliation` | `d8d4fe0` | `d8d4fe0` | 237 / 0 | Yes | Smarak Padhi | 2026-11-15 |
| `origin/docs/readme-attribution-and-cleanup` | `14155f4` | `14155f4` | 134 / 0 | Yes | Agent 2 (T2.2) | 2026-11-15 |
| `origin/docs/readme-branding-license-modernization` | `4619178` | `4619178` | 285 / 0 | Yes | Smarak Padhi | 2026-11-14 |
| `origin/docs/t0-1-acceptance-t0-2-review-status` | `0ecf3ef` | `0ecf3ef` | 275 / 0 | Yes | Akriti Lohani | 2026-11-14 |
| `origin/docs/t0.1-acceptance-status-reconciliation` | `e08a26e` | `e08a26e` | 269 / 0 | Yes | Akriti Lohani | 2026-11-14 |
| `origin/docs/t0.1-local-regression-evidence` | `6da1150` | `6da1150` | 277 / 0 | Yes | Smarak Padhi | 2026-11-14 |
| `origin/docs/t2.2-acceptance-t2.3-kickoff` | `5534897` | `5534897` | 130 / 0 | Yes | Deeptiman Parida | 2026-11-15 |
| `origin/docs/t3.2-acceptance-evidence-wording-followup` | `320cd77` | `320cd77` | 1 / 0 | Yes | Akriti Lohani | 2026-11-21 |
| `origin/docs/t3.2-formal-acceptance-reconciliation` | `f5d8cd7` | `607f0b9` | 3 / 1 | No | Akriti Lohani | 2026-11-21 |
| `origin/docs/v2-architecture-team-ownership` | `51dee14` | `51dee14` | 307 / 0 | Yes | Smarak Padhi | 2026-11-14 |
| `origin/feat/electron-desktop-foundation` | `e400e31` | `e400e31` | 92 / 0 | Yes | Smarak Padhi | 2026-11-16 |
| `origin/feat/g1-qualification-mobile-deploy-resolution` | `b75ef85` | `b75ef85` | 216 / 0 | Yes | Akriti Lohani | 2026-11-15 |
| `origin/feat/loop5-independent-validation-and-demo` | `a9806ae` | `a9806ae` | 15 / 0 | Yes | Akriti Lohani | 2026-11-20 |
| `origin/feat/loop6-release-integrity-and-reproducibility` | `360c3fb` | `360c3fb` | 41 / 0 | Yes | DocuReady Auditor | 2026-11-19 |
| `origin/feature/g1-package-migration` | `31f2d4f` | `31f2d4f` | 313 / 0 | Yes | Smarak Padhi | 2026-11-14 |
| `origin/feature/mobile-web-mvp` | `7efebb9` | `7efebb9` | 246 / 0 | Yes | Smarak Padhi | 2026-11-15 |
| `origin/feature/prototype-decision-safety` | `f78f0e6` | `f78f0e6` | 311 / 0 | Yes | Smarak Padhi | 2026-11-14 |
| `origin/feature/prototype-ui-privacy` | `c7bcbdc` | `c7bcbdc` | 311 / 0 | Yes | Smarak Padhi | 2026-11-14 |
| `origin/fix/G0.1-post-merge-ci-hardening` | `d3684a3` | `d3684a3` | 285 / 0 | Yes | Smarak Padhi | 2026-11-14 |
| `origin/fix/T2.1-consolidated-decision-invariance` | `4733207` | `1a5fc70` | 165 / 1 | No | Deeptiman Parida | 2026-11-15 |
| `origin/fix/T2.1-contract-hardening` | `efe9ad8` | `354d4c3` | 163 / 1 | No | Deeptiman Parida | 2026-11-15 |
| `origin/fix/T2.1-evidence-provenance` | `d8663d2` | `d8663d2` | 173 / 0 | Yes | Susmita Rana | 2026-11-15 |
| `origin/fix/T2.1-mainline-outcome-repair` | `bac9f1b` | `e512e23` | 175 / 1 | No | Smarak Padhi | 2026-11-15 |
| `origin/fix/T2.1-post-merge-stabilization` | `439bfd2` | `439bfd2` | 172 / 0 | Yes | Akriti Lohani | 2026-11-15 |
| `origin/fix/T2.3-acceptance-hardening-corrections` | `5e1684b` | `5e1684b` | 126 / 0 | Yes | Agent 2 (T2.2) | 2026-11-15 |
| `origin/fix/T2.3-final-acceptance-remediation` | `04f83d2` | `04f83d2` | 124 / 0 | Yes | Deeptiman Parida | 2026-11-16 |
| `origin/fix/T2.4-classification-hardening` | `96d00fa` | `96d00fa` | 118 / 0 | Yes | Akriti Lohani | 2026-11-16 |
| `origin/fix/T2.4-post-merge-hardening` | `0ed1c74` | `0ed1c74` | 99 / 0 | Yes | Akriti Lohani | 2026-11-20 |
| `origin/fix/ci-reproducible-wheel-verification` | `9018f37` | `ac72e83` | 287 / 5 | No | Akriti Lohani | 2026-11-14 |
| `origin/fix/pyyaml-direct-dev-dependency` | `b75ef85` | `b75ef85` | 216 / 0 | Yes | Akriti Lohani | 2026-11-15 |
| `origin/fix/vercel-static-product-site` | `d419d2a` | `d419d2a` | 158 / 0 | Yes | Deeptiman Parida | 2026-11-15 |
| `origin/fix/windows-exe-startup-and-ci` | `96b6b3f` | `3e207aa` | 62 / 2 | No | Smarak Padhi | 2026-11-16 |
| `origin/fix/windows-release-qualification-post-pr81` | `70eb10e` | `70eb10e` | 5 / 0 | Yes | Akriti Lohani | 2026-11-21 |
| `origin/main` | `392ce9a` | `392ce9a` | 0 / 0 | Yes | Akriti Lohani | 2026-11-21 |
| `origin/task/G0.1-runtime-support-modernization` | `1505811` | `2907fae` | 288 / 2 | No | Smarak Padhi | 2026-11-14 |
| `origin/task/T0.1-characterise-current-behaviour` | `4678cdf` | `a6a4990` | 299 / 1 | No | Smarak Padhi | 2026-11-14 |
| `origin/task/T0.2-ci-that-exercises-ocr` | `87ada00` | `87ada00` | 277 / 0 | Yes | Akriti Lohani | 2026-11-14 |
| `origin/task/T0.2-ocr-success-proof` | `53d494b` | `53d494b` | 267 / 0 | Yes | Smarak Padhi | 2026-11-15 |
| `origin/task/T0.3-package-contract-verification` | `200eb17` | `50ccf89` | 266 / 1 | No | Akriti Lohani | 2026-11-15 |
| `origin/task/T1.1-claims-register` | `0e103fd` | `0e103fd` | 230 / 0 | Yes | Akriti Lohani | 2026-11-15 |
| `origin/task/T1.1-claims-register-corrective` | `ddec213` | `ddec213` | 246 / 0 | Yes | Smarak Padhi | 2026-11-15 |
| `origin/task/T1.2-no-network-contract` | `79ac024` | `43767d4` | 257 / 1 | No | Smarak Padhi | 2026-11-15 |
| `origin/task/T1.2-telemetry-off-no-network` | `5f2cc42` | `5f2cc42` | 258 / 0 | Yes | Akriti Lohani | 2026-11-15 |
| `origin/task/T1.3-pdf-backend-licensing` | `0919c8c` | `0919c8c` | 256 / 0 | Yes | Smarak Padhi | 2026-11-15 |
| `origin/task/T1.3-pdf-backend-licensing-corrective` | `f237b77` | `f237b77` | 246 / 0 | Yes | Smarak Padhi | 2026-11-15 |
| `origin/task/T1.4-redaction-safe-logging` | `fa966dd` | `fa966dd` | 256 / 0 | Yes | Smarak Padhi | 2026-11-15 |
| `origin/task/T1.4-redaction-safe-logging-corrective` | `d625e5e` | `d625e5e` | 246 / 0 | Yes | Smarak Padhi | 2026-11-15 |
| `origin/task/T1.5-citation-audit` | `8920519` | `8920519` | 256 / 0 | Yes | Smarak Padhi | 2026-11-15 |
| `origin/task/T1.5-citation-audit-corrective` | `602b663` | `602b663` | 246 / 0 | Yes | Smarak Padhi | 2026-11-15 |
| `origin/task/T2.1-status-vocabulary-resolver` | `2f02062` | `b5d53ab` | 169 / 2 | No | Susmita Rana | 2026-11-15 |
| `origin/task/T2.2-per-rule-test-matrix` | `5c4a504` | `5c4a504` | 168 / 0 | Yes | Susmita Rana | 2026-11-15 |
| `origin/task/T2.2-validator-fixture-matrix` | `7a04ef3` | `7a04ef3` | 155 / 0 | Yes | Agent 2 (T2.2) | 2026-11-15 |
| `origin/task/T2.3-match-grades-injected-clock` | `78a8f72` | `16b80d5` | 128 / 2 | No | Agent 2 (T2.2) | 2026-11-15 |
| `origin/task/T2.4-slot-validation` | `1067f9b` | `00b99bd` | 124 / 1 | No | Akriti Lohani | 2026-11-16 |
| `origin/task/T3.1-pack-schema-loader-lint` | `d6f9fd1` | `d6f9fd1` | 108 / 0 | Yes | Deeptiman Parida | 2026-11-16 |
| `origin/task/T3.2-primitives-generic-demo-port` | `db20885` | `db20885` | 105 / 0 | Yes | Deeptiman Parida | 2026-11-17 |
| `origin/task/T3.2.1-post-merge-safety-equivalence` | `97f98d5` | `97f98d5` | 103 / 0 | Yes | Deeptiman Parida | 2026-11-17 |
| `origin/test/T2.2-validator-matrix-assertion-hardening` | `793739c` | `793739c` | 143 / 0 | Yes | Agent 2 (T2.2) | 2026-11-15 |

---

## 5. Team Ownership & Protection Status

- **Teammate Authors Observed on `origin/*`:** Akriti Lohani, Deeptiman Parida, Smarak Padhi, Susmita Rana, Agent 2 (T2.2) — all remote-tracking commits dated **2026-11-14 to 2026-11-21**.
- **Local Research Author:** `DocuReady Auditor` — commits dated **2026-11-13** (orphan `loop-2`, `loop-3`) and **2026-11-21 to 2026-11-27** (`fix/final-desktop-release-stabilization`, `loop-01`..`loop-47`).
- **Active Dirty Teammate Worktrees:** None detected locally.
- **Protected Branches (Never Modify/Delete):** `main` (`22377d5`), `loop-10-competition-demo-reliability-and-final-readiness` (`bdc403a`), all `loop-01`..`loop-47`, `loop-2-robustness`, `loop-3-evidence-calibration`, and all `origin/*` branches.
