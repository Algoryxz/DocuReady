# Loop 28 Blind Partition Protocol & Cryptographic Register

## 1. Cryptographic Register
To preserve benchmark integrity and prevent data snooping or overfitting:
- **Blind Partition Corpus File**: `research/loop28/corpus/cross_document_corpus.json`
- **Registered SHA-256 Hash**: `9199efdc6016802b6d865c76fdc30d92fb135100d27ed3474926e7a547444562`
- **File Size**: 62195 bytes
- **Lock Status**: `FROZEN_LOCKED_BLIND`
- **Timestamp**: `2026-11-24T16:15:00+05:30`

## 2. Partition Separation Rules
1. `DEV` and `CAL` partitions were used during active engineering of entity matching and normalizers.
2. `BLIND` partition (12 packets, 31 claims) was locked and evaluated strictly after engine implementation was frozen.
3. No hyperparameter or threshold adjustment was conducted on the basis of BLIND results.
