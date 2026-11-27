# DocuReady Loop 32 Root-Cause Analysis

**Programme:** DocuReady Product Excellence  
**Investigation Focus:** Deep Architectural Root Causes for Discovered Defects  
**Date:** 2026-11-25  

---

## 1. Mathematical Corruption in Duplicate Verhoeff Tables (BUG-032-005)

### Deep Root Cause
During early MVP development, the Verhoeff checksum algorithm was implemented in `src/docuready/normalize/normalizer.py` based on an incorrect handwritten copy of the dihedral group $D_5$ multiplication table. The author mistakenly assumed that the lower rows of the table followed simple cyclic addition modulo 10 ($x + y \pmod{10}$):
```python
# Corrupted rows 5-9 in normalizer.py:
[5, 6, 7, 8, 9, 0, 1, 2, 3, 4],  # cyclic mod 10!
```
In reality, the dihedral group $D_5$ is non-abelian; the lower rows reflect reflection operations:
```python
# Authoritative dihedral D5 rows in identifier_validation.py:
[5, 9, 8, 7, 6, 0, 4, 3, 2, 1],  # true D5 reflection!
```
In Loop 27, when formal identifier verification was hardened, the developer correctly implemented `identifier_validation.py` with standard tables but forgot to deprecate or update the duplicate in `normalizer.py`.
**Remedy:** Centralized all Verhoeff logic to single source of truth (`identifier_validation.py`).

---

## 2. Pluggable PDF Backend Interface Mismatch (BUG-032-001)

### Deep Root Cause
PyMuPDF (`fitz.Page.search_for`) returns instances of `fitz.Rect` which have property getters `.x0`, `.y0`, `.x1`, `.y1`. However, standard abstract PDF backends (such as pdfplumber, pypdf, or custom test mocks) return standard Python `Tuple[float, float, float, float]`. `extractor.py` hardcoded property access without polymorphism or duck-typing guards.
**Remedy:** Added duck-typing attribute check `hasattr(r, "x0")` with tuple fallback.

---

## 3. Asymmetric Format Canonicalization in Date Normalizer (BUG-032-002)

### Deep Root Cause
The date normalization regex in `cross_document.py` was built under the assumption that all input dates were in the Indian / Commonwealth format `DD/MM/YYYY`. When hyphens were present, it replaced `-` with `/` and matched `(\d{1,2})/(\d{1,2})/(\d{2,4})`. This turned `2026-03-15` into `2026/03/15`, matching group 1 as 2026 (day), group 2 as 3 (month), and group 3 as 15 (year), generating invalid or unparsed date representations that failed cross-document equality against `15/03/2026`.
**Remedy:** Added explicit ISO pattern `^(\d{4})/(\d{1,2})/(\d{1,2})$` before generic matching.

---

## 4. Silent Basename Collision in Workspace Staging (BUG-032-004)

### Deep Root Cause
Desktop workspace file staging used `path.join(packetDir, doc.name)` as the destination path. In audit workflows involving multiple invoices or certificates from different sources, files frequently share generic basenames (e.g. `invoice.pdf`, `receipt.pdf`). Writing to `packetDir` without tracking seen basenames resulted in silent overwriting and corrupted multi-document evidence bundles.
**Remedy:** Added tracking `seenNames` set and appended `${base}_${doc.id}${ext}` upon collision.
