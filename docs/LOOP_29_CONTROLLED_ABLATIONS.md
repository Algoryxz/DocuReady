# Loop 29 Extended 10-Mode Ablation Study

## 1. Loop 28 Corpus Ablations (36 Packets, 92 Claims)
| Mode | Claims | Verified | Exact | False | Abstain | Precision | Coverage | Pkt False |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Mode A: Naive Baseline | 92 | 92 | 42 | 50 | 0 | **45.65%** | **100.00%** | 30 |
| Mode B: Entity Resolution Only | 92 | 89 | 42 | 47 | 3 | **47.19%** | **96.74%** | 27 |
| Mode C: Independence Detection Only | 92 | 54 | 27 | 27 | 38 | **50.00%** | **58.70%** | 27 |
| Mode D: Contradiction Detection Only | 92 | 58 | 39 | 19 | 34 | **67.24%** | **63.04%** | 13 |
| Mode E: Conservative Abstention Only | 92 | 53 | 30 | 23 | 39 | **56.60%** | **57.61%** | 23 |
| Mode F: Full Policy (Production) | 92 | 42 | 42 | 0 | 50 | **100.00%** | **45.65%** | 0 |
| Mode G: LOO-Entity | 92 | 39 | 39 | 0 | 53 | **100.00%** | **42.39%** | 0 |
| Mode H: LOO-Duplicate | 92 | 42 | 42 | 0 | 50 | **100.00%** | **45.65%** | 0 |
| Mode I: LOO-Contradiction | 92 | 77 | 42 | 35 | 15 | **54.55%** | **83.70%** | 19 |
| Mode J: LOO-Missing | 92 | 47 | 42 | 5 | 45 | **89.36%** | **51.09%** | 5 |
