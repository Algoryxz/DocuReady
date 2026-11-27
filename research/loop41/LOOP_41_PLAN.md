# DOCUREADY — LOOP 41 INVESTIGATION & QUALIFICATION PLAN

**Mission:** Qualify in-process OCR reliability, reconcile historical benchmark baselines, expand multilingual blind evaluation, make a rigorous Package A/B decision, audit Windows release trust, and complete Gates A–Z.  
**Branch:** `loop-41-inprocess-ocr-reliability-and-release-qualification` (from `b487f03`)  
**Protected Release:** Loop 10 (`bdc403a`) — immutable, verified 5/5 bit-exact.

---

## 1. Agent Ownership & Orchestration

| Role | Scope | Primary Deliverables |
|---|---|---|
| **Agent A — In-Process OCR Reliability** | `_InProcessScriptProbe` DLL discovery, `TessBaseAPI` lifecycle, `threading.Lock()`, `atexit`, concurrency stress, memory/handle stability, fallback parity, malformed input safety | `LOOP_41_INPROCESS_OCR_AUDIT.md`, `LOOP_41_CONCURRENCY_REPORT.md`, `LOOP_41_RESOURCE_LIFECYCLE_REPORT.md`, `LOOP_41_FALLBACK_PARITY_REPORT.md` |
| **Agent B — Benchmark Forensics** | Reconcile Loop 17, 18, 39 (two measurement sets), and 40 artifacts; run cold fresh-process vs warm steady-state, packet, multilingual, native vs fallback benchmarks | `LOOP_41_BENCHMARK_FORENSICS.md` |
| **Agent C — Multilingual Accuracy** | Frozen `DEV` / `CALIBRATION` / `BLIND` splits across `eng`, `hin`, `ori`, `eng+hin`, `eng+ori`; CER, WER, field exact/normalized match, table-cell accuracy, abstention, latency, routing | `LOOP_41_MULTILINGUAL_ACCURACY_REPORT.md` |
| **Agent D — Windows & Package Qualification** | Package A vs Variant B startup/runtime/utility audit, Authenticode signing, SmartScreen, clean-machine blocker verification | `LOOP_41_PACKAGE_AB_DECISION.md`, `LOOP_41_WINDOWS_TRUST_REPORT.md` |
| **Integration Agent** | Cross-audit reconciliation, security/privacy checks, full regression suite, Gates A–Z matrix, failure analysis, learnings, final closeout | `LOOP_41_SECURITY_PRIVACY_REPORT.md`, `LOOP_41_TEST_REPORT.md`, `LOOP_41_QUALIFICATION_MATRIX.md`, `LOOP_41_FAILURE_ANALYSIS.md`, `LOOP_41_LEARNINGS.md`, `LOOP_41_FINAL_REPORT.md` |

---

## 2. Adversarial Design Challenge (`/grill-me`)

1. **Thread safety:** Does `threading.Lock()` protect shared `TessBaseAPI` handles across languages, or can language-model switching or pointer reuse corrupt state?
2. **Fallback equivalence:** Does falling back from `_InProcessScriptProbe` to `pytesseract` subprocess produce identical script classification, CER/WER, word count, and `probe_uncertain` semantics?
3. **Benchmark comparability:** Are Loop 40's `142.00 ms` (Loop 17) and `159.95 ms` (Loop 18) warm in-process numbers comparable to Loop 39's fresh-process subprocess numbers?
4. **Work hiding:** Does the tighter central strip (`350 px`, `0.25–0.45` height) hide work or miss script signals on real documents?
5. **Package minimization:** Is Variant B's `63.40 MiB` reduction justified given `n=10` paired CI variance?
6. **Windows blockers:** Are unsigned binaries and lack of a clean VM reported honestly as `BLOCKED`?
