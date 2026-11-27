# LOOP 21: Ponytail Review & Architectural Simplicity Audit

## 1. Governance & Discipline

In accordance with the canonical `skills/ponytail/SKILL.md` directive, Loop 21 operates under strict Ponytail discipline:
- **Default Intensity**: Full.
- **Guiding Rule**: "The best code is the code never written. A lazy senior developer reaches for the standard library before custom code, native platform features before dependencies, one line before fifty, and fixes root causes rather than symptoms."
- **The Ladder of Simplicity**:
  1. *Does this need to exist at all?* (YAGNI)
  2. *Already in this codebase?* Reuse existing row clustering, interval projection, and `FieldEvidence` structures.
  3. *Stdlib does it?* Use Python's built-in `re`, `math`, `unicodedata`, and `dataclasses`.
  4. *Native platform feature covers it?* OS-level image decoding and process execution.
  5. *Already-installed dependency solves it?* Use `numpy` and `PIL` (already present). Zero new packages.
  6. *Can it be one line?* Write one line.
  7. *Only then:* the minimum working code.

---

## 2. Complexity Avoidance in Loop 21

| Proposed Feature / Temptation | Ponytail Verdict | Reason & Minimal Alternative |
| :--- | :---: | :--- |
| **Deep Learning Multi-Tier Table Parser (e.g. Table-Transformer / TATR / PubTables)** | **REJECTED** | Massive weights (>300MB), GPU requirements, non-deterministic inference, breaks competition freeze. Multi-tier headers are handled by detecting multi-column spans in row 0 and concatenating parent/child header text in <25 lines of pure Python. |
| **Global Page-Wide 3x Upscaling** | **REJECTED** | Tripling whole-page dimensions ($3000 \times 2700$) increases OCR latency by $400\%\text{–}600\%$ (exceeding 2.5 seconds per page) and balloons memory. Minimal alternative: targeted 2x bicubic pre-scaling strictly on numeric crops or low-resolution bounding boxes. |
| **Speculative Heuristic Decimal Injector** | **REJECTED** | Hardcoding regexes to insert decimal points into integers (e.g. turning `56` into `5.6`) corrupts genuine integers like `56 units` or `₹56`. Decimal points must only be recognized from actual visual evidence. |
| **New Image Filtering / Morphological Engine** | **REJECTED** | Standard Pillow `ImageResampling.BICUBIC` and contrast enhancement provide clean raster interpolation without custom C-extensions. |

---

## 3. Deliberate Shortcuts & Constraints (`ponytail:` ledger)

- `ponytail: multi-tier header fusion handles up to 2 header tiers (parent super-header and child column headers); tables with >= 3 tiers route to human review.`
- `ponytail: targeted bicubic pre-scaling applied selectively to tokens with height < 20px containing digits to preserve low latency on standard high-DPI scans.`
- `ponytail: parent-child header concatenation uses simple forward slash syntax ('Parent / Child') preserving standard string searchability.`

---

## 4. Verification Check

A single clean, highly targeted test suite `tests/test_loop21_header_and_decimal.py` verifies:
- Multi-tier header fusion and exact data row indexing.
- Decimal retention (`5.6` preserved without dropping point).
- Prevention of integer corruption (integers like `56` do not gain decimal points).
- Preservation of bit-exact Loop 10 binaries and zero regression on existing suites.
