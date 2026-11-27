# DOCUREADY — LOOP 33 IDENTIFIER INTEGRITY & AMBIGUITY AUDIT (FAMILY A)

**Milestone:** Loop 33 — Domain Rules & Decision Integrity  
**Component:** `src/docuready/ingest/identifier_validation.py`, `src/docuready/normalize/normalizer.py`  
**Operating Thresholds:** $T^* = 70.0$, $T_{\text{fuzzy}} = 75.0$  
**Evaluation Date:** 2026-11-25  

---

## 1. Scope & Objectives

Rule Family A governs the extraction, syntactic verification, cross-character ambiguity handling, and cross-document comparison of critical alphanumeric identifiers:
- **IFSC Codes:** Bank routing identifiers (RBI standard).
- **PAN Cards:** Permanent Account Numbers (CBDT standard).
- **Aadhaar Numbers:** 12-digit national identification with Verhoeff dihedral D5 checksum.
- **Bank Account Numbers:** 9 to 18-digit account strings.
- **Registration / Roll Numbers:** Educational and institutional roll strings.
- **Certificate Reference Numbers:** State revenue and caste certificate references.

The objective of this audit is to verify that identifier matching is mathematically sound, detects OCR visual glyph confusions, suppresses punctuation bleed, and strictly abstains on ambiguity rather than producing false verifications.

---

## 2. Structural & Algorithmic Standards

### 2.1 Verhoeff D5 Dihedral Checksum (Aadhaar)
- **Standard:** UIDAI Specification & Dihedral Group $D_5$.
- **Implementation:** `validate_verhoeff()` in `identifier_validation.py`.
- **Properties:**
  - Detects 100% of single-digit substitution errors ($a \to b$).
  - Detects 100% of adjacent transposition errors ($ab \to ba$).
  - Detects >95% of twin and jump-transposition errors ($aba \to aca$).
- **Audit Result:** PASS. The multiplication table `VERHOEFF_D`, permutation table `VERHOEFF_P`, and inverse table `VERHOEFF_INV` are implemented bit-identically to the standard.

### 2.2 IFSC Code Strict Structure (RBI Master Direction)
- **Standard:** 11 characters: `^[A-Z]{4}0[A-Z0-9]{6}$`.
- **Critical Rule:** 5th character must be numeric zero (`0`), never alphabet `'O'`.
- **Audit Finding:** In OCR outputs, `SBIN0001234` is frequently recognized as `SBINO001234` or `SBINOOO1234`. The strict regular expression `RE_IFSC_STRICT` correctly rejects or flags confusable `'O'` via `RE_IFSC_CONFUSABLE`. When the 5th character is `'O'`, the engine flags `ambiguous_glyphs=['O']` and abstains with status `REVIEW`.

### 2.3 Permanent Account Number (PAN) Strict Mask (CBDT Rule 114)
- **Standard:** 10 characters: `^[A-Z]{5}[0-9]{4}[A-Z]$`.
- **Audit Finding:** The mask strictly enforces 5 uppercase alphabetic characters, followed by 4 digits, followed by 1 alphabetic check character. Confusable substitutions (e.g. `ABCDE1234O` vs `ABCDE12340`) are caught by the character-type constraint: position 10 must be alpha, while positions 6–9 must be numeric.

---

## 3. Visual Glyph Confusable Matrix & Punctuation Bleed

DocuReady enforces a formal confusable pair matrix:
| Character Pair | Visual Context | Detection Rule | Engine Action |
| :---: | :---: | :---: | :---: |
| `O` vs `0` | Alpha-numeric boundary | Type-mask check | Abstain (REVIEW) |
| `I` vs `1` vs `l` | Vertical stroke confusion | Digit/alpha expected | Abstain (REVIEW) |
| `S` vs `5` | Curvature stroke confusion | Position mask check | Abstain (REVIEW) |
| `B` vs `8` | Dual loop confusion | Position mask check | Abstain (REVIEW) |
| `Z` vs `2` | Diagonal corner confusion | Position mask check | Abstain (REVIEW) |
| `G` vs `6` | Open/closed loop confusion | Position mask check | Abstain (REVIEW) |

### Punctuation Bleed Suppression
In raw OCR scans, trailing or leading commas, periods, quotation marks, or currency symbols often adhere to identifier tokens (e.g., `"SBIN0001234,"` or `'ABCDE1234F'`).
- `sanitize_identifier_token()` cleanly strips leading/trailing quotes, punctuation, and currency markers (`₹`, `Rs.`, `INR`) before syntax evaluation while preserving valid internal hyphens and slashes.

---

## 4. Verification Findings & Abstention Policy

Under Loop 27 and Loop 32 hardening:
1. Identifiers that violate strict structural syntax are **rejected or flagged**.
2. Identifiers with confusable glyphs without checksum validation produce `MatchGrade.AMBIGUOUS` with status `Status.REVIEW` (`ReasonCode.EVIDENCE_AMBIGUOUS`).
3. Multi-document comparisons between ambiguous candidate identifiers never resolve to `EXACT` or `COMPATIBLE`; they strictly abstain.

**Audit Status:** APPROVED. Family A rules are fully sound and conservative.
