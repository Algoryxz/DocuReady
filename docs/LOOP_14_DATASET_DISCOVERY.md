# DOCUREADY — LOOP 14
## Indian Public Data Portals Deep Forensic Discovery Report

**Audit Date:** 2026-11-22  
**Harness:** `research/loop14/portal_research.py`  
**Output Data:** `research/loop14/portal_survey_results.json`  
**Scope:** Automated inspection and forensic content verification across all four Indian national public portals.  

---

### 1. Executive Summary

In compliance with Section 2 of the Loop 14 Directive, an active probe and deep forensic evaluation of all four designated Indian government and open-data portals was executed. The objective was to discover authentic administrative document formats, government circulars, scholarship verification schedules, and questionnaire layouts across English, Hindi, and Odia.

Every portal was evaluated for network availability, response latency, architectural framework, search API functionality, downloadable file types (native text vs scanned raster), language distribution, and licensing constraints.

---

### 2. Empirical Portal Accessibility & Latency Matrix

| Portal Key | Portal Name | Authority / Host | Base URL | Base Status | Latency | Search Endpoints | Architecture Model |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **Portal A** | Open Government Data (OGD) | National Informatics Centre (NIC) | `https://www.data.gov.in` | **200 OK** | 377.3 ms | **200 OK** (5 queries) | Nuxt.js SSR + CKAN Backend |
| **Portal B** | NDAP | NITI Aayog | `https://ndap.niti.gov.in` | **200 OK** | 269.8 ms | **404 / API Restricted** | Client-Side SPA (React) + GraphQL API |
| **Portal C** | MoSPI Microdata Archive | Ministry of Statistics (MoSPI) | `https://microdata.gov.in/nada` | **200 OK** | 290.9 ms | **200 OK** (4 queries) | NADA National Data Archive (PHP) |
| **Portal D** | India Data Portal | Bharti Institute (ISB) | `https://indiadataportal.com` | **200 OK** | 750.7 ms | **200 OK** (4 queries) | WordPress + CKAN Open Data |

---

### 3. Forensic Portal Analysis & Document Types

#### Portal A: data.gov.in (Open Government Data Platform)
- **Operated by:** National Informatics Centre (NIC), Ministry of Electronics & IT (MeitY).
- **Architecture:** Nuxt.js Server-Side Rendered (SSR) portal communicating with CKAN data catalog services.
- **Search Query Probing:**
  - `scholarship` $\to$ HTTP 200 (1,221 ms)
  - `income certificate` $\to$ HTTP 200 (924 ms)
  - `caste` $\to$ HTTP 200 (1,047 ms)
  - `guidelines` $\to$ HTTP 200 (1,015 ms)
  - `format` $\to$ HTTP 200 (1,170 ms)
- **Document Formats Discovered:** Central sector scholarship guidelines, quota allocation circulars, revenue department application formats. Most resources are distributed as published policy circulars (PDF) or open CSV aggregate datasets.
- **Licensing:** Government Open Data License - India (GODL-India).

#### Portal B: NDAP (National Data & Analytics Platform)
- **Operated by:** NITI Aayog.
- **Architecture:** Modern Single-Page Application (SPA) built with React/Angular frontends. Search requests via URL query parameters return HTTP 404 because routing is client-side, while data is retrieved through internal GraphQL microservices (`/api/v1/...`).
- **OCR Relevance:** NDAP primarily aggregates standardized tabular CSV datasets (district indicators, census metrics). Document imagery is limited to methodological notes and survey documentation.
- **Licensing:** NITI Aayog Open Access Terms.

#### Portal C: microdata.gov.in/nada (MoSPI Microdata / NADA)
- **Operated by:** National Statistical Office (NSO), Ministry of Statistics and Programme Implementation (MoSPI).
- **Architecture:** International Household Survey Network (IHSN) NADA catalog platform.
- **Search Query Probing:**
  - `NSS` $\to$ HTTP 200 (695 ms)
  - `Schedule` $\to$ HTTP 200 (722 ms)
  - `Questionnaire` $\to$ HTTP 200 (260 ms)
  - `Income` $\to$ HTTP 200 (274 ms)
- **Document Discovery & Verification:**
  - The Central Data Catalog lists 15+ major national survey series (e.g. Study 237: *Household Consumption Expenditure Survey: 2023-24*, Study 254: *Periodic Labour Force Survey (PLFS)*, Study 290: *Household Social Consumption: Health*).
  - Authentic, downloadable government PDF documents are hosted directly, including the official user guide: `/NADA/Guide_to_download_microdata.pdf` (1,701,761 bytes), acquired as `DOC_EXT_01_MOSPI_NADA_GUIDE.pdf`.
- **Licensing:** Government of India Official Statistics Data Dissemination Policy (Public Use Data).

#### Portal D: indiadataportal.com (India Data Portal)
- **Operated by:** Bharti Institute of Public Policy, Indian School of Business (ISB).
- **Architecture:** Open CKAN platform with WordPress CMS.
- **Search Query Probing:**
  - `scholarship` $\to$ HTTP 200 (477 ms)
  - `agriculture` $\to$ HTTP 200 (451 ms)
  - `education` $\to$ HTTP 200 (474 ms)
  - `report` $\to$ HTTP 200 (444 ms)
- **Document Discovery:** Rich collection of agricultural surveys, district-wise education metrics, and rural development reports with bilingual headers.
- **Licensing:** Creative Commons Attribution 4.0 (CC BY 4.0).

---

### 4. Legal, Privacy & Ingestion Governance

1. **Zero-PII Compliance:** No private applicant submissions, live beneficiary records, or unredacted personal files were downloaded or processed. All investigated resources are official government formats, blank schedules, methodology guides, or published public gazettes.
2. **Access Control Integrity:** All downloads adhered strictly to open-access HTTP endpoints without attempting authentication bypass, scraping protected boundaries, or circumventing bot detection.
