# DOCUREADY LOOP 27 — IDENTIFIER TAXONOMY & VERIFICATION SPECIFICATION
## Formal Structural Grammars, Check Digits & Ambiguity Matrices

---

### 1. Identifier Class Taxonomy

| Class ID | Identifier Family | Canonical Regex / Grammar | Check Digit Algorithm | Common Visual Ambiguities |
|---|---|---|---|---|
| `ID_IFSC` | Indian Financial System Code | `^[A-Z]{4}0[A-Z0-9]{6}$` | Fixed 5th digit invariant `0` | `O/0` at index 4 |
| `ID_PAN` | Permanent Account Number | `^[A-Z]{5}[0-9]{4}[A-Z]$` | Pos 9 alphabetic check | `0/O`, `1/I`, `5/S`, `8/B` |
| `ID_GSTIN` | GST Identification Number | `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$` | Mod 36 checksum | `O/0` in state code |
| `ID_ACCT` | Bank Account Number | `^[0-9]{9,18}$` | Numeric only | `O/0`, `l/1`, `I/1`, `S/5` |
| `ID_UID` | Aadhaar National ID | `^[2-9][0-9]{11}$` | Verhoeff Dihedral $D_5$ | Numeric substitutions |
| `ID_DATE` | Calendar Date | `^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$` | Chronological boundary $\le 2026$ | Trailing punctuation, `6/8` |
| `ID_GEN` | Generic Alphanumeric ID | `^[A-Za-z0-9][A-Za-z0-9_\-\./]*$` | Format-dependent | Multi-token bleed, garble |

---

### 2. Mathematical Formalization of Verhoeff Algorithm
For Aadhaar and checked identifiers, validation uses the dihedral group $D_5$:
$$c = \sum_{i=0}^{n-1} d\Big(c, p(i \pmod 8, d_i)\Big) = 0$$
Where $d$ is the multiplication table, $p$ is the permutation table, and inverse operations guarantee detection of 100% of single-digit substitutions and 100% of adjacent transpositions.
