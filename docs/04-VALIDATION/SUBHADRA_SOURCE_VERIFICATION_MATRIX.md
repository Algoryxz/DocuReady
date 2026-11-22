# SUBHADRA v1.4 — Parameter-Level Source Verification Matrix

**Task:** T3.3 — Odisha SUBHADRA scheme pack  
**Owner:** Susmita — Domain Rules, Evidence & Evaluation  
**Version:** v1.4 (independent-review revision)  
**Prepared:** 22 November 2026  
**Review status:** Submitted for Akriti's independent review; **not approved**  
**Implementation gate:** HOLD — no pack, rule, schema, exporter, or test implementation changes authorized by this document.

> This matrix separates (1) what the Government source establishes, (2) what DocuReady can safely verify from supplied evidence, and (3) what is actually implemented. A verified legal requirement is not automatically an automatable rule. This is a document-verification aid, not an eligibility decision or Government determination.

## 1. Source register and provenance

Retrieval date for all three official PDFs below: **22 November 2026**. URLs were opened and checked against the Government of Odisha W&CD Department website on that date.

| Source ID | Exact title / identifier | Issuing authority | Document / issue date | Official URL | Evidence location |
|---|---|---|---|---|---|
| SRC-SUB-GUIDELINES-2024 | SUBHADRA Guidelines; Letter No. 19188/WCD; File No. WCD-ICDS-M-SCHM-0003-2024 | Department of Women & Child Development, Government of Odisha; forwarded by Joint Secretary to Government | Guidelines: August 2024; forwarding letter dated 29-08-2024 | https://wcd.odisha.gov.in/sites/default/files/2025-06/148.%20Lt.%20No.%2019188Dt.%2029.08.2024%20Circulation%20of%20Subhadra%20guideline%20English.pdf | Printed pp. 4–5, §§5.1–5.2; p. 5, §§6–7 |
| SRC-SUB-GAZETTE-2024 | The Odisha Gazette Extraordinary No. 1637; Resolution No. 19898—WCD-SUBH-SCHM-0008/2024/WCD | Department of Women & Child Development, Government of Odisha | 05-09-2024 | https://wcd.odisha.gov.in/sites/default/files/2025-07/1637%20Gazette%20Resolution%20ENGLISH_0.pdf | Printed p. 2, §§2(a), 3.1(a)–(e); pp. 2–3, §3.2; p. 4, §5 |
| SRC-SUB-SOP-2024 | Standard Operating Procedure (SOP) for implementation of SUBHADRA; Letter No. 26139/WCD; No. WCD-SUBH-SCHM-0029-2024 | Department of Women & Child Development, Government of Odisha; forwarded by Joint Secretary to Government | SOP cover: October 2024; forwarding letter dated 11-11-2024 | https://wcd.odisha.gov.in/sites/default/files/2025-07/26139%20Dt.%2011.11.2024%20SOP%20Subhadra%20English.pdf | Printed p. 3, §2; p. 6, §§4–4.3; p. 7, §4.4; printed p. 15, Annexure 3 |

**Authority hierarchy used:** Gazette Resolution is the primary published scheme resolution; Guidelines supply operational eligibility and ineligibility criteria; SOP supplies application, assisted-submission, e-KYC, scrutiny and field-verification procedures. Where the documents describe different stages, the matrix records the distinction instead of silently treating an operational process as a new statutory criterion.

## 2. Parameter-level verification matrix

Status vocabulary:
- **VERIFIED** — the cited official source expressly establishes the requirement or rule.
- **PARTIALLY VERIFIED** — the source establishes part of the proposition, but scope or operational interpretation remains unresolved.
- **UNVERIFIED** — no adequate authoritative evidence has been established for the specific proposition.
- **NOT AUTOMATABLE** — legal requirement may be verified, but the current DocuReady inputs/integrations cannot safely determine it.
- **DEFERRED** — deliberately not implemented pending trusted evidence, product-owner approval, or a suitable primitive.

| Parameter / rule area | Official source, clause and printed page | Supporting wording / faithful summary | Statutory verification | Safe automation | Proposed primitive / severity cap / failure behaviour | Current implementation implication |
|---|---|---|---|---|---|---|
| Odisha residence | Guidelines §5.1(a), p. 4; Gazette §3.1(a), p. 2 | Applicant must be a resident of Odisha. | VERIFIED | NOT AUTOMATABLE from an applicant declaration or address text alone. A document address is not conclusive proof of residence. | No eligibility FAIL primitive. If a supported residence document is supplied, extraction may be informational; otherwise REVIEW / INSUFFICIENT_DATA. Severity cap REVIEW. | Do not claim residence has been verified from OCR or self-declaration. No automated rejection. |
| NFSA / SFSS household coverage | Guidelines §5.1(b), p. 4; Gazette §3.1(b), p. 2; SOP §§4, 4.2–4.3, pp. 5–6 | Applicants covered under NFSA/SFSS satisfy this branch; applications are separated and checked against Government databases by the designated process. | VERIFIED | NOT AUTOMATABLE without trusted, current Government database verification and reliable family linkage. Applicant declaration or OCR of a ration card alone must not establish database status. | No executable eligibility primitive until trusted integration exists. REVIEW / INSUFFICIENT_DATA; severity cap REVIEW; never PASS or FAIL from applicant declaration alone. | Intentionally unimplemented. Preserve omission of an income-exemption or coverage verdict based only on applicant-declared NFSA/SFSS. |
| Family-income ceiling, conditional branch | Guidelines §5.1(b), p. 4; Gazette §3.1(b), p. 2; SOP Annexure 3, p. 15 | A woman from a family without an NFSA/SFSS card may apply where family income does not exceed ₹2.50 lakh. SOP Annexure 3 is a self-certification/field-verification artefact, not an independent trusted income database. | VERIFIED as a conditional statutory criterion; applicability for an individual applicant is not verified without trusted coverage evidence. | NOT AUTOMATABLE as an eligibility decision using applicant declaration, uploaded income certificate, or OCR alone. | Extraction/mapping may be informational only. No income-ceiling PASS/FAIL rule. Severity cap REVIEW; unknown coverage or income must remain REVIEW / INSUFFICIENT_DATA, not NOT_APPLICABLE. | Keep income ceiling out of executable parameters/rules until trusted coverage and income evidence are available. |
| Age: baseline FY 2024–25 | Gazette §3.1(c)–(d), printed p. 2; Guidelines §5.1(c)–(d), p. 4 | Age must be at least 21 and below 60 on the qualifying date. For FY 2024–25 the date is 01-07-2024; Aadhaar-recorded DOB is the stated final DOB basis. | VERIFIED | SAFELY AUTOMATABLE only for the FY 2024–25 baseline when a legible, reliable Aadhaar DOB is available and date parsing is unambiguous. | `age_on` using DOB, reference date 2024-07-01, lower bound 21 inclusive and upper bound 60 exclusive. FAIL may be used only for the scoped FY 2024–25 baseline after reliable DOB extraction; missing/uncertain DOB => REVIEW / INSUFFICIENT_DATA. | Existing age parameters represent this historical baseline only. They must not be described as a current 2026 age test or a permanent scheme-wide determination. |
| Age transition: turns 21 after 01-07-2024 | Gazette §3.1(e), printed p. 2; Guidelines §5.1(e), p. 4 | A woman attaining 21 after 01-07-2024 receives ₹10,000 per year only for the remaining years of the scheme period. | VERIFIED | NOT safely handled by a single fixed-date age rule. Requires year-aware transition calculation and a clearly defined scheme-year model. | Proposed separate transition logic, not an extension of a blanket FAIL. Until year-aware calculation is specified and reviewed: REVIEW / TRANSITION_REQUIRES_YEAR_SCOPE; severity cap REVIEW. | Matrix must explicitly preserve future-year entitlement. An FY 2024–25 baseline age failure must not be represented as permanent ineligibility for all remaining scheme years. |
| Age transition: turns 60 after 01-07-2024 | Gazette §3.1(e), printed p. 2; Guidelines §5.1(e), p. 4 | Women who complete 60 after 01-07-2024 do not receive benefits for the remaining years of the scheme period. | VERIFIED | NOT safely handled by a single fixed-date age rule for all scheme years. | Requires year-aware benefit-period treatment. Until approved: REVIEW / TRANSITION_REQUIRES_YEAR_SCOPE; severity cap REVIEW. Do not infer or invent a retrospective recovery or closing-date rule. | Distinguish baseline FY 2024–25 age qualification from subsequent-year entitlement. |
| Aadhaar possession / own-name requirement | Gazette §5(a)(i), printed p. 4; Guidelines §7(a)(i)–(b), p. 5; SOP §2(c), p. 3 | Applicant must have Aadhaar card/Aadhaar number in her own name; SOP requires applicants to carry the card/number for assisted submission and describes Aadhaar enrolment/update assistance. | VERIFIED | Physical possession cannot be inferred from absence of an uploaded scan. OCR can inspect an uploaded copy but cannot determine whether an applicant physically holds Aadhaar. | Do not treat a missing digital upload as statutory absence. If scan slot is absent: REVIEW / DIGITAL_EVIDENCE_NOT_SUPPLIED, non-blocking, severity cap REVIEW. If supplied but unreadable: REVIEW / INSUFFICIENT_DATA. No FATAL, statutory FAIL, or Government-rejection claim. | Separate statutory Aadhaar possession from DocuReady's optional digital evidence input. The current MISSING/FATAL/NOT_READY outcome on scan absence is not supported as a legal conclusion and must be reconciled before implementation approval. |
| Aadhaar-linked mobile and e-KYC | Gazette §5(a)(ii), printed p. 4; Guidelines §7(a)(ii), p. 5; SOP §2(f), p. 3 and §4.1, p. 6 | Aadhaar-linked mobile is required at submission; SOP describes e-KYC by biometric method (iris/fingerprint) or facial recognition, and addresses prior OTP e-KYC. | VERIFIED | NOT AUTOMATABLE from a document scan. The system has no verified e-KYC transaction response in the supplied packet. | No OCR-based PASS/FAIL. Missing proof => REVIEW / EXTERNAL_VERIFICATION_REQUIRED; severity cap REVIEW. | Do not claim e-KYC completion or Aadhaar-mobile linkage based on the presence of an Aadhaar scan. |
| Single-holder Aadhaar-enabled, DBT-enabled bank account | Gazette §§1(e), 5(a)(iii), printed pp. 1 and 4; Guidelines §§3(e), 7(a)(iii), pp. 3 and 5 | Benefit transfer is to a single-holder account in the beneficiary's name that is Aadhaar-enabled and DBT-enabled. | VERIFIED | Partially automatable: OCR can read visible name/account details; it cannot establish single-holder status, Aadhaar seeding, DBT enablement or NPCI mapper status from a passbook image alone. | Existing `match_across` may compare visible names as an advisory check only, capped at REVIEW. External bank/DBT status => REVIEW / EXTERNAL_VERIFICATION_REQUIRED. No FAIL from passbook absence or OCR mismatch alone. | Keep `RULE-SUB-NAME-01` advisory. Do not claim the passbook proves DBT readiness. |
| Government pension / assistance threshold | Guidelines §5.2(a), p. 4; Gazette §3.2(a), printed p. 2 | Receipt of State/Central Government assistance such as pension or scholarship at ₹1,500/month or ₹18,000/year or more is an exclusion. | VERIFIED | NOT AUTOMATABLE without trusted benefit/pension data and reliable identity/family resolution. | No declaration-only exclusion rule. REVIEW / EXTERNAL_VERIFICATION_REQUIRED; severity cap REVIEW. | Intentionally unimplemented absent trusted Government data. |
| Family-member and public-office / employment exclusions | Guidelines §5.2(b)(i)–(v), pp. 4–5; Gazette §3.2(b)(i)–(v), printed pp. 2–3 | Exclusions cover specified MP/MLA, income-tax payer, elected representative, government employment/pension, and nominated/appointed representative conditions; some are scoped to applicant or family members. | VERIFIED, subject to exact category and family-scope interpretation | NOT AUTOMATABLE without authoritative, current datasets and a reliable statutory family relationship model. | No self-declaration-only FAIL. REVIEW / EXTERNAL_VERIFICATION_REQUIRED; severity cap REVIEW. | Keep external exclusions unimplemented. Do not assert the applicant has passed them because no data was found in an uploaded document. |
| Honorarium exception — AWW | Guidelines §5.2(b)(iv), p. 4; Gazette §3.2(b)(iv), printed p. 3 | The Gazette expressly lists Anganwadi Worker among honorarium workers considered if otherwise eligible. | VERIFIED for AWW | Not a standalone automated pass: role and honorarium status require authoritative evidence and the rest of eligibility still applies. | If a role document is present, informational extraction only; REVIEW cap. No FAIL solely for AWW status. | Preserve the express AWW exception. Do not generalize the exception to unlisted roles without evidence. |
| Honorarium exception — AWH | No specific Gazette or Guidelines wording establishing AWH was identified in the cited official sources. | AWH is not expressly named in the identified honorarium-exception wording. Absence from this wording is not proof of exclusion or inclusion under another authoritative order. | UNVERIFIED | NOT AUTOMATABLE / unresolved. | No rule. Status UNVERIFIED; no PASS or FAIL; REVIEW pending separate authoritative evidence. | Keep AWH explicitly UNVERIFIED. Do not silently map AWH to AWW. |
| Four-wheeler ownership and listed exceptions | Guidelines §5.2(b)(vi), p. 5; Gazette §3.2(b)(vi), printed p. 3 | Ownership of a four-wheeler is an exclusion, subject to stated exceptions such as tractors, mini-trucks and specified light goods vehicles. | VERIFIED | NOT AUTOMATABLE without trusted vehicle-registration and ownership/family linkage data; applicant declaration is insufficient. | No declaration-based rule. REVIEW / EXTERNAL_VERIFICATION_REQUIRED; severity cap REVIEW. | Intentionally unimplemented. |
| Agricultural land thresholds and family definition | Guidelines §5.2(c) and note, p. 5; Gazette §3.2(c) and note, printed p. 3 | Exclusion applies above five acres irrigated or ten acres non-irrigated; family definition is tied to NFSA/SFSS. | VERIFIED | NOT AUTOMATABLE without trusted land records, land classification, family linkage and current ownership evidence. | No declaration-only rule. REVIEW / EXTERNAL_VERIFICATION_REQUIRED; severity cap REVIEW. | Intentionally unimplemented. |
| Application window / 31-03-2025 | Gazette §2(a), printed p. 2; Guidelines §4, p. 4 | The Gazette establishes the scheme period FY 2024–25 to FY 2028–29. The cited sources do not establish 31-03-2025 as the official application closing date. | Scheme duration VERIFIED; 31-03-2025 as official closing date UNVERIFIED / NOT ESTABLISHED by these sources. | Not an applicant-document primitive. | No closing-date validation rule. Any 2025-03-31 value must be explicitly scoped to internal demo/evaluation snapshot metadata, not a Government deadline. | Keep `effective.to` or snapshot metadata clearly labelled as a historical demo boundary only. Remove any banner wording that states “intake window closed” as a Government fact unless a separate date-specific Government notice is produced. |

## 3. Specific rule-level review findings

### RULE-SUB-DOC-01 — Aadhaar document slot

- **Legal fact:** Aadhaar card/number in the applicant's own name is a statutory requirement (Gazette §5(a)(i)).
- **Process fact:** SOP §2 requires the applicant to carry the physical Aadhaar card/Aadhaar number and Aadhaar-linked mobile for assisted submission; it also provides assistance for Aadhaar enrolment/update. It does not establish that the applicant must upload a digital scan to DocuReady.
- **Boundary:** The digital scan is an optional DocuReady input used only for OCR-based pre-checking. Its absence cannot prove the applicant lacks Aadhaar or is legally ineligible.
- **Proposed handling:** Missing scan => non-blocking REVIEW / DIGITAL_EVIDENCE_NOT_SUPPLIED; unreadable scan => REVIEW / INSUFFICIENT_DATA. Severity cap REVIEW. No FATAL, statutory FAIL, or claim of Government rejection.
- **Review blocker:** Existing branch test asserts `Status.MISSING`, `Severity.FATAL`, and `Readiness.NOT_READY` for an omitted Aadhaar upload, despite also asserting no statutory FAIL and explanatory remediation. This is internally misleading at the readiness/severity layer and requires a product-level decision before any code change.

### RULE-SUB-FLD-01 — applicant-name field presence

- A `field_present` check can only establish that a field was extracted from available evidence; it cannot establish that a field exists when its source document is absent.
- **Required missing-document behaviour:** If Aadhaar is absent, the rule must abstain with REVIEW / INSUFFICIENT_DATA (or produce no independent positive finding, according to the agreed engine contract). It must not emit PASS or field-present messaging. If the document exists but the name is absent/illegible, REVIEW is appropriate. A clear extracted name may satisfy field presence, but that is not an identity/e-KYC verification.
- **Severity cap:** REVIEW. No statutory FAIL.
- **Evidence test required after approval:** cover absent Aadhaar document, present-but-empty name field, unreadable document, and a clearly extracted name. Assert no PASS or misleading “field present” result for missing evidence.

### Age transition and baseline scope

- Keep the fixed 01-07-2024 date only for the FY 2024–25 baseline rule.
- Add an explicit specification for §3.1(e) before any implementation: a person turning 21 after the baseline date may qualify for the remaining scheme years; a person turning 60 after the baseline date does not receive benefits for the remaining years.
- Do not convert the baseline FAIL into a permanent, scheme-wide ineligibility claim.
- Do not calculate later-year entitlements until scheme-year boundaries and the exact age-transition evaluation contract are approved.

### Report header / exporter test

- Current test `test_subhadra_report_header_proposed_format` constructs a proposed banner string inside the test. It does not call the production report exporter and therefore does not prove that an actual report contains the banner.
- The token “intake window closed” is not supported as an official closing-date claim by the cited Gazette, Guidelines or SOP.
- **Required test design after the relevant owner approves the interface:** invoke the real report-export function with the Subhadra demo snapshot and assert on the generated report bytes/text; assert the historical-snapshot disclaimer; assert that no official application deadline or Government closure is claimed.
- This is an evidence/test gap, not authorization for T3.3 to modify another owner's exporter. Coordinate the test seam with the exporter owner.

## 4. Explicit non-claims and unresolved evidence

1. DocuReady does not determine final Subhadra eligibility, approve/reject applicants, or replace Government database checks, field enquiry, committee scrutiny or e-KYC.
2. An absent Aadhaar upload does not establish absence of Aadhaar possession.
3. An Aadhaar scan does not prove successful e-KYC or Aadhaar-linked mobile status.
4. A passbook image does not prove single-holder account status, Aadhaar seeding, DBT enablement or NPCI mapper status.
5. Applicant declarations/OCR do not verify NFSA/SFSS coverage, family income, pension, tax status, public office/employment, vehicle ownership or landholding.
6. The ₹2.50 lakh income criterion is conditional on the family not having NFSA/SFSS coverage; it must not be applied or waived based only on applicant declaration.
7. AWW is expressly named in the honorarium exception; AWH remains UNVERIFIED pending a separate authoritative source.
8. 31-03-2025 is not established by the cited official sources as an application closing date.
9. The age-transition provision in §3.1(e) is verified but is not fully represented by a single fixed-date age rule.
10. No new exclusion rule, severity escalation, primitive, schema field or exporter behaviour is authorized by this matrix.

## 5. Implementation boundary and gate

| Area | Current position | Gate |
|---|---|---|
| Source registry / official source facts | Three primary Government sources identified and cross-checked | Matrix review |
| Legal parameter verification | Verified / unverified states recorded above | Akriti review |
| Aadhaar digital-upload semantics | Current implementation/test behaviour requires reconciliation | No code change before agreement |
| RULE-SUB-FLD-01 missing-source behaviour | Test gap identified | No code change before agreement |
| Age §3.1(e) | Legal provision verified; year-aware model unresolved | Specification approval first |
| Income / NFSA-SFSS / external exclusions | Intentionally not executable without trusted verification | Remain deferred |
| AWW / AWH | AWW verified exception; AWH unverified | No AWH rule |
| Report exporter | Existing test is string-construction only; production exporter not tested | Coordinate with exporter owner |
| 31-03-2025 | Demo metadata only; not an official closing date | No official deadline claim |
| Implementation PR / merge | Not opened / not authorized by this matrix | Wait for Akriti's explicit written agreement |

**T3.3 owner:** Susmita. This document preserves T3.3 ownership and does not transfer acceptance criteria or authorize changes outside the T3.3 boundary.

**Requested review decision:** Akriti to review this matrix and either (a) explicitly agree to the evidence and implementation boundaries, or (b) return specific row-level corrections. No implementation work proceeds until explicit agreement is recorded.
