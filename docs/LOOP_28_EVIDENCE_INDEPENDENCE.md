# Loop 28 Evidence Independence & Duplication Detection

## 1. The Circular Evidence Hazard
A common fraud vector and operational error is uploading duplicate copies or re-scans of the same document under different filenames (e.g., `income_cert.pdf` and `income_cert_verified_copy.pdf`).
If a system treats these as independent sources, repeated OCR errors become falsely "corroborated" claims.

## 2. Independence Taxonomy
DocuReady classifies multi-document relationships into four discrete categories:
1. `INDEPENDENT`: Distinct documents issued by independent authorities or separate events.
2. `DUPLICATE`: Identical SHA-256 byte/text content hash, identical filename, or >96% verbatim textual match.
3. `DERIVED`: Summary document directly quoting a primary source without independent evidentiary standing.
4. `CORRELATED_OCR`: Documents produced from identical templates exhibiting shared OCR layout biases.

## 3. Enforcement Invariant
When two claims agree but originate from documents flagged as `DUPLICATE`, the cross-document engine suppresses the multi-source corroboration confidence bonus, treating the claim as single-source evidence.
