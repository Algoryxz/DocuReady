# LOOP 47 — CORPUS MANIFEST

All SHA-256 hashes, partition assignments (`CAL` vs `BLIND`), and cohort classifications (`REAL_CORPUS` vs `SYNTHETIC_COMPOSITED`) are recorded in `research/loop47/LOOP_47_AUDIT_RAW.json`.

## 1. Real / Corpus Cohort (`22` Documents — Strictly Separate from Synthetic)
- **CAL (`5`)**: `DOC_CTRL_01`, `DOC_EXT_06`, `DOC_HIN_01`, `DOC_MIX_01`, `DOC_MIX_02`.
- **BLIND (`17`)**: `doclaynet_001..005` (real-world DocLayNet layouts), `CHALLENGE_02_ORI_ENG_2COL`, `CHALLENGE_03_HIN_ENG_GRID`, `CHALLENGE_06_FAINT_SEAL`, `DOC_EXT_02_PENSION`, `DOC_EXT_03_DEGREE`, `DOC_EXT_04_KHATAUNI`, `DOC_EXT_05_HEALTH`, `DOC_EXT_07_DIPLOMA`, `DOC_EXT_08_LIFE_CERT`, `DOC_EXT_09_RTI`, `DOC_MULTI_01_TRISCRIPT`, `STRESS_02_STAMP`.
- **Provenance Limitation**: No newly acquired external licensed Indic-header + Latin-body real-world documents were available in this offline environment; synthetic fixtures are kept strictly separate.

## 2. Synthetic / Composited Cohort (`23` Documents — Separate Cohort)
- **Positive (`11`)**: `SYN_DEV_HDR_LAT_ID`, `SYN_ORI_HDR_LAT_ID`, `SYN_DEV_HDR_LAT_BODY`, `SYN_ORI_HDR_LAT_BODY`, `SYN_LAT_HDR_DEV_BODY`, `SYN_LAT_HDR_ORI_BODY`, `SYN_SHORT_UPPER_DEV`, `SYN_SHORT_UPPER_ORI`, `SYN47_SHALLOW_DEV_HDR`, `SYN47_SHALLOW_ORI_HDR`, `SYN47_INDIC_HDR_LAT_BODY_INDIC_TBL`.
- **Expanded Negative Controls (`12` synthetic + `2` real/corpus = `14`)**: `NEG_ENG_CIRCULAR_SEAL`, `NEG_ENG_DECORATIVE_CREST`, `NEG_ENG_UPPER_NOISE`, `NEG_ENG_DIAGONAL_MARKS`, `NEG46_BLANK_UPPER_DENSE_LATIN`, `NEG46_AMBIGUOUS_TYPOGRAPHY`, `NEG46_OFFICIAL_STAMP_AND_WATERMARK`, `NEG47_SIGNATURE_UPPER`, `NEG47_INDIC_LIKE_DECORATIVE_MARKS`, `NEG47_ENGLISH_TABLE_FORM`, `NEG47_LOW_QUALITY_BLUR_SCAN`, `NEG47_SPARSE_UPPER_TEXT`, plus `CHALLENGE_06_FAINT_SEAL` & `STRESS_02_STAMP`.
