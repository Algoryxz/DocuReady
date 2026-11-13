"""
Deterministic, Explainable Validation Engine for DocuReady MVP
Implements statutory rules, cross-document entity comparisons, and provenance-linked finding generation.
"""

import re
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple, Any
from src.models import (
    DocumentType, ExtractedDocument, ExtractedField, EvidenceProvenance,
    Finding, FindingStatus, Severity, AuditResult, EvidenceState
)
from src.normalizer import (
    compare_names, parse_and_normalize_date, normalize_cert_number,
    validate_ifsc_code
)
from src.safety_layer import DecisionSafetyLayer


class SchemeConfig:
    def __init__(
        self,
        name: str = "Odisha Post-Matric Scholarship (SC/ST/OBC)",
        target_state: str = "ODISHA",
        income_ceiling: float = 250000.0,
        min_academic_percentage: float = 50.0,
        sc_st_cutoff_policy: str = "PASS_ONLY",  # "PASS_ONLY" (Post-Matric), "RELAXED_50" (Medhabruti), "STRICT" (PM-YASASVI)
        income_cert_validity_years: int = 3,
        mandatory_documents: Optional[List[DocumentType]] = None
    ):
        self.name = name
        self.target_state = target_state.upper()
        self.income_ceiling = income_ceiling
        self.min_academic_percentage = min_academic_percentage
        self.sc_st_cutoff_policy = sc_st_cutoff_policy
        self.income_cert_validity_years = income_cert_validity_years
        self.mandatory_documents = mandatory_documents or [
            DocumentType.INCOME_CERT,
            DocumentType.CASTE_CERT,
            DocumentType.RESIDENCE_CERT,
            DocumentType.MARKSHEET,
            DocumentType.BANK_PASSBOOK,
            DocumentType.APPLICATION_FORM
        ]


class DocuReadyValidator:
    """Validates multi-document applicant packets against statutory rules and cross-document facts."""

    def __init__(self, scheme_config: Optional[SchemeConfig] = None, audit_date: Optional[date] = None):
        self.scheme = scheme_config or SchemeConfig()
        # Reference date set to Nov 13, 2026
        self.audit_date = audit_date or date(2026, 11, 13)
        self.safety_layer = DecisionSafetyLayer()

    def validate_packet(self, packet_id: str, documents: Dict[DocumentType, ExtractedDocument]) -> AuditResult:
        findings: List[Finding] = []
        score = 100

        # ----------------- 1. MISSING MANDATORY DOCUMENTS CHECK -----------------
        for req_doc in self.scheme.mandatory_documents:
            doc = documents.get(req_doc)
            if not doc or doc.status == "MISSING":
                findings.append(Finding(
                    rule_id="RULE-DOC-01",
                    rule_name="Mandatory Document Completeness",
                    status=FindingStatus.FAIL,
                    severity=Severity.FATAL,
                    penalty=35,
                    field="MANDATORY_DOCUMENT",
                    documents_involved=[req_doc.value],
                    message=f"Mandatory document '{req_doc.value}' is missing from the application packet.",
                    evidence=[],
                    remediation=f"Obtain and upload a valid {req_doc.value} before portal submission.",
                    statutory_reference="OSSP Guidelines 2024-25, Section 3.1 & NSP Common Framework"
                ))
                score -= 35

        # ----------------- 2. UNREADABLE / SCAN QUALITY CHECK -----------------
        for d_type, doc in documents.items():
            if doc and doc.status in ["UNREADABLE", "CORRUPTED"]:
                findings.append(Finding(
                    rule_id="RULE-DOC-02",
                    rule_name="Document Legibility & Evidence Integrity",
                    status=FindingStatus.UNKNOWN,
                    severity=Severity.CRITICAL,
                    penalty=25,
                    field="SCAN_QUALITY",
                    documents_involved=[d_type.value],
                    message=f"Document '{d_type.value}' is unreadable or corrupted. Clear evidence cannot be extracted.",
                    evidence=[
                        EvidenceProvenance(
                            document_type=d_type.value,
                            file_name=doc.file_path,
                            raw_snippet="[UNREADABLE SCAN / INSUFFICIENT EVIDENCE]"
                        )
                    ],
                    remediation="Re-scan the document with at least 300 DPI flatbed scanner and ensure good lighting.",
                    statutory_reference="NSP Upload Guidelines & IT Act 2000 Section 6A"
                ))
                score -= 25

        # Helper to get field safely
        def get_f(dt: DocumentType, fname: str) -> Optional[ExtractedField]:
            d = documents.get(dt)
            if d and d.status == "VALID":
                return d.fields.get(fname)
            return None

        # ----------------- 3. MISSING MANDATORY FIELDS CHECK -----------------
        mandatory_field_map = {
            DocumentType.INCOME_CERT: ["applicant_name", "annual_income", "issue_date", "certificate_no"],
            DocumentType.CASTE_CERT: ["applicant_name", "caste_category", "certificate_no"],
            DocumentType.RESIDENCE_CERT: ["applicant_name", "state", "certificate_no"],
            DocumentType.MARKSHEET: ["applicant_name", "dob", "percentage"],
            DocumentType.BANK_PASSBOOK: ["applicant_name", "account_no", "ifsc"],
            DocumentType.APPLICATION_FORM: ["applicant_name", "annual_income", "caste_category"]
        }

        for doc_type, req_fields in mandatory_field_map.items():
            doc = documents.get(doc_type)
            if doc and doc.status == "VALID":
                for mf in req_fields:
                    fld = doc.fields.get(mf)
                    if not fld or not fld.raw_value:
                        findings.append(Finding(
                            rule_id="RULE-FLD-01",
                            rule_name="Mandatory Field Completeness",
                            status=FindingStatus.FAIL,
                            severity=Severity.CRITICAL,
                            penalty=20,
                            field=mf.upper(),
                            documents_involved=[doc_type.value],
                            message=f"Mandatory field '{mf}' is missing or unextracted in {doc_type.value}.",
                            evidence=[],
                            remediation=f"Ensure that {mf} is clearly visible and legible on {doc_type.value}.",
                            statutory_reference="NSP Common Application Standards 2024"
                        ))
                        score -= 20

        # ----------------- 4. CROSS-DOCUMENT APPLICANT NAME CONSISTENCY -----------------
        name_fields: List[Tuple[DocumentType, ExtractedField]] = []
        for dt in [
            DocumentType.APPLICATION_FORM, DocumentType.INCOME_CERT,
            DocumentType.CASTE_CERT, DocumentType.RESIDENCE_CERT,
            DocumentType.MARKSHEET, DocumentType.BANK_PASSBOOK
        ]:
            f = get_f(dt, "applicant_name")
            if f and f.raw_value:
                name_fields.append((dt, f))

        # Compare each supporting document against the primary Application Form (or first doc)
        primary_dt, primary_f = name_fields[0] if name_fields else (None, None)
        divergent_docs_seen = set()

        for dt2, f2 in name_fields[1:]:
            cmp = compare_names(primary_f.raw_value, f2.raw_value)
            ev = [
                primary_f.provenance or EvidenceProvenance(document_type=primary_dt.value, file_name="", raw_snippet=primary_f.raw_value),
                f2.provenance or EvidenceProvenance(document_type=dt2.value, file_name="", raw_snippet=f2.raw_value)
            ]
            is_any_unc = primary_f.is_uncertain or f2.is_uncertain

            if cmp["status"] == "FAIL" and dt2 not in divergent_docs_seen:
                divergent_docs_seen.add(dt2)
                if is_any_unc:
                    unc_src = primary_dt.value if primary_f.is_uncertain else dt2.value
                    findings.append(Finding(
                        rule_id="RULE-NAME-UNCERTAIN",
                        rule_name="Cross-Document Name Verification (Uncertain OCR)",
                        status=FindingStatus.REVIEW,
                        severity=Severity.REVIEW,
                        penalty=10,
                        field="APPLICANT_NAME_UNCERTAIN",
                        documents_involved=[primary_dt.value, dt2.value],
                        message=f"Apparent name discrepancy between {primary_dt.value} ('{primary_f.raw_value}') and {dt2.value} ('{f2.raw_value}'), but extraction from {unc_src} has low confidence. Human review required.",
                        evidence=ev,
                        remediation="Inspect physical scan to verify whether apparent name variance is due to scanning noise or an actual discrepancy.",
                        statutory_reference="MeitY Demographic Verification Standards 2023, Clause 4.2"
                    ))
                    score -= 10
                else:
                    findings.append(Finding(
                        rule_id="RULE-NAME-01",
                        rule_name="Cross-Document Applicant Name Consistency",
                        status=FindingStatus.FAIL,
                        severity=Severity.CRITICAL,
                        penalty=25,
                        field="APPLICANT_NAME",
                        documents_involved=[primary_dt.value, dt2.value],
                        message=f"Conflicting applicant names between {primary_dt.value} ('{primary_f.raw_value}') and {dt2.value} ('{f2.raw_value}').",
                        evidence=ev,
                        remediation="Ensure the exact legal name is used across all documents or attach Gazette notification/affidavit.",
                        statutory_reference="MeitY Demographic Verification Standards 2023, Clause 4.2"
                    ))
                    score -= 25
            elif cmp["status"] == "REVIEW" and dt2 not in divergent_docs_seen:
                divergent_docs_seen.add(dt2)
                findings.append(Finding(
                    rule_id="RULE-NAME-02",
                    rule_name="Cross-Document Applicant Name Variation",
                    status=FindingStatus.REVIEW,
                    severity=Severity.REVIEW,
                    penalty=10,
                    field="APPLICANT_NAME_VARIATION",
                    documents_involved=[primary_dt.value, dt2.value],
                    message=f"Name variation detected between {primary_dt.value} ('{primary_f.raw_value}') and {dt2.value} ('{f2.raw_value}'): {cmp['notes']}.",
                    evidence=ev,
                    remediation="Verify if this abbreviation/transliteration is acceptable under local portal rules or upload self-declaration.",
                    statutory_reference="UIDAI Name Matching Standard Guidelines"
                ))
                score -= 10

        # If name fields exist and no FAIL/REVIEW was generated among primary docs, add PASS
        if len(name_fields) >= 2 and not any(f.field.startswith("APPLICANT_NAME") for f in findings):
            primary_ev = [f.provenance for _, f in name_fields[:2] if f.provenance]
            findings.append(Finding(
                rule_id="RULE-NAME-PASS",
                rule_name="Cross-Document Applicant Name Consistency",
                status=FindingStatus.PASS,
                severity=Severity.INFO,
                penalty=0,
                field="APPLICANT_NAME",
                documents_involved=[dt.value for dt, _ in name_fields],
                message="Applicant name matches consistently across all verified documents.",
                evidence=primary_ev,
                remediation="No action required.",
                statutory_reference="MeitY Demographic Verification Standards 2023"
            ))

        # ----------------- 5. CROSS-DOCUMENT DATE OF BIRTH CONSISTENCY & VALIDITY -----------------
        dob_f_app = get_f(DocumentType.APPLICATION_FORM, "dob")
        dob_f_mark = get_f(DocumentType.MARKSHEET, "dob")

        if dob_f_app and dob_f_mark:
            ev_dob = [
                dob_f_app.provenance or EvidenceProvenance(document_type="APPLICATION_FORM", file_name="", raw_snippet=dob_f_app.raw_value),
                dob_f_mark.provenance or EvidenceProvenance(document_type="MARKSHEET", file_name="", raw_snippet=dob_f_mark.raw_value)
            ]
            d1, st1, amb1 = parse_and_normalize_date(dob_f_app.raw_value)
            d2, st2, amb2 = parse_and_normalize_date(dob_f_mark.raw_value)

            if st1 == "INVALID_FORMAT" or st2 == "INVALID_FORMAT":
                findings.append(Finding(
                    rule_id="RULE-DOB-03",
                    rule_name="Date of Birth Format Validity",
                    status=FindingStatus.FAIL,
                    severity=Severity.CRITICAL,
                    penalty=25,
                    field="DOB_FORMAT",
                    documents_involved=[DocumentType.APPLICATION_FORM.value, DocumentType.MARKSHEET.value],
                    message=f"Malformed Date of Birth format: Application Form ('{dob_f_app.raw_value}') or Marksheet ('{dob_f_mark.raw_value}').",
                    evidence=ev_dob,
                    remediation="Enter Date of Birth in standardized DD/MM/YYYY format.",
                    statutory_reference="HSC Examination Board Verification Manual"
                ))
                score -= 25
            elif amb1 or amb2:
                findings.append(Finding(
                    rule_id="RULE-DOB-02",
                    rule_name="Date of Birth Ambiguity",
                    status=FindingStatus.REVIEW,
                    severity=Severity.REVIEW,
                    penalty=5,
                    field="DOB_AMBIGUITY",
                    documents_involved=[DocumentType.APPLICATION_FORM.value, DocumentType.MARKSHEET.value],
                    message=f"Ambiguous date representation detected ('{dob_f_app.raw_value}' vs '{dob_f_mark.raw_value}'). Could represent DD/MM/YYYY or MM/DD/YYYY.",
                    evidence=ev_dob,
                    remediation="Confirm whether day precedes month before final submission.",
                    statutory_reference="ISO 8601 Date Standard & NSP Portal Format Requirement"
                ))
                score -= 5
            elif d1 and d2:
                if d1 != d2:
                    if dob_f_app.is_uncertain or dob_f_mark.is_uncertain:
                        unc_doc = "APPLICATION_FORM" if dob_f_app.is_uncertain else "MARKSHEET"
                        findings.append(Finding(
                            rule_id="RULE-DOB-UNCERTAIN",
                            rule_name="Cross-Document Date of Birth (Uncertain OCR)",
                            status=FindingStatus.REVIEW,
                            severity=Severity.REVIEW,
                            penalty=10,
                            field="DATE_OF_BIRTH_UNCERTAIN",
                            documents_involved=[DocumentType.APPLICATION_FORM.value, DocumentType.MARKSHEET.value],
                            message=f"Potential Date of Birth discrepancy between Application Form ({d1}) and Marksheet ({d2}), but extraction from {unc_doc} has low OCR confidence. Human verification required.",
                            evidence=ev_dob,
                            remediation="Inspect original certificates to verify exact date of birth digits.",
                            statutory_reference="UIDAI Demographic Guidelines 2023"
                        ))
                        score -= 10
                    else:
                        findings.append(Finding(
                            rule_id="RULE-DOB-01",
                            rule_name="Cross-Document Date of Birth Consistency",
                            status=FindingStatus.FAIL,
                            severity=Severity.CRITICAL,
                            penalty=25,
                            field="DATE_OF_BIRTH",
                            documents_involved=[DocumentType.APPLICATION_FORM.value, DocumentType.MARKSHEET.value],
                            message=f"Date of Birth contradiction: Application Form ({d1}) vs Marksheet ({d2}).",
                            evidence=ev_dob,
                            remediation="Update Date of Birth on portal application to strictly match the Class 10 High School Certificate.",
                            statutory_reference="UIDAI & Board of Secondary Education Regulation Clause 7"
                        ))
                        score -= 25
                else:
                    findings.append(Finding(
                        rule_id="RULE-DOB-PASS",
                        rule_name="Date of Birth Consistency",
                        status=FindingStatus.PASS,
                        severity=Severity.INFO,
                        penalty=0,
                        field="DATE_OF_BIRTH",
                        documents_involved=[DocumentType.APPLICATION_FORM.value, DocumentType.MARKSHEET.value],
                        message=f"Date of Birth matches consistently ({d1}).",
                        evidence=ev_dob,
                        remediation="No action required.",
                        statutory_reference="HSC Board Verification Guidelines"
                    ))

        # ----------------- 6. INCOME VALUE CONSISTENCY & CEILING VALIDATION -----------------
        inc_f_cert = get_f(DocumentType.INCOME_CERT, "annual_income")
        inc_f_app = get_f(DocumentType.APPLICATION_FORM, "annual_income")

        if inc_f_cert:
            cert_val = inc_f_cert.normalized_value
            ev_inc_cert = inc_f_cert.provenance or EvidenceProvenance(document_type="INCOME_CERT", file_name="", raw_snippet=inc_f_cert.raw_value)

            if cert_val is None:
                findings.append(Finding(
                    rule_id="RULE-INC-03",
                    rule_name="Income Extraction",
                    status=FindingStatus.UNKNOWN,
                    severity=Severity.CRITICAL,
                    penalty=20,
                    field="INCOME_VALUE",
                    documents_involved=[DocumentType.INCOME_CERT.value],
                    message=f"Could not parse valid numerical income from Income Certificate ('{inc_f_cert.raw_value}').",
                    evidence=[ev_inc_cert],
                    remediation="Verify income figure on certificate is not smudged or obscured.",
                    statutory_reference="Odisha Misc Cert Rules 2019"
                ))
                score -= 20
            else:
                # Check Ceiling Breach
                if cert_val > self.scheme.income_ceiling:
                    if inc_f_cert.is_uncertain:
                        findings.append(Finding(
                            rule_id="RULE-INC-CEIL-UNCERTAIN",
                            rule_name="Statutory Income Ceiling Compliance (Uncertain OCR)",
                            status=FindingStatus.REVIEW,
                            severity=Severity.REVIEW,
                            penalty=10,
                            field="INCOME_CEILING_UNCERTAIN",
                            documents_involved=[DocumentType.INCOME_CERT.value],
                            message=f"Certified annual income appears to be ₹{cert_val:,.0f} (above ceiling ₹{self.scheme.income_ceiling:,.0f}), but extraction has low OCR confidence. Verify certificate manually.",
                            evidence=[ev_inc_cert],
                            remediation="Inspect certificate scan manually to confirm the exact income digits.",
                            statutory_reference="Post-Matric Scholarship Scheme Guidelines 2021-2026, Clause 5.2"
                        ))
                        score -= 10
                    else:
                        findings.append(Finding(
                            rule_id="RULE-INC-01",
                            rule_name="Statutory Income Ceiling Compliance",
                            status=FindingStatus.FAIL,
                            severity=Severity.FATAL,
                            penalty=35,
                            field="INCOME_CEILING",
                            documents_involved=[DocumentType.INCOME_CERT.value],
                            message=f"Certified annual income ₹{cert_val:,.0f} exceeds scheme ceiling ₹{self.scheme.income_ceiling:,.0f}.",
                            evidence=[ev_inc_cert],
                            remediation=f"Applicant exceeds statutory economic threshold of ₹{self.scheme.income_ceiling:,.0f} for this scheme.",
                            statutory_reference="Post-Matric Scholarship Scheme Guidelines 2021-2026, Clause 5.2"
                        ))
                        score -= 35
                else:
                    findings.append(Finding(
                        rule_id="RULE-INC-CEIL-PASS",
                        rule_name="Statutory Income Ceiling Compliance",
                        status=FindingStatus.PASS,
                        severity=Severity.INFO,
                        penalty=0,
                        field="INCOME_CEILING",
                        documents_involved=[DocumentType.INCOME_CERT.value],
                        message=f"Certified annual income ₹{cert_val:,.0f} is within statutory ceiling (₹{self.scheme.income_ceiling:,.0f}).",
                        evidence=[ev_inc_cert],
                        remediation="No action required.",
                        statutory_reference="Post-Matric Scholarship Guidelines Clause 5.2"
                    ))

                # Compare with Application Form declared income
                if inc_f_app and inc_f_app.normalized_value is not None:
                    app_val = inc_f_app.normalized_value
                    ev_both = [
                        ev_inc_cert,
                        inc_f_app.provenance or EvidenceProvenance(document_type="APPLICATION_FORM", file_name="", raw_snippet=inc_f_app.raw_value)
                    ]
                    if abs(cert_val - app_val) > 1.0:
                        if inc_f_cert.is_uncertain or inc_f_app.is_uncertain:
                            findings.append(Finding(
                                rule_id="RULE-INC-MISMATCH-UNCERTAIN",
                                rule_name="Income Consistency (Uncertain OCR)",
                                status=FindingStatus.REVIEW,
                                severity=Severity.REVIEW,
                                penalty=10,
                                field="INCOME_MISMATCH_UNCERTAIN",
                                documents_involved=[DocumentType.INCOME_CERT.value, DocumentType.APPLICATION_FORM.value],
                                message=f"Income variance detected: Certified ₹{cert_val:,.0f} vs Declared ₹{app_val:,.0f}, but extraction has low OCR confidence. Verify figures visually.",
                                evidence=ev_both,
                                remediation="Check application form and income certificate to confirm values.",
                                statutory_reference="NSP Guidelines on Income Declaration Verification"
                            ))
                            score -= 10
                        else:
                            findings.append(Finding(
                                rule_id="RULE-INC-02",
                                rule_name="Income Consistency (Declared vs Certified)",
                                status=FindingStatus.FAIL,
                                severity=Severity.CRITICAL,
                                penalty=25,
                                field="INCOME_MISMATCH",
                                documents_involved=[DocumentType.INCOME_CERT.value, DocumentType.APPLICATION_FORM.value],
                                message=f"Income mismatch: Certified ₹{cert_val:,.0f} vs Declared on form ₹{app_val:,.0f}.",
                                evidence=ev_both,
                                remediation="Correct declared income in application form to exactly equal the certified income.",
                                statutory_reference="NSP Guidelines on Income Declaration Verification"
                            ))
                            score -= 25
                    else:
                        findings.append(Finding(
                            rule_id="RULE-INC-MATCH-PASS",
                            rule_name="Income Consistency (Declared vs Certified)",
                            status=FindingStatus.PASS,
                            severity=Severity.INFO,
                            penalty=0,
                            field="INCOME_MATCH",
                            documents_involved=[DocumentType.INCOME_CERT.value, DocumentType.APPLICATION_FORM.value],
                            message=f"Declared income (₹{app_val:,.0f}) matches certified income exactly.",
                            evidence=ev_both,
                            remediation="No action required.",
                            statutory_reference="NSP Guidelines"
                        ))

        # ----------------- 7. CERTIFICATE EXPIRY CHECK (INCOME CERTIFICATE) -----------------
        inc_date_f = get_f(DocumentType.INCOME_CERT, "issue_date")
        if inc_date_f and inc_date_f.raw_value:
            ev_date = [inc_date_f.provenance or EvidenceProvenance(document_type="INCOME_CERT", file_name="", raw_snippet=inc_date_f.raw_value)]
            p_date, st_date, _ = parse_and_normalize_date(inc_date_f.raw_value)
            if not p_date:
                findings.append(Finding(
                    rule_id="RULE-EXP-02",
                    rule_name="Certificate Date Parseability",
                    status=FindingStatus.UNKNOWN,
                    severity=Severity.CRITICAL,
                    penalty=20,
                    field="CERT_DATE_PARSE",
                    documents_involved=[DocumentType.INCOME_CERT.value],
                    message=f"Issue date '{inc_date_f.raw_value}' on Income Certificate is unreadable or malformed.",
                    evidence=ev_date,
                    remediation="Ensure the certificate date stamp is crisp and legible.",
                    statutory_reference="Odisha Misc Cert Rules 2019"
                ))
                score -= 20
            else:
                age_days = (self.audit_date - p_date).days
                age_years = age_days / 365.25
                if age_years > self.scheme.income_cert_validity_years:
                    findings.append(Finding(
                        rule_id="RULE-EXP-01",
                        rule_name="Income Certificate Statutory Validity Period",
                        status=FindingStatus.FAIL,
                        severity=Severity.CRITICAL,
                        penalty=25,
                        field="CERTIFICATE_EXPIRY",
                        documents_involved=[DocumentType.INCOME_CERT.value],
                        message=f"Income Certificate expired: issued on {p_date} ({age_years:.1f} years ago; maximum validity is {self.scheme.income_cert_validity_years} years).",
                        evidence=ev_date,
                        remediation="Apply for a renewed Income Certificate at the nearest Tahsil Office or e-District portal.",
                        statutory_reference="Odisha Misc Cert Rules 2019, Rule 8(2)"
                    ))
                    score -= 25
                else:
                    findings.append(Finding(
                        rule_id="RULE-EXP-PASS",
                        rule_name="Income Certificate Statutory Validity Period",
                        status=FindingStatus.PASS,
                        severity=Severity.INFO,
                        penalty=0,
                        field="CERTIFICATE_VALIDITY",
                        documents_involved=[DocumentType.INCOME_CERT.value],
                        message=f"Income Certificate is valid (issued {p_date}, age {age_years:.1f} years <= {self.scheme.income_cert_validity_years} years).",
                        evidence=ev_date,
                        remediation="No action required.",
                        statutory_reference="Odisha Misc Cert Rules 2019, Rule 8(2)"
                    ))

        # ----------------- 8. CERTIFICATE NUMBER INCONSISTENCIES -----------------
        # Income cert no
        app_inc_no = get_f(DocumentType.APPLICATION_FORM, "income_cert_no")
        act_inc_no = get_f(DocumentType.INCOME_CERT, "certificate_no")
        if app_inc_no and act_inc_no and app_inc_no.raw_value and act_inc_no.raw_value:
            ev_c = [
                app_inc_no.provenance or EvidenceProvenance(document_type="APPLICATION_FORM", file_name="", raw_snippet=app_inc_no.raw_value),
                act_inc_no.provenance or EvidenceProvenance(document_type="INCOME_CERT", file_name="", raw_snippet=act_inc_no.raw_value)
            ]
            if normalize_cert_number(app_inc_no.raw_value) != normalize_cert_number(act_inc_no.raw_value):
                findings.append(Finding(
                    rule_id="RULE-REF-01",
                    rule_name="Income Certificate Number Reference Match",
                    status=FindingStatus.FAIL,
                    severity=Severity.CRITICAL,
                    penalty=25,
                    field="INCOME_CERT_NO_MISMATCH",
                    documents_involved=[DocumentType.APPLICATION_FORM.value, DocumentType.INCOME_CERT.value],
                    message=f"Application form references Income Cert '{app_inc_no.raw_value}', but uploaded document has '{act_inc_no.raw_value}'.",
                    evidence=ev_c,
                    remediation="Update certificate reference number in portal application to match uploaded certificate.",
                    statutory_reference="OSSP e-District Integration Guideline"
                ))
                score -= 25
            else:
                findings.append(Finding(
                    rule_id="RULE-REF-INC-PASS",
                    rule_name="Income Certificate Number Reference Match",
                    status=FindingStatus.PASS,
                    severity=Severity.INFO,
                    penalty=0,
                    field="INCOME_CERT_NO_MATCH",
                    documents_involved=[DocumentType.APPLICATION_FORM.value, DocumentType.INCOME_CERT.value],
                    message="Income Certificate number matches reference on application form.",
                    evidence=ev_c,
                    remediation="No action required.",
                    statutory_reference="OSSP e-District Guidelines"
                ))

        # Caste cert no
        app_cst_no = get_f(DocumentType.APPLICATION_FORM, "caste_cert_no")
        act_cst_no = get_f(DocumentType.CASTE_CERT, "certificate_no")
        if app_cst_no and act_cst_no and app_cst_no.raw_value and act_cst_no.raw_value:
            ev_cst = [
                app_cst_no.provenance or EvidenceProvenance(document_type="APPLICATION_FORM", file_name="", raw_snippet=app_cst_no.raw_value),
                act_cst_no.provenance or EvidenceProvenance(document_type="CASTE_CERT", file_name="", raw_snippet=act_cst_no.raw_value)
            ]
            if normalize_cert_number(app_cst_no.raw_value) != normalize_cert_number(act_cst_no.raw_value):
                findings.append(Finding(
                    rule_id="RULE-REF-02",
                    rule_name="Caste Certificate Number Reference Match",
                    status=FindingStatus.FAIL,
                    severity=Severity.CRITICAL,
                    penalty=25,
                    field="CASTE_CERT_NO_MISMATCH",
                    documents_involved=[DocumentType.APPLICATION_FORM.value, DocumentType.CASTE_CERT.value],
                    message=f"Application form references Caste Cert '{app_cst_no.raw_value}', but uploaded document has '{act_cst_no.raw_value}'.",
                    evidence=ev_cst,
                    remediation="Update caste certificate reference number on the portal.",
                    statutory_reference="OSSP Guidelines Section 4.3"
                ))
                score -= 25
            else:
                findings.append(Finding(
                    rule_id="RULE-REF-CST-PASS",
                    rule_name="Caste Certificate Number Reference Match",
                    status=FindingStatus.PASS,
                    severity=Severity.INFO,
                    penalty=0,
                    field="CASTE_CERT_NO_MATCH",
                    documents_involved=[DocumentType.APPLICATION_FORM.value, DocumentType.CASTE_CERT.value],
                    message="Caste Certificate number matches reference on application form.",
                    evidence=ev_cst,
                    remediation="No action required.",
                    statutory_reference="OSSP Guidelines"
                ))

        # ----------------- 9. BANK IFSC & ACCOUNT NUMBER VALIDATION -----------------
        pass_ifsc = get_f(DocumentType.BANK_PASSBOOK, "ifsc")
        pass_acc = get_f(DocumentType.BANK_PASSBOOK, "account_no")
        app_ifsc = get_f(DocumentType.APPLICATION_FORM, "ifsc")
        app_acc = get_f(DocumentType.APPLICATION_FORM, "account_no")

        if pass_ifsc and pass_ifsc.raw_value:
            ev_ifsc = [pass_ifsc.provenance or EvidenceProvenance(document_type="BANK_PASSBOOK", file_name="", raw_snippet=pass_ifsc.raw_value)]
            if not validate_ifsc_code(pass_ifsc.raw_value):
                findings.append(Finding(
                    rule_id="RULE-BNK-01",
                    rule_name="Bank IFSC Code Standard Format",
                    status=FindingStatus.FAIL,
                    severity=Severity.CRITICAL,
                    penalty=20,
                    field="IFSC_FORMAT",
                    documents_involved=[DocumentType.BANK_PASSBOOK.value],
                    message=f"Bank IFSC code '{pass_ifsc.raw_value}' violates standard RBI format (4 letters, 0, 6 alphanumeric).",
                    evidence=ev_ifsc,
                    remediation="Check the passbook or contact branch for the official 11-character RBI IFSC code.",
                    statutory_reference="RBI Master Direction - Core Banking IFSC Standards"
                ))
                score -= 20
            else:
                findings.append(Finding(
                    rule_id="RULE-BNK-IFSC-PASS",
                    rule_name="Bank IFSC Code Format",
                    status=FindingStatus.PASS,
                    severity=Severity.INFO,
                    penalty=0,
                    field="IFSC_FORMAT",
                    documents_involved=[DocumentType.BANK_PASSBOOK.value],
                    message=f"Bank IFSC code '{pass_ifsc.raw_value}' is valid per RBI standard.",
                    evidence=ev_ifsc,
                    remediation="No action required.",
                    statutory_reference="RBI Master Direction"
                ))

        # Cross check account number if application form present
        if pass_acc and app_acc and pass_acc.raw_value and app_acc.raw_value:
            ev_acc = [
                pass_acc.provenance or EvidenceProvenance(document_type="BANK_PASSBOOK", file_name="", raw_snippet=pass_acc.raw_value),
                app_acc.provenance or EvidenceProvenance(document_type="APPLICATION_FORM", file_name="", raw_snippet=app_acc.raw_value)
            ]
            if pass_acc.raw_value.strip() != app_acc.raw_value.strip():
                findings.append(Finding(
                    rule_id="RULE-BNK-02",
                    rule_name="Bank Account Number Consistency",
                    status=FindingStatus.FAIL,
                    severity=Severity.CRITICAL,
                    penalty=25,
                    field="BANK_ACCOUNT_MISMATCH",
                    documents_involved=[DocumentType.BANK_PASSBOOK.value, DocumentType.APPLICATION_FORM.value],
                    message=f"Bank account number discrepancy: Passbook '{pass_acc.raw_value}' vs Form '{app_acc.raw_value}'.",
                    evidence=ev_acc,
                    remediation="Ensure the exact DBT bank account number is typed into the scholarship portal.",
                    statutory_reference="DBT Mission Guidelines for Direct Benefit Transfer"
                ))
                score -= 25

        # ----------------- 10. DOMICILE STATE VALIDATION -----------------
        res_state_f = get_f(DocumentType.RESIDENCE_CERT, "state")
        if res_state_f and res_state_f.raw_value:
            ev_dom = [res_state_f.provenance or EvidenceProvenance(document_type="RESIDENCE_CERT", file_name="", raw_snippet=res_state_f.raw_value)]
            st_val = res_state_f.raw_value.strip().upper()
            if st_val != self.scheme.target_state:
                findings.append(Finding(
                    rule_id="RULE-DOM-01",
                    rule_name="State Domicile Requirement",
                    status=FindingStatus.FAIL,
                    severity=Severity.CRITICAL,
                    penalty=25,
                    field="DOMICILE_STATE",
                    documents_involved=[DocumentType.RESIDENCE_CERT.value],
                    message=f"Applicant domicile state '{st_val}' does not match required scheme state '{self.scheme.target_state}'.",
                    evidence=ev_dom,
                    remediation=f"Submit a valid Resident Certificate issued by Revenue Authority of {self.scheme.target_state}.",
                    statutory_reference="State Scholarship Rules (Govt of Odisha) Clause 2(a)"
                ))
                score -= 25
            else:
                findings.append(Finding(
                    rule_id="RULE-DOM-PASS",
                    rule_name="State Domicile Requirement",
                    status=FindingStatus.PASS,
                    severity=Severity.INFO,
                    penalty=0,
                    field="DOMICILE_STATE",
                    documents_involved=[DocumentType.RESIDENCE_CERT.value],
                    message=f"Applicant residence state '{st_val}' matches scheme requirements.",
                    evidence=ev_dom,
                    remediation="No action required.",
                    statutory_reference="State Scholarship Rules Clause 2(a)"
                ))

        # ----------------- 11. MARKSHEET MERIT PERCENTAGE CUTOFF -----------------
        mark_pct_f = get_f(DocumentType.MARKSHEET, "percentage")
        app_caste_f = get_f(DocumentType.APPLICATION_FORM, "caste_category")
        cst_caste_f = get_f(DocumentType.CASTE_CERT, "caste_category")

        # Determine applicant category
        is_sc = False
        is_st = False
        for cf in [app_caste_f, cst_caste_f]:
            if cf and cf.raw_value:
                txt = cf.raw_value.upper()
                if "SCHEDULED CASTE" in txt or re.search(r"\bSC\b", txt):
                    is_sc = True
                if "SCHEDULED TRIBE" in txt or re.search(r"\bST\b", txt):
                    is_st = True

        if mark_pct_f and mark_pct_f.normalized_value is not None:
            pct_val = mark_pct_f.normalized_value
            ev_pct = [mark_pct_f.provenance or EvidenceProvenance(document_type="MARKSHEET", file_name="", raw_snippet=mark_pct_f.raw_value)]

            # Check scheme-specific reservation cutoff policy
            if (is_sc or is_st) and self.scheme.sc_st_cutoff_policy == "PASS_ONLY":
                # MoSJE / MoTA Post-Matric: Clause 5.2 - Eligible upon qualifying pass without cutoff
                findings.append(Finding(
                    rule_id="RULE-MRK-RELAX-PASS",
                    rule_name="Academic Eligibility Compliance (SC/ST Qualifying Pass)",
                    status=FindingStatus.PASS,
                    severity=Severity.INFO,
                    penalty=0,
                    field="MERIT_PERCENTAGE",
                    documents_involved=[DocumentType.MARKSHEET.value],
                    message=f"Candidate percentage ({pct_val}%) satisfies scheme criteria: under Clause 5.2 of Post-Matric Guidelines, SC/ST candidates are exempt from minimum percentage cutoffs upon passing the qualifying examination.",
                    evidence=ev_pct,
                    remediation="No action required.",
                    statutory_reference="Centrally Sponsored Post-Matric Scholarship Scheme Guidelines (MoSJE/MoTA) Clause 5.2"
                ))
            elif (is_sc or is_st) and self.scheme.sc_st_cutoff_policy == "RELAXED_50":
                # Medhabruti rule: 50% for SC/ST vs 60% for General
                if pct_val >= 50.0:
                    findings.append(Finding(
                        rule_id="RULE-MRK-RELAX-PASS",
                        rule_name="Academic Cutoff Compliance (SC/ST Relaxed Cutoff)",
                        status=FindingStatus.PASS,
                        severity=Severity.INFO,
                        penalty=0,
                        field="MERIT_PERCENTAGE",
                        documents_involved=[DocumentType.MARKSHEET.value],
                        message=f"Candidate percentage ({pct_val}%) satisfies relaxed SC/ST cutoff (50.0%).",
                        evidence=ev_pct,
                        remediation="No action required.",
                        statutory_reference="Medhabruti Guidelines 2024-25, Clause 4.1"
                    ))
                else:
                    findings.append(Finding(
                        rule_id="RULE-MRK-01",
                        rule_name="Academic Cutoff Compliance (SC/ST Relaxed)",
                        status=FindingStatus.FAIL,
                        severity=Severity.CRITICAL,
                        penalty=25,
                        field="MERIT_PERCENTAGE",
                        documents_involved=[DocumentType.MARKSHEET.value],
                        message=f"Aggregate marks ({pct_val}%) is below relaxed SC/ST cutoff (50.0%).",
                        evidence=ev_pct,
                        remediation="Ensure candidate meets the relaxed 50% reservation threshold.",
                        statutory_reference="Medhabruti Guidelines 2024-25, Clause 4.1"
                    ))
                    score -= 25
            else:
                # Standard cutoff compliance
                if pct_val < self.scheme.min_academic_percentage:
                    findings.append(Finding(
                        rule_id="RULE-MRK-01",
                        rule_name="Academic Cutoff Compliance",
                        status=FindingStatus.FAIL,
                        severity=Severity.CRITICAL,
                        penalty=25,
                        field="MERIT_PERCENTAGE",
                        documents_involved=[DocumentType.MARKSHEET.value],
                        message=f"Aggregate marks ({pct_val}%) is below minimum scheme cutoff ({self.scheme.min_academic_percentage}%).",
                        evidence=ev_pct,
                        remediation="Check scheme reservation categories or alternative scholarship tiers.",
                        statutory_reference="Scheme Academic Criteria Notification 2024"
                    ))
                    score -= 25
                else:
                    findings.append(Finding(
                        rule_id="RULE-MRK-PASS",
                        rule_name="Academic Cutoff Compliance",
                        status=FindingStatus.PASS,
                        severity=Severity.INFO,
                        penalty=0,
                        field="MERIT_PERCENTAGE",
                        documents_involved=[DocumentType.MARKSHEET.value],
                        message=f"Aggregate marks ({pct_val}%) satisfies the minimum cutoff ({self.scheme.min_academic_percentage}%).",
                        evidence=ev_pct,
                        remediation="No action required.",
                        statutory_reference="Scheme Academic Criteria Notification"
                    ))

        # ----------------- INDEPENDENT DECISION SAFETY LAYER -----------------
        findings = self.safety_layer.audit_findings(findings, documents, self.scheme.name)

        # ----------------- OVERALL STATUS & SCORE DETERMINATION -----------------
        score = 100 - sum(f.penalty for f in findings)
        score = max(0, min(100, score))

        summary_counts = {
            FindingStatus.PASS.value: sum(1 for f in findings if f.status == FindingStatus.PASS),
            FindingStatus.REVIEW.value: sum(1 for f in findings if f.status == FindingStatus.REVIEW),
            FindingStatus.FAIL.value: sum(1 for f in findings if f.status == FindingStatus.FAIL),
            FindingStatus.UNKNOWN.value: sum(1 for f in findings if f.status == FindingStatus.UNKNOWN),
        }

        has_unreadable = summary_counts[FindingStatus.UNKNOWN.value] > 0
        has_fatal = any(f.severity == Severity.FATAL for f in findings if f.status == FindingStatus.FAIL)
        has_fail = summary_counts[FindingStatus.FAIL.value] > 0
        has_review = summary_counts[FindingStatus.REVIEW.value] > 0

        if has_unreadable:
            overall_status = "UNREADABLE_PACKET"
        elif has_fatal:
            overall_status = "REJECT_PRECHECK"
        elif has_fail:
            overall_status = "ACTION_REQUIRED"
        elif has_review:
            overall_status = "REVIEW_RECOMMENDED"
        else:
            overall_status = "READY_TO_SUBMIT"

        return AuditResult(
            packet_id=packet_id,
            scheme_name=self.scheme.name,
            readiness_score=score,
            overall_status=overall_status,
            findings=findings,
            summary_counts=summary_counts,
            execution_time_ms=0.0,
            timestamp=datetime.now().isoformat()
        )
