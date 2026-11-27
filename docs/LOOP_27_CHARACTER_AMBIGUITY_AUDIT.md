# DOCUREADY LOOP 27 — CHARACTER-LEVEL OCR AMBIGUITY AUDIT
## Visual Glyph Confusables, Font Sub-Pixel Distortion & Guard Mechanisms

---

### 1. Confusable Glyph Matrix

| Glyph Pair | Context / Position | Failure Mode | DocuReady Prevention Rule |
|---|---|---|---|
| `O` vs `0` | IFSC 5th character | OCR outputs `BARBOBHUBAN` | Structural regex enforces 5th char `0`; flags `O/0` confusable |
| `I` / `l` vs `1` | Numeric account / PAN digits | OCR outputs `12345l789` | Numeric-only validation rejects alphabetic glyphs |
| `S` vs `5` | Account / PAN sequence | OCR outputs `ABCDES234F` | Type-sequence contradiction detection |
| `B` vs `8` | Numeric fields | OCR outputs `1234B678` | Type-sequence contradiction detection |
| `Z` vs `2` | Alphanumeric transitions | OCR outputs `Z026` vs `2026` | Strict syntax bounds |
| Trailing Punctuation | Receipt dates / IDs | `10/10/2028,` | Deterministic edge sanitization + horizon gating |
