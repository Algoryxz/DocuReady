# Loop 26 - Locked Blind Partition Protocol & Exposure Register

## Partition Isolation Protocol

The 20 Locked Blind documents (100 critical fields) were cryptographically sealed using SHA-256 hashes prior to code freezing.

## Exposure Register
- `COHORT_K_DEV_*`: EXPOSED (used for rule verification and debugging)
- `COHORT_K_CAL_*`: EXPOSED (used for threshold sweep and ECE/MCE verification)
- `COHORT_K_BLIND_*`: **LOCKED_UNEXPOSED** (evaluated strictly once at qualification)
- `COHORT_K_CHALL_*`: **LOCKED_UNEXPOSED** (evaluated strictly once at qualification)

## Blind Partition Integrity
All 20 blind document hashes match their pre-registered signatures. No blind document or field was inspected during algorithm development.
