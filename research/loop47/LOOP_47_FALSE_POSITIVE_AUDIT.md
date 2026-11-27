# LOOP 47 — FALSE-POSITIVE & NEGATIVE-CONTROL AUDIT

Evaluated `14` negative controls (`12` synthetic + `2` real/corpus) against Strategy C unchanged (`research/loop47/LOOP_47_AUDIT_RAW.json`):
- **English-Only False Multilingual Routing**: **0 / 14 (0.00%)**
- **Devanagari False-Positive Triggers**: **0 / 14 (0.00%)**
- **Odia False-Positive Triggers**: **0 / 14 (0.00%)**

All negative controls — including `NEG47_SIGNATURE_UPPER`, `NEG47_INDIC_LIKE_DECORATIVE_MARKS` (horizontal shirorekha-like bar + arcs), `NEG47_ENGLISH_TABLE_FORM`, `NEG47_LOW_QUALITY_BLUR_SCAN`, `NEG47_SPARSE_UPPER_TEXT`, `NEG46_BLANK_UPPER_DENSE_LATIN`, `NEG_ENG_CIRCULAR_SEAL`, `NEG_ENG_DECORATIVE_CREST`, `NEG_ENG_UPPER_NOISE`, `NEG_ENG_DIAGONAL_MARKS`, `CHALLENGE_06_FAINT_SEAL`, and `STRESS_02_STAMP` — routed to `FAST_PATH_ENG` (`eng`).
