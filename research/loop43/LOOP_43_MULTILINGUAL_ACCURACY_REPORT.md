# DOCUREADY — LOOP 43 MULTILINGUAL ACCURACY REPORT

## 1. Preserved Corpora
- **Loop 40 35-Document Corpus (`research/loop40/accuracy_results.json`):** Adaptive Micro CER `19.56%` vs Global `20.81%`; `BLIND` (`6`, `1` abstained) Micro CER `17.16%` vs Global `19.10%`.

## 2. Independent Unseen `BLIND43` Corpus (`n = 5` Distinct Documents)

| Doc ID | Bucket | Expected | Observed (`selected_lang`) | Routing | CER | WER | Latency (ms) |
|---|---|---|---|---|---:|---:|---:|
| `BLIND43_ENG_TAX` | `eng` | `FAST_PATH_ENG` | `FAST_PATH_ENG` (`eng`) | **PASS** | `0.00%` | `0.00%` | `529.65` |
| `BLIND43_HIN_AFFIDAVIT` | `hin` | `MONOLINGUAL_HIN` | `MONOLINGUAL_HIN` (`hin`) | **PASS** | `10.62%` | `36.84%` | `335.84` |
| `BLIND43_ORI_CASTE` | `ori` | `MONOLINGUAL_ORI` | `MONOLINGUAL_ORI` (`ori`) | **PASS** | `8.08%` | `38.46%` | `408.14` |
| `BLIND43_LAT_HDR_HIN_BODY` | `eng+hin` | `GLOBAL_MULTILINGUAL` | `GLOBAL_MULTILINGUAL` (`eng+hin`) | **PASS** | `12.83%` | `25.00%` | `995.56` |
| `BLIND43_IND_HDR_LAT_ID` | `eng+ori` | `GLOBAL_MULTILINGUAL` | `FAST_PATH_ENG` (`eng`) | **MISS** | `44.55%` | `61.54%` | `318.98` |

**Honest Finding:** Strategy C resolved `BLIND43_LAT_HDR_HIN_BODY`, while `BLIND43_IND_HDR_LAT_ID` (Odia header at `y < 0.25` with empty `0.52–0.85`) was missed because upper-header band `0.08–0.25` was not probed when lower-body `0.52–0.85` was blank.
