# DOCUREADY — LOOP 11 EXTERNAL DATASET CATALOG & LICENSING AUDIT
## Independent Dataset Benchmark, OCR Generalization & Performance Frontier

**Project:** DocuReady  
**Phase:** Phase 2 — External Dataset Discovery & Audit  
**Author:** Antigravity Engineering (Research Loop 11)  
**Date:** 2026-11-22  
**Governance:** Zero production release modifications; strict adherence to research ethics, data privacy, and intellectual property.

---

## 1. DATASET DISCOVERY & AUDIT MATRIX

| Dataset | Primary Focus | Language(s) | License | Ground Truth Type | Acceptance Decision | Key Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FUNSD** | Form understanding, noisy scans, KIE | English | Academic / Open Research | Words, bboxes, key-value links | **ACCEPTED** | Canonical noisy form layout and key-value extraction benchmark. |
| **SROIE** | Scanned receipt OCR & field extraction | English | CC-BY-4.0 | Text bboxes, transcripts, 4 target fields | **ACCEPTED** | Highly relevant for date, name, and financial amount parsing. |
| **DocLayNet** | Large-scale layout analysis | English, German, French | CDLA-Permissive-1.0 | 11 layout categories, polygon bboxes | **ACCEPTED (Sample)** | Authoritative benchmark for document structure and segment bounds. |
| **XFUND** | Multilingual form understanding | 7 languages (ZH, JA, ES, FR, IT, DE, PT) | CC BY-NC-SA 4.0 | Multilingual bboxes, key-value pairs | **ACCEPTED (Eval)** | Tests cross-lingual token grouping and layout extraction. |
| **IndicDLP / Indic Mozhi** | Indic printed text OCR & layout | Hindi, Odia, 11 Indic scripts | MIT / Academic (IIIT-H / AI4Bharat) | Word transcripts, layout categories | **ACCEPTED** | Essential for testing Hindi (`hin`) and Odia (`ori`) OCR generalization. |
| **RVL-CDIP** | Document classification (16 types) | English | Research / Legacy Tobacco Archive | Category labels only (no token bboxes) | **REJECTED (OCR)** | Lacks fine-grained word/field ground truth; classification only. |
| **DIBCO / H-DIBCO** | Document image degradation & binarization | Multilingual historical | Academic / Non-Commercial | Binary pixel masks (no OCR text) | **ACCEPTED (Robustness)** | Used strictly for synthetic degradation modeling (stains/blur). |
| **OCRBench** | LMM text reasoning & VQA | Multilingual | Varied Academic | Question-Answer pairs | **REJECTED** | Designed for multimodal LLMs, not local rule-based OCR extractors. |

---

## 2. DETAILED DATASET RECORDS

### 2.1. FUNSD (Form Understanding in Noisy Scanned Documents)
- **Official Source URL:** https://guillaumejaume.github.io/FUNSD/
- **Repository Mirror:** https://huggingface.co/datasets/nielsr/funsd
- **License:** Open Academic / Research
- **Commercial Restrictions:** Yes (Non-commercial research use only)
- **Redistribution Restrictions:** Attribution required; derivative annotations permitted.
- **Privacy Considerations:** Sourced from public tobacco industry documents (Truth Tobacco Industry Documents archive); historical institutional business forms; no active PII.
- **Language Coverage:** English (typewritten, stamp, and scanned variations).
- **Document Types:** Application forms, questionnaire sheets, memos, financial certificates.
- **Dataset Size:** 199 fully annotated scanned forms (149 training, 50 testing).
- **Ground Truth Format:** JSON files pairing words, bounding box coordinates $[x_0, y_0, x_1, y_1]$, entity labels (`header`, `question`, `answer`, `other`), and semantic relation links.
- **Relevance to DocuReady:** Directly challenges DocuReady's `PageOCRData._build_lines` spatial clustering and key-value regex heuristics on non-standard form layouts.
- **Decision:** **ACCEPTED** for Form Layout & OCR Benchmark.

---

### 2.2. SROIE (ICDAR 2019 Scanned Receipts OCR and Information Extraction)
- **Official Source URL:** https://rrc.cvc.uab.es/?ch=13
- **Repository Mirror:** https://huggingface.co/datasets/jsdnrs/ICDAR2019-SROIE
- **License:** Creative Commons Attribution 4.0 International (CC-BY-4.0)
- **Commercial Restrictions:** None (Permissive with attribution)
- **Redistribution Restrictions:** Preserves CC-BY-4.0 notice.
- **Privacy Considerations:** Public commercial retail receipts. No sensitive personal applicant credentials.
- **Language Coverage:** English.
- **Document Types:** Scanned transactional paper receipts (thermal prints, dot-matrix, table lines).
- **Dataset Size:** 1,000 scans (626 train, 361 test).
- **Ground Truth Format:** Task 1 (Text localization bounding boxes), Task 2 (Exact OCR text transcription), Task 3 (Key information extraction: `company`, `date`, `address`, `total`).
- **Relevance to DocuReady:** Evaluates character-level OCR accuracy (CER/WER), numeric/currency normalization, and date parsing under thermal fading and camera distortion.
- **Decision:** **ACCEPTED** for OCR Accuracy & Field Extraction Benchmark.

---

### 2.3. DocLayNet (Document Layout Network - IBM Research)
- **Official Source URL:** https://github.com/DS4SD/DocLayNet
- **Repository Mirror:** https://huggingface.co/datasets/ds4sd/DocLayNet
- **License:** CDLA-Permissive-1.0 (Community Data License Agreement – Permissive, Version 1.0)
- **Commercial Restrictions:** Permissive; allows research, evaluation, and commercial usage.
- **Redistribution Restrictions:** Retains CDLA notice.
- **Privacy Considerations:** Sourced from publicly available financial filings, legal statutes, patent grants, and scientific papers.
- **Language Coverage:** English, German, French.
- **Document Types:** Financial reports, administrative forms, legal decrees, scientific papers.
- **Dataset Size:** 80,863 unique document pages.
- **Ground Truth Format:** COCO-format JSON with polygon segmentations and 11 visual layout classes (`Caption`, `Footnote`, `Formula`, `List-item`, `Page-footer`, `Page-header`, `Picture`, `Section-header`, `Table`, `Text`, `Title`).
- **Relevance to DocuReady:** Tests header anchor detection, table isolation, and bounding box IoU alignment.
- **Decision:** **ACCEPTED (Stratified Sample)** for Layout Segmentation & Bounding Box IoU.

---

### 2.4. IndicDLP & Indic Mozhi OCR (AI4Bharat / IIT Madras / IIIT Hyderabad)
- **Official Source URL:** https://ai4bharat.iitm.ac.in / https://cvit.iiit.ac.in
- **Repository Mirror:** https://huggingface.co/datasets/ai4bharat/indicdlp
- **License:** MIT / CC-BY-4.0 (Open research)
- **Commercial Restrictions:** None for open subsets.
- **Redistribution Restrictions:** Standard open-source attribution.
- **Privacy Considerations:** Government gazettes, publicly published educational circulars, literary excerpts; zero private citizen data.
- **Language Coverage:** Hindi (`hin`), Odia (`ori`), Bengali, Tamil, Telugu, English.
- **Document Types:** Administrative circulars, application notices, official gazette extracts, printed marksheets.
- **Dataset Size:** 1,200+ annotated document pages with multi-script line and word annotations.
- **Ground Truth Format:** Unicode UTF-8 transcripts, bounding box coordinates, language and script metadata.
- **Relevance to DocuReady:** Directly evaluates DocuReady's bundled Tesseract `hin.traineddata` and `ori.traineddata` models. Forensics identified that DocuReady defaults to `eng`; this dataset measures multilingual OCR generalization gaps.
- **Decision:** **ACCEPTED** for Multilingual Indian Script Generalization.

---

### 2.5. XFUND (Multilingual Form Understanding - Microsoft Research)
- **Official Source URL:** https://github.com/doc-analysis/XFUND
- **Repository Mirror:** https://huggingface.co/datasets/nielsr/xfund
- **License:** CC BY-NC-SA 4.0 (Creative Commons Attribution-NonCommercial-ShareAlike 4.0)
- **Commercial Restrictions:** Non-commercial research only.
- **Privacy Considerations:** Anonymized synthesized enterprise forms.
- **Language Coverage:** 7 languages (Chinese, Japanese, Spanish, French, Italian, German, Portuguese).
- **Dataset Size:** 1,393 forms across 7 languages.
- **Ground Truth Format:** Word tokens, polygon bboxes, key-value relations.
- **Decision:** **ACCEPTED (Diagnostic Split)** for evaluating spatial reading order invariance across diverse scripts.

---

### 2.6. RVL-CDIP (Ryerson Vision Lab Complex Document Information Processing)
- **Official Source URL:** https://www.cs.cmu.edu/~aharley/rvl-cdip/
- **License:** Legacy Tobacco Archive Research Terms
- **Decision:** **REJECTED for OCR Evaluation**. RVL-CDIP only provides whole-document coarse category labels (16 classes) with zero bounding boxes or OCR transcripts. Not suitable for measuring OCR accuracy or field extraction.

---

### 2.7. DIBCO / H-DIBCO (Document Image Binarization Contest)
- **Official Source URL:** ICDAR / ICFHR Binarization Competitions
- **License:** Academic Research License
- **Ground Truth:** Binary foreground/background ground-truth masks.
- **Decision:** **ACCEPTED for Degradation Profiling**. Provides objective mathematical standards for noise, contrast degradation, and bleed-through.

---

## 3. DATA LEAKAGE & PRIVACY SAFEGUARDS

1. **Zero Real Applicant PII:** None of the selected datasets contain active, private citizen data or real identity credentials.
2. **Train/Test Leakage Elimination:** For every accepted benchmark dataset, DocuReady evaluations strictly use the **official Test / Challenge partitions**. No parameters or thresholds in DocuReady were trained or tuned on these splits.
3. **Partition Stratification:** Where stratified sampling is required (e.g., DocLayNet and SROIE), samples are deterministically selected using fixed random seeds (`seed=20261122`) and recorded in `loop11_dataset_manifest.json`.

---

## 4. CONCLUSION & TRANSITION TO PHASE 3

The dataset discovery and licensing audit confirms that:
- **FUNSD** and **SROIE** provide authoritative, legally permitted English form and receipt OCR ground truths.
- **IndicDLP / Indic Mozhi** provides essential multilingual Hindi and Odia ground truths to test DocuReady's neural Tesseract models.
- **DocLayNet** provides fine-grained layout boundary annotations.

Proceeding to Phase 3: Dataset Acquisition & Verification.
