# DOCUREADY — LOOP 42 MULTILINGUAL BLIND ACCURACY REPORT

## 1. Preserved 35-Document Corpus (`research/loop40/accuracy_results.json`)

- **Overall (`35`, `1` abstained):** Adaptive Micro CER `19.56%` vs Global `20.81%`; Adaptive Micro WER `32.43%` vs Global `33.74%`.
- **BLIND (`6`, `1` abstained):** Adaptive Micro CER `17.16%` vs Global `19.10%`.

## 2. Independent Unseen Synthetic Blind Corpus (`BLIND42`, `n = 5` Distinct Documents)

Rendered independently (not transformed copies of Loop 14/18 fixtures) using Windows `arial.ttf` and `Nirmala.ttc`:

| Doc ID | Bucket | Strategy | Selected Lang | CER | WER | Latency (ms) |
|---|---|---|---|---:|---:|---:|
| `BLIND42_ENG_RECEIPT` | `eng` | `FAST_PATH_ENG` | `eng` | `0.00%` | `0.00%` | `534.00` |
| `BLIND42_HIN_FORM` | `hin` | `MONOLINGUAL_HIN` | `hin` | `7.55%` | `29.41%` | `453.63` |
| `BLIND42_ORI_NOTICE` | `ori` | `MONOLINGUAL_ORI` | `ori` | `2.38%` | `8.33%` | `427.81` |
| `BLIND42_MIX_HIN_ENG` | `eng+hin` | `FAST_PATH_ENG` | `eng` | `9.01%` | `13.33%` | `339.29` |
| `BLIND42_MIX_ORI_ENG` | `eng+ori` | `FAST_PATH_ENG` | `eng` | `9.43%` | `14.29%` | `304.11` |

**Observation:** On `BLIND42_MIX_HIN_ENG` and `BLIND42_MIX_ORI_ENG`, the `0.25–0.45` vertical strip had majority Latin tokens, routing to `FAST_PATH_ENG` (`9.01%` / `9.43%` CER because Indic tokens were misread by `eng`). Documented honestly; routing thresholds were not tuned on `BLIND42`.
