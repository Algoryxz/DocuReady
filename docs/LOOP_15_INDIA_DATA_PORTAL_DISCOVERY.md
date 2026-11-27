# DOCUREADY — LOOP 15 INDIA DATA PORTAL DISCOVERY
## Comprehensive Forensic Investigation of Indian Public Data Portals for Document Ingestion

**Project:** DocuReady — HackNation 2026  
**Engineering Loop:** 15  
**Date:** November 2026  
**Status:** FORENSICALLY SURVEYED & CLASSIFIED  

---

## 1. Objective & Scope

Under the HackNation 2026 governance rules, DocuReady must maintain strict legal provenance and empirical authenticity for document validation. Loop 15 executed an active investigation across all four authorized Indian public data repositories:

1. **data.gov.in** — Open Government Data (OGD) Platform India
2. **ndap.niti.gov.in** — National Data & Analytics Platform (NITI Aayog)
3. **microdata.gov.in/nada** — National Data Archive (Ministry of Statistics and Programme Implementation - MoSPI)
4. **indiadataportal.com** — India Data Portal (Bharti Institute of Public Policy, Indian School of Business)

The mission: determine where genuine administrative forms, multi-script circulars, marksheets, and revenue certificates reside, their machine-readability formats, licensing terms, and acquisition viability.

---

## 2. Empirical Survey Results

A deterministic survey script (`research/loop15/portal_survey.py`) probed base availability, network latency, search APIs, and resource structures.

| Portal | Base Accessibility | Mean Latency | Primary Resource Types | Language Distribution | Licensing Framework |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **data.gov.in** | **Online (200 OK)** | 259.9 ms | CSV, XML, JSON, occasional PDF circulars | Bilingual metadata (Eng/Hin); documents mostly English or Hindi vector | Government Open Data License (GODL) |
| **ndap.niti.gov.in** | **Online (200 OK)** | 308.5 ms | Harmonized time-series CSV, JSON APIs | English data tables; portal UI bilingual | NDAP Open Terms (Attribution required) |
| **microdata.gov.in/nada** | **Online (200 OK)** | 218.8 ms | PDF Questionnaires, Survey Schedules, Microdata files | **Richly bilingual (English + Hindi, English + Regional)** | MoSPI Data Sharing Policy (Public Research) |
| **indiadataportal.com** | **Online (200 OK)** | 651.1 ms | Curated datasets, CSVs, Visualizations | English tabular summaries | Open Research Access (ISB / Bharti Institute) |

---

## 3. In-Depth Portal Forensic Assessments

### 3.1 Portal A: data.gov.in (OGD India)
- **Architecture & Access:** Powered by CKAN open data portal software. Offers public APIs (`/api/3/action/package_search`) and direct search endpoints.
- **Document Finding:** The vast majority of published resources on OGD India are structured datasets (CSV, XLS, JSON) detailing statistics, expenditures, and facility directories.
- **Multilingual Characteristics:** Government gazettes and notifications uploaded as PDFs are primarily native digital PDFs (vector text layers), not scanned physical paper. When scanned PDFs appear, they are usually administrative guidelines or tender notices.
- **License:** **Government Open Data License - India (GODL)**. Fully permissible for validation, research, and non-commercial/commercial computational use with attribution.

### 3.2 Portal B: ndap.niti.gov.in (NDAP / NITI Aayog)
- **Architecture & Access:** Modern Single Page Application (SPA) with authenticated and session-managed GraphQL/REST endpoints. Ad-hoc unauthenticated query probing without frontend token handshake yields HTTP 404 or redirect.
- **Document Finding:** NDAP was explicitly created to harmonize tabular administrative metrics across ministries (health, education, power, rural development). It does **not** host raw citizen-facing administrative certificates (e.g., individual caste/income certificates or university marksheets).
- **Evaluation:** Highly valuable for macro-data validation, but unsuitable as a repository of scanned multi-script application forms.

### 3.3 Portal C: microdata.gov.in/nada (MoSPI National Data Archive)
- **Architecture & Access:** Built on the International Household Survey Network (IHSN) NADA catalog platform. High accessibility (218 ms response time) with search parameters (`/catalog?sk={query}`).
- **Document Finding:** **This is the premier source of authentic Indian government survey schedules, field enumeration forms, and instructions.**
  - Official survey instruments (e.g., NSS 78th Round Multiple Indicator Survey Schedule, NSS 79th Round AYUSH, Periodic Labour Force Survey) are published as comprehensive PDF documents.
  - Sourced document: `DOC_EXT_01_MOSPI_NADA_GUIDE.pdf` (1.7 MB, 50+ pages, MoSPI).
- **Multilingual Characteristics:** These documents feature dual-language column headings (English and Hindi), tabular matrices with Roman numerals and Indic codes, and multi-region instructions.
- **License:** Public dissemination under MoSPI National Data Sharing and Accessibility Policy (NDSAP) for research, verification, and academic modeling.

### 3.4 Portal D: indiadataportal.com (India Data Portal / ISB)
- **Architecture & Access:** WordPress/React frontend with curated datasets on Indian agriculture, rural economy, and socioeconomic indicators.
- **Document Finding:** Excellent portal for mapped indicators and curated district datasets. Like NDAP, it is focused on structured tabular metrics rather than raw paper documents or citizen certificates.
- **Evaluation:** Useful secondary reference; confirms that raw scanned multi-script documents must be gathered from official administrative releases or constructed as rigorous legal templates derived directly from verified official gazettes.

---

## 4. Derived & Ground Truth Architecture for Loop 15

Because Indian citizen certificates (caste certificates, domicile certificates, income certificates, marksheets) contain sensitive personally identifiable information (PII) that cannot legally or ethically be harvested from private citizens without consent:
1. **`VERIFIED_EXTERNAL` Cohort:** Genuine public government documents downloaded directly from authorized repositories (e.g. MoSPI NADA public survey instructions and guidelines).
2. **`DERIVED_FROM_EXTERNAL` Cohort:** Documents structured with exact fidelity to statutory templates prescribed in official state gazettes (e.g., Odisha e-District Revenue formats, Uttar Pradesh Revenue Board formats, Bihar Board marksheets).
3. **`VERIFIED_SYNTHETIC` Cohort:** Controlled synthetic documents engineered to isolate specific failure modes (noise, skew, low contrast, multi-column reading order, mixed-script bounding boxes).

Every document in the Loop 15 corpus is explicitly tagged with its cohort to maintain uncompromised scientific integrity.
