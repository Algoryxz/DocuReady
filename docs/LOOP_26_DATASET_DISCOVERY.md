# Loop 26 - Independent Dataset Discovery & Candidate Audit

## Executive Summary

To evaluate independent real-world generalization without data contamination or synthetic bias, seven candidate public and academic document datasets were audited against strict legal, licensing, privacy, and task suitability criteria.

## Dataset Suitability Matrix

| Candidate Dataset | Primary Domain | Official Source | License Status | PII / Privacy Risk | Task Alignment | Benchmark Verdict |
|---|---|---|---|---|---|---|
| **FUNSD** | Scanned Forms | Guillaume Jaume / IIT-CDIP | Public Domain / Research | Non-PII (Historical) | High (Key-Value Forms) | **APPROVED (16 Docs)** |
| **SROIE** | Scanned Receipts | ICDAR 2019 / CVC | Research License | Anonymized Merchant | High (Line-Item Totals) | **APPROVED (16 Docs)** |
| **Indic OCR** | Govt Certificates | OGD India / State Portals | OGD / CC-BY Compatible | Anonymized Public Format | High (Bilingual Revenue) | **APPROVED (15 Docs)** |
| **DocLayNet** | Financial & Legal | IBM Research | CDLA-Permissive-1.0 | Open Corporate Disclosures | High (Complex Tables) | **APPROVED (13 Docs via Degradation)** |
| **CORD** | Indonesian Receipts | Clova AI | CC-BY-SA 4.0 | Low (Commercial POS) | Medium (Non-target script) | DEFERRED (Scope constraint) |
| **PubTables-1M** | Scientific Tables | Microsoft Research | CDLA-Permissive-1.0 | Synthetic / Unrendered | Low (Vector-only XML) | EXCLUDED (Not real scans) |
| **IIT-CDIP Full** | Legacy Litigation | UCSF Library | Public Domain | Unindexed (Needs OCR) | Medium (FUNSD subset chosen) | EXCLUDED (Redundant with FUNSD) |

## Selection Decision

A unified 60-document independent corpus (**Cohort K**) was constructed from approved sources, representing 6 document families, 3 acquisition conditions, and 3 layout paradigms.
