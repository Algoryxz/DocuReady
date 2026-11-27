# DocuReady Parameter-Level Source-Verification Matrix: SUBHADRA Yojana

**Document ID:** `DOC-VAL-SUB-EVIDENCE-MATRIX-001`
**Task:** T3.3 — Odisha SUBHADRA scheme pack
**Owner:** Susmita — Domain Rules, Evidence & Evaluation
**Reviewer:** Akriti — Platform, Privacy & Delivery Lead (Evidence-Matrix Reviewer)
**Version:** `v1.4` (Post-PR #88 Reconciled Edition)
**Prepared / matrix re-verification:** 22 November 2026 | **Reviewer clarification:** 24 November 2026 | **Rebased on `main`:** 27 November 2026
**Review status:** Reviewer clarifications incorporated on 24 November 2026; PR #85 (`fe73c4d`) merged into `main` at `fb630d6`; PR #86 (`535c38f`) merged governance reconciliation at `c1d6976`; PR #88 (`1f3721e`) merged Aadhaar & `field_present` safety fixes at `7ccf274`. On 27 November 2026, the Product Owner confirmed Akriti's agreement with this source-review matrix and Aadhaar-upload interpretation and authorized the shared `field_present` correction. T3.3 final formal acceptance remains open.
**Implementation status:** `RULE-SUB-DOC-01` removed in `odisha.subhadra` `2024.1.1` (keeping `aadhaar_card.required: false`), and shared `eval_field_present()` corrected with cross-pack regression coverage. Age-transition §3.1(e), unverified reopening/deadline records, and deferred exclusions remain unchanged.

> This matrix separates (1) what the Government source establishes, (2) what DocuReady can safely verify from supplied evidence, and (3) what is actually implemented. A verified legal requirement is not automatically an automatable rule. This is a document-verification aid, not an eligibility decision or Government determination.

---

## 1. Source Register and Provenance

**Retrieval-date reconciliation:** The three official PDFs retain `retrieved_on: 2026-11-21` in `packs/odisha.subhadra/sources.yaml`, recording the initial source-registry retrieval. The matrix author re-opened and re-verified those same official PDFs on **22 November 2026**. These are separate retrieval/re-verification events; the original registry retrieval dates are not overwritten. The secondary announcement listed below was retrieved on **22 November 2026**.

| Source ID | Exact Title / Identifier | Issuing Authority | Document / Issue Date | Retrieval Date | Official URL | Verified Clauses & Printed Pages | Base Statutory Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`SRC-SUB-GUIDELINES-2024`** | *Guidelines for Implementation of 'SUBHADRA' Scheme* (Letter No. 19188/WCD; File No. WCD-ICDS-M-SCHM-0003-2024) | Dept of Women & Child Development, Govt of Odisha | Guidelines: Aug 2024; letter: `2024-08-29` | `2026-11-21` | [W&CD Guidelines PDF](https://wcd.odisha.gov.in/sites/default/files/2025-06/148.%20Lt.%20No.%2019188Dt.%2029.08.2024%20Circulation%20of%20Subhadra%20guideline%20English.pdf) | pp. 4–5, §§5.1–5.2; p. 5, §6(g), §7(a)(ii) | `VERIFIED` |
| **`SRC-SUB-GAZETTE-2024`** | *The Odisha Gazette Extraordinary No. 1637* (Resolution No. 19898—WCD-SUBH-SCHM-0008/2024/WCD) | Dept of Women & Child Development, Govt of Odisha | `2024-09-05` | `2026-11-21` | [Gazette Resolution PDF](https://wcd.odisha.gov.in/sites/default/files/2025-07/1637%20Gazette%20Resolution%20ENGLISH_0.pdf) | p. 1, §1(e); p. 2, §§2(a), 3.1(a)–(e), 3.2(a), 3.2(b)(i)–(iii); p. 3, §§3.2(b)(iv)–(vi), 3.2(c), 4(g); p. 4, §5(a)(i)–(iii) | `VERIFIED` |
| **`SRC-SUB-SOP-2024`** | *Standard Operating Procedure (SOP) for Implementation of SUBHADRA Yojana* (Letter No. 26139/WCD; No. WCD-SUBH-SCHM-0029-2024) | Dept of Women & Child Development, Govt of Odisha | SOP: Oct 2024; letter: `2024-11-11` | `2026-11-21` | [SOP English PDF](https://wcd.odisha.gov.in/sites/default/files/2025-07/26139%20Dt.%2011.11.2024%20SOP%20Subhadra%20English.pdf) | p. 3, §2; p. 6, §§4.1–4.3; p. 7, §4.4; p. 11, §10(f); p. 14, Annx 2; p. 15, Annx 3 | `VERIFIED_WITH_LIMITATIONS` |
| **`SRC-SUB-INTAKE-WINDOW`** | *Subhadra Scheme Public Portal* (`subhadra.odisha.gov.in`) | Dept of Women & Child Development, Govt of Odisha | Ongoing Administrative Reference | `2026-11-21` | [Subhadra Portal](https://subhadra.odisha.gov.in) | General Administrative Reference (No gazetted cutoff date) | `UNVERIFIED` (`supports_rule: false`) |
| **`SRC-SUB-ANNOUNCEMENT-2026-09-16`** | Secondary news report: *"Subhadra turns 2, govt announces fresh registration window"* | The Pratidhwani (secondary news publication; not a Government authority) | Published `2026-09-16` | `2026-11-22` | [Pratidhwani Report](https://thepratidhwani.com/2026/09/16/subhadra-turns-2-govt-announces-fresh-registration-window-bhubaneswar-news/) | Context/chronology only; reports statement attributed to Dy CM Pravati Parida on `01-04-2027` reopening | `UNVERIFIED` (`supports_rule: false`) |
| **`SRC-SUB-REOPENING-NOTICE-2027`** | Required date-specific official written notification for reported `01-04-2027` reopening | Dept of Women & Child Development, Govt of Odisha (expected; notice not produced) | Not supplied as of `2026-11-22` | N/A | Not available — awaiting official notice | Evidence-gap placeholder only; not an actual source document | `UNVERIFIED` (`supports_rule: false`) |

**Authority hierarchy:** Gazette Resolution is the primary published scheme resolution; Guidelines supply operational eligibility and ineligibility criteria; SOP supplies application, assisted-submission, e-KYC, scrutiny, and field-verification procedures.

---

## 2. Two-Dimensional Status & Reason-Code Vocabulary

1. **Statutory Evidence Status:** `VERIFIED` | `VERIFIED_WITH_LIMITATIONS` | `UNVERIFIED` | `REQUIRES_STATUTORY_SOURCE_VERIFICATION` | `NOT_APPLICABLE`
2. **Internal Implementation Status:** `INTERNAL_CONTRACT_VERIFIED` | `IMPLEMENTED` | `UNIMPLEMENTED` | `NOT_APPLICABLE`
3. **Reason-Code Compatibility Clarification (24 November 2026):** Illustrative issue labels such as `TRANSITION_REQUIRES_YEAR_SCOPE` or `EXTERNAL_VERIFICATION_REQUIRED` are **not** members of the canonical `ReasonCode` enum in `src/docuready/domain/enums.py` and must never be written to findings. For unresolved age-transition scope or unavailable external verification, use the existing contract: `Raw.INDETERMINATE` + `EvidenceState.UNCERTAIN` $\to$ `Status.REVIEW` / `ReasonCode.INSUFFICIENT_DATA`.

---

## 3. Parameter-Level Evidence & Technical Compatibility Matrix

### Verified Manifest Document Slots (`packs/odisha.subhadra/pack.yaml`)
All 5 slots are configured with `required: false`:
`aadhaar_card` (`[eng, ori]`), `bank_passbook` (`[eng]`), `income_certificate` (`[eng, ori]`), `application_form` (`[eng, ori]`), `ration_card` (`[eng, ori]`).

### Domain 1: Eligibility and Odisha Residency

| Parameter | Manifest Slot / Field | Source ID & Printed Page | Supporting Statutory Wording | Statutory Status | Internal Status | Contract & Implementation Implication |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Odisha Residency Mandate** | No direct verified slot | `SRC-SUB-GUIDELINES-2024` §5.1(a), p. 4; `SRC-SUB-GAZETTE-2024` §3.1(a), p. 2 | *"The applicant must be a resident of Odisha."* | `VERIFIED` | `UNIMPLEMENTED` | `enum_in` is unactivated. DocuReady does not extract address or verify domicile. Aadhaar presence does not prove Odisha residency. |

### Domain 2: Age Criteria and Qualifying Reference Date

| Parameter | Manifest Slot / Field | Source ID & Printed Page | Supporting Statutory Wording | Statutory Status | Internal Status | Contract & Implementation Implication |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Age Reference Date** | `age_reference_date` (`"2024-07-01"`) | `SRC-SUB-GUIDELINES-2024` §5.1(c), p. 4; `SRC-SUB-GAZETTE-2024` §3.1(c), p. 2 | *"21 years of age or above and less than 60 years of age as on 01.07.2024."* | `VERIFIED` | `IMPLEMENTED` | Scoped strictly to FY 2024–25 baseline in `RULE-SUB-AGE-01` (`age_on`). |
| **Minimum / Maximum Age** | `min_age` (`21`), `max_age` (`59`) | `SRC-SUB-GUIDELINES-2024` §5.1(c), p. 4; `SRC-SUB-GAZETTE-2024` §3.1(c), p. 2 | Born between `02.07.1964` and `01.07.2003`. | `VERIFIED` | `IMPLEMENTED` | `max_severity: FAIL` only for scoped FY 2024–25 baseline when Aadhaar DOB is `VERIFIED`. |
| **Aadhaar DOB Sole Proof** | `aadhaar_card.dob` | `SRC-SUB-GUIDELINES-2024` §5.1(d), p. 4; `SRC-SUB-GAZETTE-2024` §3.1(d), p. 2 | *"The date of birth recorded in the Aadhaar card would be taken as the final proof for the age."* | `VERIFIED` | `IMPLEMENTED` | Missing/unparseable DOB $\to$ `Raw.INDETERMINATE` $\to$ `Status.REVIEW` / `ReasonCode.INSUFFICIENT_DATA`. |
| **FY 2024–25 Post-Qualifying Date Age Transition** | No direct verified slot | `SRC-SUB-GAZETTE-2024` §3.1(e), p. 2; `SRC-SUB-GUIDELINES-2024` §5.1(e), p. 4 | Women turning 21 after `01.07.2024` receive ₹10,000/year for remaining scheme years; turning 60 after `01.07.2024` cease receiving benefits for remaining years. | `VERIFIED` | `UNIMPLEMENTED` | Baseline `2024-07-01` FAIL must not be represented as permanent scheme-wide ineligibility. |

### Domain 3: Income and NFSA/SFSS Conditions

| Parameter | Manifest Slot / Field | Source ID & Printed Page | Supporting Statutory Wording | Statutory Status | Internal Status | Contract & Implementation Implication |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **NFSA / SFSS Coverage** | `ration_card.category` | `SRC-SUB-GUIDELINES-2024` §5.1(b), p. 4; `SRC-SUB-GAZETTE-2024` §3.1(b), p. 2; `SRC-SUB-SOP-2024` §§4, 4.2–4.3, pp. 5–6 | Covered under NFSA / SFSS. | `VERIFIED` | `IMPLEMENTED` (Slot mapping only) | No FS&CW database API. Never PASS/FAIL from declaration or OCR alone. |
| **Gross Annual Family Income Ceiling** | No active rule | `SRC-SUB-GUIDELINES-2024` §5.1(b), p. 4; `SRC-SUB-GAZETTE-2024` §3.1(b), p. 2 | Non-NFSA/SFSS woman may apply if gross annual family income $\le$ ₹2,50,000/-. | `VERIFIED` (conditional) | `UNIMPLEMENTED` | `numeric_cap` unactivated. Conditional on non-NFSA/SFSS status. |
| **Annexure 3 Self-Declaration** | `application_form` / `income_certificate` | `SRC-SUB-SOP-2024` §2, p. 3; Annexure 3, p. 15 | Self-declaration form for gross annual family income. | `VERIFIED_WITH_LIMITATIONS` | `IMPLEMENTED` (Slot mapping only) | Self-declaration is not proof of eligibility. |

### Domain 4: Exclusion Conditions (Guidelines §5.2 / Gazette §3.2)

| Parameter | Manifest Slot | Source ID & Printed Page | Supporting Statutory Wording | Statutory Status | Internal Status | Contract & Implementation Implication |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Family Definition Incorporation** | None | Guidelines §5.2, p. 4; Gazette §3.2, p. 3 | Family defined as in NFSA / SFSS. | `VERIFIED` | `UNIMPLEMENTED` | Express statutory incorporation clause. |
| **Underlying NFSA/SFSS Family Composition** | None | NFSA 2013 / SFSS Operational Rules | Underlying ration household membership rules. | `REQUIRES_STATUTORY_SOURCE_VERIFICATION` | `UNIMPLEMENTED` | No household composition model in schema. |
| **Financial Assistance Threshold** | None | Guidelines §5.2(a), p. 4; Gazette §3.2(a), p. 2 | Assistance $\ge$ ₹1,500/mo or ₹18,000/yr under State/Central scheme. | `VERIFIED` | `UNIMPLEMENTED` | No IFMS/DBT ledger API. |
| **MP / MLA Exclusion** | None | Guidelines §5.2(b)(i), p. 4; Gazette §3.2(b)(i), p. 2 | Current or former MP or MLA. | `VERIFIED` | `UNIMPLEMENTED` | No external registry lookup. |
| **Income Tax Payee** | None | Guidelines §5.2(b)(ii), p. 4; Gazette §3.2(b)(ii), p. 2 | An Income Tax payee. | `VERIFIED` | `UNIMPLEMENTED` | No CBDT PAN-Aadhaar API. |
| **PRI / ULB Elected Representatives** | None | Guidelines §5.2(b)(iii), p. 4; Gazette §3.2(b)(iii), p. 2 | Elected representative in ULB/PRI (except Ward Members & Councillors). | `VERIFIED` | `UNIMPLEMENTED` | No SEC registry API. |
| **Govt Employment & Pensions (Proviso)** | None | Guidelines §5.2(b)(iv), p. 4; Gazette §3.2(b)(iv), p. 3 | Regular/contractual employee or pensioner; proviso allows honorarium workers such as ASHA, AWWs, CRPs, MBKs, outsourced workers. | `VERIFIED` (AWW); `UNVERIFIED` in statutory proviso / `VERIFIED_WITH_LIMITATIONS` in SOP §10(f) (AWH) | `UNIMPLEMENTED` | Zero automated employment rules. See `SUBHADRA_AWW_AWH_STATUTORY_CLARIFICATION.md`. |
| **Govt Appointed Representatives** | None | Guidelines §5.2(b)(v), p. 4; Gazette §3.2(b)(v), p. 3 | Elected / nominated / appointed representative in Govt Dept/Undertaking/Board. | `VERIFIED` | `UNIMPLEMENTED` | No public board registry API. |
| **4-Wheeler Motor Vehicles** | None | Guidelines §5.2(b)(vi), p. 4; Gazette §3.2(b)(vi), p. 3 | Owner of 4-wheeler except tractors, mini-trucks, small commercial/light goods vehicles. | `VERIFIED` | `UNIMPLEMENTED` | No Vahan API. |
| **Agricultural Land Ceiling** | None | Guidelines §5.2(c), p. 4; Gazette §3.2(c), p. 3 | >5 acres irrigated or >10 acres un-irrigated land. | `VERIFIED` | `UNIMPLEMENTED` | No Bhulekh RoR API. |

### Domain 5: Aadhaar & Banking Requirements

| Parameter | Manifest Slot / Field | Source ID & Printed Page | Supporting Statutory Wording | Statutory Status | Internal Status | Contract & Implementation Implication |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Mandatory Aadhaar Possession** | `aadhaar_card` (`required: false`) | Gazette §5(a)(i), p. 4; Guidelines §7(a)(i), p. 5; SOP §2, p. 3 | Applicant must have Aadhaar card/number in her own name. | `VERIFIED` | `IMPLEMENTED` (Optional slot; `RULE-SUB-DOC-01` removed) | Absent optional scan does NOT emit `Status.MISSING` / `NOT_READY`; dependent rules abstain via `Raw.INDETERMINATE` $\to$ `Status.REVIEW` / `ReasonCode.INSUFFICIENT_DATA` (`NEEDS_CHECKS`). |
| **Aadhaar-Linked Mobile Number** | None | Gazette §5(a)(ii), p. 4; Guidelines §7(a)(ii), p. 5; SOP §2, p. 3 | Mobile number linked with Aadhaar card. | `VERIFIED` | `UNIMPLEMENTED` | OCR cannot verify mobile linkage. |
| **e-KYC Completion & Method** | None | Gazette §4(g), p. 3; Guidelines §6(g), p. 5; SOP §4.1, p. 6 | Self-certification + e-KYC (biometric/iris/fingerprint/face-auth). | `VERIFIED` | `UNIMPLEMENTED` | OCR cannot verify e-KYC completion. |
| **Applicant Legal Name Visibility** | `aadhaar_card.applicant_name` | SOP §2, p. 3; SOP §4.1, p. 6 | Legal name visible against Aadhaar e-KYC record. | `VERIFIED` | `IMPLEMENTED` (`RULE-SUB-FLD-01`) | `field_present` (`max_severity: REVIEW`); absent/unreadable doc or blank field $\to$ `Raw.INDETERMINATE` $\to$ `Status.REVIEW` / `ReasonCode.INSUFFICIENT_DATA`. |
| **Single-Holder Aadhaar/DBT Account & APBS** | None | Gazette §1(e), p. 1; §5(a)(iii), p. 4; Guidelines §§3(e), 7(a)(iii), pp. 3, 5 | DBT via APBS to single-holder Aadhaar-enabled, DBT-enabled account. | `VERIFIED` (mandate); `REQUIRES_STATUTORY_SOURCE_VERIFICATION` (NPCI procedure) | `UNIMPLEMENTED` | Cannot verify NPCI mapper or DBT seeding via OCR. |
| **Bank Passbook Upload & Name Comparison** | `bank_passbook.applicant_name` | Internal DocuReady Advisory Slot | Optional upload (`required: false`) + `match_across` (`RULE-SUB-NAME-01`, `max_severity: REVIEW`). | `UNVERIFIED` as statutory mandate | `INTERNAL_CONTRACT_VERIFIED` / `IMPLEMENTED` | Advisory consistency heuristic only. |

### Domain 6: Historical Intake Window & Reporting

| Parameter | Manifest Field | Source ID & Printed Page | Statutory Status | Internal Status | Contract & Implementation Implication |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Scheme Duration** | None | Gazette §2(a), p. 2 (FY 2024–25 to FY 2028–29) | `VERIFIED` | `NOT_APPLICABLE` | 5-year scheme duration. |
| **Historical Demo Snapshot Metadata** | `effective` (`2024-09-05` to `2025-03-31`) | `SRC-SUB-INTAKE-WINDOW` | `UNVERIFIED` as official close date | `INTERNAL_CONTRACT_VERIFIED` | Metadata only; not enforced by engine. Age determinism uses `age_reference_date`. |
| **Reported `01-04-2027` Reopening** | None | `SRC-SUB-ANNOUNCEMENT-2026-09-16`; `SRC-SUB-REOPENING-NOTICE-2027` | `UNVERIFIED` (`supports_rule: false`) | `NOT_APPLICABLE` | Context only; no rule or effective-date change authorized. |
| **Historical Demo Disclaimer** | `pack_status: demo_snapshot` | PO-approved wording (`fe73c4d`) | `NOT_APPLICABLE` | `IMPLEMENTED` | `PackExecutionEngine` + `exporter.py` emit `"DEMO SNAPSHOT — FY 2024–25 REFERENCE MATERIALS"` in Markdown & JSON. |

---

## 4. Exact Schema & Primitive Contract Mapping

- **Canonical Python Enums (`src/docuready/domain/enums.py`):**
  - `Readiness`: `NOT_READY`, `NEEDS_CHECKS`, `NO_ISSUES_FOUND` (`REJECTED` and `READY` do not exist).
  - `EvidenceState`: `VERIFIED`, `PROVISIONAL`, `UNCERTAIN` (transitional strings `VERIFIED_TEXT`, `OCR_EXTRACTED`, `AMBIGUOUS`, `LOW_CONFIDENCE`, `NOT_FOUND`, `UNREADABLE`, `CONFLICTING` normalized by `normalize_evidence_state()`).
  - `Raw`: `SATISFIED`, `VIOLATED`, `INDETERMINATE`, `DOC_ABSENT`, `EXEMPT`.
  - `Status`: `FAIL`, `WARN`, `REVIEW`, `PASS`, `MISSING`, `NOT_APPLICABLE`.
  - `MaxSeverity`: `FAIL`, `WARN`, `REVIEW`.
  - `ReasonCode`: `DEFECT_CONFIRMED`, `DEFECT_PROBABLE`, `EVIDENCE_UNCERTAIN`, `CONFIRMED_OK`, `CANNOT_CONFIRM`, `INSUFFICIENT_DATA`, `DOC_ABSENT`, `ADVISORY_RULE_CAP`, `WRONG_DOCUMENT_TYPE`.
  - `MatchGrade`: `EXACT`, `COMPATIBLE`, `CONFLICT`, `AMBIGUOUS`.
- **Activated Subhadra Primitives (3 of 9 engine primitives):**
  1. `field_present` (`RULE-SUB-FLD-01`, `max_severity: REVIEW`)
  2. `age_on` (`RULE-SUB-AGE-01`, `max_severity: FAIL`)
  3. `match_across` (`RULE-SUB-NAME-01`, `max_severity: REVIEW`)
- **Unactivated Engine Primitives (6 of 9):** `require_document`, `within_validity`, `numeric_cap`, `numeric_consistency`, `enum_in`, `legible`.
- **Cross-Pack Regression Requirement:** Shared changes to `eval_field_present` are covered by `tests/test_primitives.py`, `tests/integration/test_pack_matrix.py` (`generic.demo`), and `tests/test_subhadra_pack.py` (`odisha.subhadra`).

---

## 5. Implementation Boundary and Gate

| Area | Current Position | Gate |
|---|---|---|
| Source registry / official source facts | Three official PDFs retain `retrieved_on: 2026-11-21`; re-verified `2026-11-22`. Secondary announcement & placeholder recorded separately as `UNVERIFIED` / `supports_rule: false`. | Matrix review |
| Legal parameter verification | Verified / unverified states recorded above; PO confirmed Akriti's agreement on 27 Nov 2026. | T3.3 final acceptance pending |
| Aadhaar digital-upload semantics | `RULE-SUB-DOC-01` removed in `2024.1.1`; `aadhaar_card.required: false` retained. | Implemented in PR #88 (`7ccf274`) |
| `RULE-SUB-FLD-01` missing-source behaviour | `eval_field_present()` corrected; cross-pack regression tests added. | Implemented in PR #88 (`7ccf274`) |
| Age §3.1(e) | Legal provision verified; year-aware model unresolved. | Specification approval first |
| Income / NFSA-SFSS / external exclusions | Intentionally not executable without trusted verification. | Remain deferred |
| AWW / AWH | AWW verified exception; AWH unverified in Gazette/Guidelines (`SOP §10(f)` summary enquiry only). | No AWH rule |
| Report exporter | PO wording decision resolved (`DEMO SNAPSHOT — FY 2024–25 REFERENCE MATERIALS`); production exporter emits disclosure for `demo_snapshot` packs. | Wording resolved by PO; T3.3 final acceptance pending |
| 16-09-2026 reopening announcement | Secondary report recorded as `UNVERIFIED` / `supports_rule: false`; official notice not produced. | No rule/effective-date change |
