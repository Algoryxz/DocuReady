# Loop 28 Generalization Results Across Partitions

## 1. Partition Breakdown
| Partition | Packets | Claims | Verified | Exact Matches | False Verifications | Abstentions | Precision (95% CI) | Coverage (95% CI) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DEV** | 10 | 27 | 14 | 14 | 0 | 13 | **100.00%** [78.47-100.0] | **51.85%** [33.99-69.26] |
| **CAL** | 8 | 23 | 13 | 13 | 0 | 10 | **100.00%** [77.19-100.0] | **56.52%** [36.81-74.37] |
| **BLIND** | 12 | 31 | 14 | 14 | 0 | 17 | **100.00%** [78.47-100.0] | **45.16%** [29.16-62.23] |
| **CHALL** | 6 | 11 | 1 | 1 | 0 | 10 | **100.00%** [20.65-100.0] | **9.09%** [1.62-37.74] |
| **AGGREGATE** | **36** | **92** | **42** | **42** | **0** | **50** | **100.00%** [91.62-100.0] | **45.65%** [35.85-55.8] |

## 2. Key Findings
- **Zero False Verifications**: Across all partitions, including the locked BLIND and adversarial CHALL cohorts, exactly **0 false verifications** occurred.
- **100.00% Observed Precision**: 42 verified claims yielded 42 exact ground truth matches.
- **Conservative Abstention Behavior**: Under adversarial and contradictory conditions (CHALL), coverage appropriately contracted to 9.09% while preserving 100% precision.
