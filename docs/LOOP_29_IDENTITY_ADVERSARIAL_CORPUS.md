# Loop 29 Identity Resolution Adversarial Suite (20 Cases)

## 1. Evaluation Results (20/20 PASSED)
| Case ID | Description | Expected | Actual | Status |
| :--- | :--- | :--- | :--- | :--- |
| CASE_01_SAME_PERSON_MATCHING_DOB | Same person, same name, matching DOB | ACCEPT | ACCEPT | **PASS** |
| CASE_02_DIFFERENT_PEOPLE_SAME_NAME | Different people, same name, distinct DOBs | REJECT | REJECT | **PASS** |
| CASE_03_SIBLINGS_SHARING_PARENT_ADDRESS | Siblings sharing father name and address, distinct DOBs and names | REJECT | REJECT | **PASS** |
| CASE_04_PARENT_CHILD_SIMILAR_NAMES | Parent and child with similar names (Ramesh Verma vs Ramesh Verma Jr) | REJECT | REJECT | **PASS** |
| CASE_05_DIFFERENT_DOB_SAME_NAME | Different DOB, identical name, without other anchors | REJECT | REJECT | **PASS** |
| CASE_06_SAME_ADDRESS_UNRELATED_APPLICANTS | Same rental address, completely unrelated applicants | REJECT | REJECT | **PASS** |
| CASE_07_SAME_AMOUNT_UNRELATED_APPLICANTS | Same fee payment amount (INR 5500.00), unrelated applicants | REJECT | REJECT | **PASS** |
| CASE_08_VERMA_VARMA_SPELLING_VARIATION | Verma versus Varma spelling variation with matching DOB anchor | ACCEPT | ACCEPT | **PASS** |
| CASE_09_PAN_O_0_CONFUSION | PAN O vs 0 confusable at index 4 (BARBOBHUBAN vs BARB0BHUBAN) | REJECT | REJECT | **PASS** |
| CASE_10_PAN_B_8_CONFUSION | PAN B vs 8 visual confusion in alphanumeric identifier | REJECT | REJECT | **PASS** |
| CASE_11_PAN_ONE_CHAR_SUBSTITUTION | PAN 1-char substitution (AZXPR0298B vs AZXPR0298F) across docs | REJECT | REJECT | **PASS** |
| CASE_12_PAN_CONFLICT_INDEPENDENT_DOCS | PAN conflict across independent docs (ABCDE1234F vs XYZPR9876K) | REJECT | REJECT | **PASS** |
| CASE_13_REPEATED_PAN_DUPLICATE_DOCS | Repeated PAN copied into multiple documents (duplicate check) | DUPLICATE | DUPLICATE | **PASS** |
| CASE_14_DUPLICATE_SCAN_DIFFERENT_FILENAME | Identical content hash under different filenames | DUPLICATE | DUPLICATE | **PASS** |
| CASE_15_SAME_FILENAME_UNRELATED_DOCS | Same filename ('invoice.pdf') used for distinct documents (different hashes) | INDEPENDENT | INDEPENDENT | **PASS** |
| CASE_16_SAME_DOC_CHANGED_FORMATTING | Same underlying document with reformatted text | DUPLICATE | DUPLICATE | **PASS** |
| CASE_17_MULTILINGUAL_TRANSLITERATION | Transliteration variation (Soumya vs Saumya) with matching DOB | ACCEPT | ACCEPT | **PASS** |
| CASE_18_MISSING_DOB_MISSING_UID | Different names without any DOB or unique identifier | REJECT | REJECT | **PASS** |
| CASE_19_CONFLICTING_FATHER_AND_DOB | Conflicting father name and conflicting DOB despite identical name | REJECT | REJECT | **PASS** |
| CASE_20_SHARED_FAMILY_IDENTIFIERS | Two family applicants with shared family ration card, distinct applicant names | REJECT | REJECT | **PASS** |
