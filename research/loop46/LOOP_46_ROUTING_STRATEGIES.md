# LOOP 46 — ROUTING STRATEGIES EVALUATION (A–E)

Evaluated 5 conditional upper-band strategies on the frozen `7`-document Calibration (`CAL`) cohort + L17 (`DOC_CTRL_01`) warm latency (`n=10`) before editing `adaptive_ocr.py` (`research/loop46/LOOP_46_REPRO_AND_ABLATION.json`):

| Strategy | Description | CAL Pass | L17 Warm Mean (ms) | L17 Max (ms) | Selected? |
|---|---|---:|---:|---:|---|
| **A** | Loop 45 Strategy D unchanged (probe upper only if lower empty) | `5 / 7` | 496.36 | 885.81 | No (misses Indic hdr + Latin body) |
| **B** | Probe upper when central is `LATIN` and lower is `LATIN` or empty | `7 / 7` | 758.69 | 910.61 | Equivalent to C when upper has ink |
| **C** | **Probe upper when central & lower are `LATIN` (or empty) AND `upper_ink >= 0.003` (`>= 6` Indic, `500 px`)** | **`7 / 7`** | **794.58** | **869.06** | **SELECTED** |
| **D** | Probe upper only on conflict or `< 15` chars in lower | `5 / 7` | 791.66 | 877.74 | No (misses dense Latin body) |
| **E** | Unconditional 3-band probe when central is `LATIN` | `7 / 7` | 833.56 | 1052.63 | No (exceeds budget risk) |

**Selection Rationale**: Strategy C achieves `7 / 7` CAL recall, skips blank upper bands (`ink < 0.003`) in `< 1 ms`, preserves the `500 px` Odia header requirement and `>= 6` Indic false-positive guard, and stays within the `< 850 ms` L17 `profile_document()` budget.
