# DOCUREADY LOOP 27 — INDEPENDENT PUBLIC VALIDATION
## Evaluation on Cohort L (45 Unseen Public Documents, 120 Critical Fields)

---

### 1. Cohort L Partition Performance
Cohort L was assembled strictly from previously unused raw documents in FUNSD, SROIE, Indic OCR, and DocLayNet datasets.

| Partition Split | Documents | Critical Fields | Verified Claims | Exact Matches | False Verifications | Precision | Coverage | Mean Overhead |
|---|---|---|---|---|---|---|---|---|
| `Cohort_L_DEV` | 10 | 30 | 6 | 6 | 0 | 100.0% | 20.0% | 1.61 ms |
| `Cohort_L_CAL` | 10 | 30 | 7 | 7 | 0 | 100.0% | 23.3% | 2.21 ms |
| `Cohort_L_BLIND` | 10 | 30 | 7 | 7 | 0 | 100.0% | 23.3% | 2.77 ms |
| `Cohort_L_CHALL` | 10 | 30 | 0 | 0 | 0 | 100.0% | 0.0% | 2.99 ms |
