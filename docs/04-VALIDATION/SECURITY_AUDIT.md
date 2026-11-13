# DocuReady Security & Privacy Audit Report

**Date:** 2026-11-13  
**Auditor:** Antigravity (Google DeepMind Agent)  
**Standard:** Digital Personal Data Protection (DPDP) Act 2023 & UIDAI Aadhaar Data Security Guidelines

---

## 1. Vulnerability Assessment & Implemented Hardening

| Security Domain | Risk Description | Status Before Audit | Implemented Remediation | Current Status |
|---|---|---|---|---|
| **Path Traversal** | Filenames containing `../` or `..\` could allow writing outside designated upload folders. | Potential vulnerability via un-sanitized `uf.name` | Added strict basename isolation and sanitization: `os.path.basename(name).replace('..', '')` | **HARDENED** |
| **File-Type Validation** | Extension spoofing (renaming executable/script to `.pdf`). | Only `.pdf` extension checked | Added binary magic-byte pre-flight inspection (`%PDF-` in first 10 bytes) before opening with PyMuPDF | **HARDENED** |
| **Upload Size Limits** | Denial-of-Service (DoS) through memory exhaustion with multi-hundred megabyte files. | Default Streamlit 200MB ceiling | Enforced strict 10MB per-document limit in `src/ui.py`. Oversized files are rejected upfront. | **HARDENED** |
| **Sensitive Data Logging** | Printing unmasked Aadhaar numbers or bank accounts in server console. | Minor exposure in debug CLI prints | Masking implemented for sensitive identifiers: Aadhaar numbers masked to `XXXXXXXX1234`; Bank accounts masked to `XXXXXX4301`. | **HARDENED** |
| **Persistent Storage** | Citizen documents stored on unencrypted local disk indefinitely in kiosk environments. | Files written to disk directory | Added privacy advisory: in production kiosks, in-memory stream buffers or automated ephemeral cleanup should be used. | **DOCUMENTED / ISOLATED** |
| **Air-Gap Integrity** | Outbound telemetry or cloud LLM calls leaking citizen documents. | Verified zero external calls | 100% offline air-gapped deterministic computation. Zero socket/HTTP requests made during audits. | **VERIFIED CLEAN** |

---

## 2. Privacy & Statutory Compliance (DPDP Act 2023)

### 1. Data Minimization (Section 6)
DocuReady extracts only the minimum demographic fields strictly necessary to verify compliance against statutory scheme criteria (Name, DOB, Income, Category, Account Number, IFSC, Validity Dates). Extraneous personal information (e.g., biometric photos, mobile numbers, biometric hashes) is intentionally discarded and never parsed.

### 2. Ephemeral Storage & Retention Policy (Section 8)
In kiosk deployments (e.g. Mo Seva Kendras, CSCs):
- Document packets are analyzed strictly during the active session.
- Once the pre-submission readiness certificate is downloaded by the citizen, session caches must be purged.
- Uploaded files are restricted to isolated synthetic data folders during development and testing.

### 3. Aadhaar Act 2016 (Section 29) Masking Compliance
DocuReady strictly forbids storing or displaying unmasked 12-digit Aadhaar numbers. In all generated UI tables, audit reports, and logs, Aadhaar numbers are presented in masked format (`XXXXXXXX1234`).
