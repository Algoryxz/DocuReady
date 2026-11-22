# LOOP 17: Agentic Skills Research & Selection Report

## 1. Catalog Inspection & Background

As part of the mandatory engineering discipline for Loop 17, we reviewed the **Agentic Awesome Skills (AAS)** repository ([github.com/sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills)), an independent catalog comprising 3,055+ installable `SKILL.md` skill definitions for agentic coding environments.

Per governance guidelines:
- We do not install the entire library indiscriminately.
- We review candidate skills against the specific mission of Loop 17: **Adaptive OCR efficiency, latency reduction, critical-field reliability, and independent verification**.
- We inspect skill provenance, system dependencies, safety risks, and operational impact.
- No third-party execution hooks or arbitrary scripts are executed.

---

## 2. Candidate Skills Considered

| Candidate Category | Candidate Skill / Domain | Evaluation & Relevance to Loop 17 | Selection Status |
|---|---|---|---|
| **Minimalist Engineering** | `ponytail` | Enforces YAGNI, standard library first, reuse of existing code, shortest diffs, and prevents speculative abstractions. | **SELECTED (MANDATORY)** |
| **Software Architecture** | `a-philosophy-of-software-design` | Deep modules, hiding complexity behind clean interfaces, reducing cognitive load. | **SELECTED** |
| **Code Structure & Safety** | `refactoring` | Martin Fowler-inspired rules for structural improvement while strictly preserving observable behavior. | **SELECTED** |
| **Performance Profiling** | `cProfile` / stdlib `time.perf_counter` / `tracemalloc` | Native Python standard library tools for sub-millisecond per-stage timing and heap tracing. | **SELECTED (Stdlib First)** |
| **Platform Profiling** | `android-profiler` / `metrickit` | Mobile/OS-specific profilers for Android ART or iOS Darwin. Irrelevant to Windows x64 Python engine. | **REJECTED** |
| **Frontend/UI Design** | `generative_ui` / `mcp-app-development` | MCP interactive widget rendering. Unnecessary for backend OCR engine optimization. | **REJECTED** |
| **Cloud/External APIs** | Cloud vision / LLM wrapper skills | Violates offline-first, local-only requirement for HackNation 2026. | **REJECTED** |

---

## 3. Selected Skills: Deep Review & Governance

### 3.1. Skill 1: `ponytail` (Minimalist Engineering Discipline)
- **Source Path:** `C:\Users\smara\.gemini\config\plugins\ponytail\skills\ponytail\SKILL.md`
- **License:** MIT
- **Operational Principle:**
  1. *Does this need to exist at all?* If speculative $\to$ omit.
  2. *Already in this codebase?* Reuse existing functions and classes in `docuready.ingest.*`.
  3. *Standard library does it?* Use `time.perf_counter`, `tracemalloc`, `dataclasses`, `re`, `unicodedata`.
  4. *Shortest working diff wins.* Do not rewrite working modules merely for aesthetic reasons.
- **Safety Review:** Verified safe. Contains prompt instructions and coding rules; does not execute background daemons or network requests.
- **Impact on Loop 17:** Prevents introducing complex multi-threading pools, speculative C-extensions, or unnecessary intermediate wrapper classes for profiling.

### 3.2. Skill 2: `a-philosophy-of-software-design`
- **Source Path:** `C:\Users\smara\.gemini\config\skills\a-philosophy-of-software-design\SKILL.md`
- **Operational Principle:**
  - Create *deep modules*: simple interfaces that conceal complex, optimized implementations.
  - The adaptive OCR selector interface (`execute_adaptive_ocr`) should remain lean and intuitive for caller code while encapsulating profiling, strategy routing, and fallback logic internally.
- **Impact on Loop 17:** Ensures that optimizations to `adaptive_ocr.py` do not leak internal heuristic thresholds or intermediate timing buffers into public API callers.

### 3.3. Skill 3: `refactoring`
- **Source Path:** `C:\Users\smara\.gemini\config\skills\refactoring\SKILL.md`
- **Operational Principle:**
  - Decompose large functions into cohesive sub-routines.
  - Preserve observable behavior and verify with automated regression tests before and after restructuring.
- **Impact on Loop 17:** Governs the refactoring of `profile_document()` and `execute_adaptive_ocr()` to separate thumbnail generation, layout projection, and OCR dispatch into clean, profile-measured stages.

---

## 4. Rejection Justification

1. **Third-Party OCR Frameworks (e.g. EasyOCR, PaddleOCR wrappers):**
   - Adding new heavy PyTorch/ONNX dependencies would violate the zero-external-dependency rule and balloon memory consumption beyond the desktop target constraint (< 500 MB RAM).
2. **Mobile / Platform Profilers:**
   - Tools tailored to Android or iOS cannot measure Windows x64 process IPC or native C-library calls in Tesseract.

---

## 5. Conclusion

By strictly adhering to `ponytail`, `a-philosophy-of-software-design`, and standard library profiling, Loop 17 will achieve its latency reduction and reliability goals through targeted algorithmic optimizations rather than toolchain sprawl.
