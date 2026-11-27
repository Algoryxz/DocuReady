# Loop 28 Operational Limitations & Future Research

## 1. Known Limitations
1. **Unstructured Free-Text Narratives**: Entity resolution operates on semi-structured entity hints and extracted key-value pairs; unstructured narrative text resolution requires formal NER extraction.
2. **Offline PAN Limitations**: Without an official offline mathematical checksum (unlike Aadhaar Verhoeff), isolated single-document PAN letter substitutions cannot be caught without cross-document corroboration.
3. **Cross-Language Scripts**: Non-Latin entity name transliteration (e.g., Devanagari/Odia to English phonetic variations) is bounded by SequenceMatcher heuristic limits.
