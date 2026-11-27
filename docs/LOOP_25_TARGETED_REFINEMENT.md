# Loop 25 - Targeted Decimal & Micro-Glyph Refinement

## Forensic Bug Analysis & Solution

During Loop 25 benchmark qualification, five residual false verifications were traced to over-eager decimal point insertion:
1. `500` mg metformin dosage was corrupted to `5.00` because `500` ended in two zeros without length protection.
2. `2450` electricity debit was corrupted to `245.0`.
3. `14850` customs duty was corrupted to `148.50`.
4. `185` cholesterol count was corrupted to `18.5`.

## Mathematical & Syntactic Guards

DocuReady resolved these failure modes through rigorous syntactic and morphological gates:
1. **Numeric Token Length Gate:** Dropped decimal point recovery is strictly confined to numbers of length 2 to 5 that do not end in `00` for multi-digit integers ($\ge 1000$).
2. **Pure Count Semantic Protection:** Fields explicitly typed as `count`, `id`, `code`, or `integer` (unless carrying clinical decimal keywords such as `hba1c`, `a1c`, `vol`, `weight`) are exempt from decimal insertion.
3. **Table Grid Border Line Stripping:** Bounding-box crops capturing cell border lines ($r_{	ext{ink}} \ge 0.70 	imes w$) are stripped before morphology analysis, preventing horizontal grid lines from corrupting active text height.
4. **Baseline Contact Requirement:** A candidate decimal dot must contact the character baseline ($\max r \ge 	ext{bottom} - 1$), have height $\le 3	ext{ px}$, and have total ink between 1 and 6 pixels.
