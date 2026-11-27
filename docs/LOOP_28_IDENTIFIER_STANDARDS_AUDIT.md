# Loop 28 Identifier Standards & Check-Digit Audit

## 1. Algorithmic Checksum Comparison
| Identifier Standard | Governing Authority | Length / Syntax | Mathematical Check Digit | Offline Deterministic Validation |
| :--- | :--- | :--- | :--- | :--- |
| **Aadhaar UID** | UIDAI | 12 digits | Verhoeff dihedral group ($D_5$) | **Yes (100% Offline)** |
| **GSTIN** | GSTN / CBIC | 15 chars (`[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]`) | Mod-36 checksum on position 15 | **Yes (100% Offline)** |
| **PAN Card** | Income Tax Dept | 10 chars (`[A-Z]{5}[0-9]{4}[A-Z]`) | None (Internal database check only) | **No (Syntax only)** |
| **IFSC Code** | RBI | 11 chars (`[A-Z]{4}0[A-Z0-9]{6}`) | None (Fixed 5th char '0') | **No (Syntax + Confusable)** |
| **Bank Account** | Individual Banks | 9 to 18 digits | Varies by CBS bank core | **No (Length + Structure)** |

## 2. PAN Limitations & Architectural Defense
Because PAN lacks an offline mathematical checksum, single-document character substitutions (`B` $\leftrightarrow$ `F`, `0` $\leftrightarrow$ `O`) cannot be eliminated through syntax validation alone.
DocuReady Loop 28 introduces multi-source packet corroboration:
- Single PAN alone with ambiguous glyph: Abstain if confidence < 75.0% or confusable glyph detected.
- Multi-document packet: If Document 1 has `AZXPR0298B` and Document 2 has `AZXPR0298F`, the cross-document engine flags `CONTRADICTION_DETECTED`, blocking false verification.
