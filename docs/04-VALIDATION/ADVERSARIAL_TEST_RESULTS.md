# DocuReady Adversarial Testing & Robustness Report

This document reports the methodology, execution traces, and outcomes for the 13 adversarial test cases executed against DocuReady in [`docuready-mvp/tests/test_adversarial.py`](file:///c:/Users/smara/Desktop/New%20folder/docuready-mvp/tests/test_adversarial.py).

---

## 1. Summary of Adversarial Test Suite

```
Test Script: docuready-mvp/tests/test_adversarial.py
Test Count: 13 Edge-Case / Adversarial Scenarios
Execution Result: 13 PASSED, 0 FAILED (0.74s)
```

---

## 2. Detailed Scenario Analysis

### 1. Similar But Different Names (`test_similar_but_different_names`)
- **Input:** "Smruti Ranjan Nayak" vs "Smruti Ranjan Rout"; "Smruti Nayak" vs "Smita Nayak".
- **Challenge:** Both pairs share significant lexical similarity (same first name or single letter difference).
- **Engine Behavior:** Normalized edit distance detects that the surname/given name is a distinct person rather than a minor typo ($sim < 0.82$).
- **Status:** **PASS** (Correctly categorized as `FAIL` or `REVIEW` depending on severity; prevents improper identity conflation).

### 2. Initials Versus Full Names (`test_initials_versus_full_names`)
- **Input:** "S R Nayak" on Bank Passbook vs "Smruti Ranjan Nayak" on Application Form.
- **Challenge:** Passbooks frequently use single-letter initials for given and middle names.
- **Engine Behavior:** Initials expansion heuristic matches token lengths and initial characters.
- **Status:** **PASS** (Yields `REVIEW` with an advisory self-declaration checklist; never rejects).

### 3. Date Ambiguity (`test_dd_mm_ambiguity`)
- **Input:** Application Form states `04/05/2003`; Marksheet states `05/04/2003`.
- **Challenge:** Both day $\le 12$ and month $\le 12$. Neither can be conclusively proven to be DD/MM vs MM/DD without explicit locale guidance.
- **Engine Behavior:** Triggers `RULE-DOB-02` with status `REVIEW`.
- **Status:** **PASS** (Alerts applicant to confirm whether day precedes month before submission).

### 4. Missing Fields (`test_missing_mandatory_fields`)
- **Input:** Income Certificate PDF with blank or omitted annual family income.
- **Challenge:** Missing data must not throw unhandled null pointer or dictionary key errors.
- **Engine Behavior:** Triggers `RULE-FLD-01` flagging missing mandatory field `ANNUAL_INCOME` with status `FAIL` and targeted remediation.
- **Status:** **PASS**.

### 5. Contradictory Values (`test_contradictory_values`)
- **Input:** Application Form DOB `14/05/2003`; Marksheet DOB `14/05/2006`.
- **Challenge:** Year mismatch represents a three-year age discrepancy.
- **Engine Behavior:** Triggers `RULE-DOB-01` with status `FAIL` (Critical penalty -25 pts).
- **Status:** **PASS**.

### 6. Invalid / Corrupted PDF Files (`test_invalid_pdf_files`)
- **Input:** Binary stream with header `NOT_A_REAL_PDF_HEADER\x00\x01\x02...` or truncated byte payloads.
- **Challenge:** Malformed streams can cause parser crashes or segfaults.
- **Engine Behavior:** Pre-flight magic-byte check (`%PDF-`) intercepts the file; returns `ExtractedDocument(status="CORRUPTED")`. Triggers `RULE-DOC-02` with status `UNKNOWN`.
- **Status:** **PASS**.

### 7. Empty / Blank PDFs (`test_empty_blank_pdf`)
- **Input:** Valid PDF structure with 1 page containing zero text characters.
- **Challenge:** Zero-text documents must not cause zero-division or index errors in field parsers.
- **Engine Behavior:** Length check catches text $< 30$ chars; returns status `UNREADABLE`.
- **Status:** **PASS**.

### 8. Multi-Page PDFs (`test_multi_page_pdf`)
- **Input:** Marksheet PDF with title and school name on Page 1, candidate name, DOB, and marks table on Page 2.
- **Challenge:** Single-page extraction fails on multi-page forms.
- **Engine Behavior:** Extractor searches across all pages of the document, extracting the values from Page 2 and preserving `page_number: 2` in `EvidenceProvenance`.
- **Status:** **PASS** (Discovered and resolved during forensic audit).

### 9. Unusual Text Positioning (`test_unusual_positioning`)
- **Input:** Text placed at bottom margin ($Y = 10\text{ pt}, 25\text{ pt}$).
- **Challenge:** Some extractors fail when bounding coordinates are near document margins.
- **Engine Behavior:** Captured exact bounding box at low Y coordinates without clipping or truncation.
- **Status:** **PASS**.

### 10. Duplicate Documents (`test_duplicate_documents`)
- **Input:** Packet containing two distinct marksheet scans (`marksheet.pdf` and `marksheet_copy.pdf`).
- **Challenge:** Overwriting or collision in document registry.
- **Engine Behavior:** Ingestion maps documents safely, maintaining deterministic execution without crashing.
- **Status:** **PASS**.

### 11. Incorrect Document Types (`test_incorrect_document_type`)
- **Input:** Electricity bill / utility receipt uploaded as Caste Certificate.
- **Challenge:** Out-of-domain documents must not produce hallucinated fields.
- **Engine Behavior:** Non-matching document headers fail field extraction; `caste_category` is omitted, triggering `RULE-FLD-01` with targeted remediation.
- **Status:** **PASS**.

### 12. Extremely Large Files (`test_large_token_volume`)
- **Input:** Multi-page PDF containing 150+ lines of administrative text surrounding demographic fields.
- **Challenge:** Performance degradation or parser hang on dense files.
- **Engine Behavior:** Extracted in under 35 ms without memory spikes.
- **Status:** **PASS**.

### 13. Malformed Income Expressions (`test_malformed_income_expressions`)
- **Input:** Income fields containing `"NIL"`, `"Zero"`, `"Not Disclosed"`, `"Fifty Thousand Only"`.
- **Challenge:** Unparseable text must not yield `0.0` (which would falsely pass income ceiling tests).
- **Engine Behavior:** Returns `None`, which triggers `RULE-INC-03` with status `UNKNOWN` and instructions to provide a legible numeric certificate.
- **Status:** **PASS**.
