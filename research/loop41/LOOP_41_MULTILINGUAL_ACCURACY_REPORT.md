# DOCUREADY — LOOP 41 MULTILINGUAL ACCURACY REPORT

## 1. Frozen 35-Document Corpus (`DEV=10`, `CALIBRATION=19`, `BLIND=6`)

From `research/loop40/accuracy_results.json` (unchanged routing in `select_ocr_strategy()`):
- **Overall (`35`, `1` abstained):** Adaptive Micro CER **`19.56%`** vs Global `20.81%`; Adaptive Micro WER **`32.43%`** vs Global `33.74%`.
- **BLIND (`6`, `1` abstained):** Adaptive Micro CER **`17.16%`** vs Global `19.10%`; Adaptive Micro WER **`26.63%`** vs Global `30.34%`.
- **Eng+Ori (`DOC_MIX_02_ORI_ENG_SCHOLARSHIP`):** CER **`6.35%`**, WER **`17.39%`**.

## 2. Loop 41 Perturbed Blind Stress Evaluation (`BLIND41`, 1.5° Rotation, `n = 5`)

| Doc ID | Bucket | Strategy | Selected Lang | CER | WER | Latency (ms) |
|---|---|---|---|---:|---:|---:|
| `BLIND41_ENG` | `eng` | `FAST_PATH_ENG` | `eng` | `2.28%` | `1.69%` | `1,725.23` |
| `BLIND41_ORI` | `ori` | `GLOBAL_MULTILINGUAL` | `eng+hin+ori` | `7.53%` | `14.66%` | `4,186.64` |
| `BLIND41_HIN` | `hin` | `MONOLINGUAL_HIN` | `hin` | `13.88%` | `43.84%` | `2,356.47` |
| `BLIND41_MIX_HIN` | `eng+hin` | `GLOBAL_MULTILINGUAL` | `eng+hin` | `9.14%` | `20.75%` | `2,637.10` |
| `BLIND41_MIX_ORI` | `eng+ori` | `GLOBAL_MULTILINGUAL` | `eng+hin+ori` | `5.69%` | `15.22%` | `3,942.06` |

- Routing remained deterministic across all 5 language buckets under unseen rotation perturbation.
- No language was silently dropped; `eng+ori` and mixed Odia routed to `eng+hin+ori`.
