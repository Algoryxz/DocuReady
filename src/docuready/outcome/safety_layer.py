"""
Independent Decision Safety Layer for DocuReady
Intercepts validation findings before applicant presentation to guarantee that:
1. Uncertain, ambiguous, unverified, or single-source evidence never triggers
   an unsupported statutory rejection (FAIL).
2. Findings lacking traceable provenance, multi-document comparison support, or
   relying on missing, unreadable, ambiguous, or low-confidence evidence never produce
   an unsupported statutory clearance (PASS).
"""

import re
from typing import Dict, List, Optional, Set, Any
from docuready.domain.enums import Raw
from docuready.outcome.resolver import resolve_outcome, weakest_evidence
from docuready.domain.models import (
    DocumentType, ExtractedDocument, ExtractedField, EvidenceState,
    Finding, FindingStatus, Severity
)


class DecisionSafetyLayer:
    """
    Independent safety firewall between extraction and finding generation.
    Enforces strict due-process guarantees, non-rejection axioms, and evidence-backed PASS/FAIL verification.
    """

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode

    def audit_findings(
        self,
        findings: List[Finding],
        documents: Dict[DocumentType, ExtractedDocument],
        scheme_name: str = "Default Scheme",
        scheme_config: Optional[Any] = None
    ) -> List[Finding]:
        """
        Audits a list of raw findings and applies safety adjustments:
        - FAIL findings without verified legal backing or with uncertain/single-source evidence are downgraded.
        - PASS findings lacking provenance, multi-source evidence, or relying on uncertain/missing fields are downgraded.
        """
        safe_findings: List[Finding] = []

        for f in findings:
            safe_f = self._audit_single_finding(f, documents, scheme_name, scheme_config)
            self._attach_v2_resolution(safe_f, documents, scheme_config)
            safe_findings.append(safe_f)

        return safe_findings

    def _attach_v2_resolution(
        self,
        finding: Finding,
        documents: Dict[DocumentType, ExtractedDocument],
        scheme_config: Optional[Any] = None,
    ) -> None:
        """Attach the canonical V2 outcome without changing legacy snapshot fields.

        This adapter lets the current validator transition safely: rule code
        still supplies its legacy raw label, while evidence certainty and the
        V2 resolver determine the public status. New rule primitives can call
        resolve_outcome directly when the pack engine is introduced.
        """
        legacy_status = finding.legacy_status_snapshot
        if finding.rule_id == "RULE-DOC-01" and legacy_status == FindingStatus.FAIL.value:
            raw = Raw.DOC_ABSENT
        elif (
            legacy_status == FindingStatus.PASS.value
            and finding.rule_id == "RULE-MRK-RELAX-PASS"
            and "exempt from minimum percentage cutoffs" in finding.message.lower()
        ):
            # The exemption is only surfaced as NOT_APPLICABLE when the
            # category evidence itself is present and verified.
            raw = Raw.EXEMPT
        elif legacy_status == FindingStatus.FAIL.value:
            raw = Raw.VIOLATED
        elif legacy_status == FindingStatus.PASS.value:
            raw = Raw.SATISFIED
        else:
            raw = Raw.INDETERMINATE

        states = self._collect_v2_evidence_states(finding, documents)
        weakest = weakest_evidence(states)

        if raw is Raw.EXEMPT and weakest is not EvidenceState.VERIFIED:
            # A category exemption cannot be trusted when its supporting
            # category evidence is absent, provisional, or uncertain.
            raw = Raw.INDETERMINATE

        severity_caps = getattr(scheme_config, "rule_max_severity", None) or {}
        max_severity = severity_caps.get(finding.rule_id)
        outcome = resolve_outcome(
            raw,
            weakest_evidence=weakest,
            max_severity=max_severity,
        )
        finding.set_resolution(raw, outcome.status, outcome.reason_code)

    def _collect_v2_evidence_states(
        self,
        finding: Finding,
        documents: Dict[DocumentType, ExtractedDocument],
    ) -> List[EvidenceState]:
        """Collect only the evidence relevant to a finding, fail-closed."""
        relevant_fields = self._get_relevant_fields(finding)
        document_names = list(finding.documents_involved)

        is_category_exemption = (
            finding.rule_id == "RULE-MRK-RELAX-PASS"
            and "exempt from minimum percentage cutoffs" in finding.message.lower()
        )
        if is_category_exemption:
            relevant_fields.update({"percentage", "caste_category"})
            # The legacy finding records only the marksheet, although category
            # is also an input. Include whichever category documents exist.
            for doc_type in (DocumentType.APPLICATION_FORM, DocumentType.CASTE_CERT):
                category_doc = documents.get(doc_type)
                has_category = bool(
                    category_doc
                    and any("caste_category" in field_name for field_name in category_doc.fields)
                )
                if has_category and doc_type.value not in document_names:
                    document_names.append(doc_type.value)

        states: List[EvidenceState] = []
        for doc_name in document_names:
            try:
                doc_type = DocumentType(doc_name)
            except (TypeError, ValueError):
                states.append(EvidenceState.UNCERTAIN)
                continue

            document = documents.get(doc_type)
            if document is None or document.status in ("MISSING", "UNREADABLE", "CORRUPTED"):
                states.append(EvidenceState.UNCERTAIN)
                continue

            if relevant_fields:
                selected_fields = [
                    field
                    for name, field in document.fields.items()
                    if name in relevant_fields
                ]
            else:
                selected_fields = list(document.fields.values())

            if selected_fields:
                for field in selected_fields:
                    is_unambiguous_expiry = False
                    if "EXP" in finding.rule_id and field.field_name == "issue_date":
                        m_year = re.search(r"\b(19\d\d|20\d\d)\b", str(field.raw_value))
                        if m_year and int(m_year.group(1)) >= 2024:
                            is_unambiguous_expiry = True

                    if field.is_uncertain and not is_unambiguous_expiry:
                        states.append(EvidenceState.UNCERTAIN)
                    elif is_unambiguous_expiry and field.evidence_state == EvidenceState.AMBIGUOUS:
                        if field.extraction_method == "NATIVE_VECTOR":
                            states.append(EvidenceState.VERIFIED_TEXT)
                        else:
                            states.append(EvidenceState.OCR_EXTRACTED)
                    else:
                        states.append(field.evidence_state)
                continue

            # Some older validator paths create provenance without a matching
            # model field. Preserve its extraction method, but missing metadata
            # must not be treated as verified.
            provenance = [
                item for item in finding.evidence
                if item.document_type == doc_type.value
            ]
            if not provenance:
                states.append(EvidenceState.UNCERTAIN)
                continue

            for item in provenance:
                if item.extraction_method == "NATIVE_VECTOR":
                    states.append(EvidenceState.VERIFIED_TEXT)
                elif item.extraction_method == "LOCAL_OCR":
                    states.append(EvidenceState.OCR_EXTRACTED)
                else:
                    states.append(EvidenceState.UNCERTAIN)

        return states

    def _audit_single_finding(
        self,
        finding: Finding,
        documents: Dict[DocumentType, ExtractedDocument],
        scheme_name: str,
        scheme_config: Optional[Any] = None
    ) -> Finding:
        if finding.legacy_status_snapshot == FindingStatus.FAIL.value:
            return self._audit_fail_finding(finding, documents, scheme_name, scheme_config)
        elif finding.legacy_status_snapshot == FindingStatus.PASS.value:
            return self._audit_pass_finding(finding, documents, scheme_name, scheme_config)
        else:
            # REVIEW and UNKNOWN findings already represent non-definitive/investigative states
            return finding

    def _audit_fail_finding(
        self,
        finding: Finding,
        documents: Dict[DocumentType, ExtractedDocument],
        scheme_name: str,
        scheme_config: Optional[Any] = None
    ) -> Finding:
        # Principle FAIL-1: Mandatory Document Absence Exception
        # If the finding is specifically about a missing mandatory document (RULE-DOC-01),
        # verify that it has a verified legal citation. Packet-level absence does not have document evidence.
        if finding.rule_id == "RULE-DOC-01" or "MANDATORY_DOCUMENT" in (finding.field or ""):
            if not finding.statutory_reference or "UNVERIFIED" in finding.statutory_reference.upper():
                return Finding(
                    rule_id=f"{finding.rule_id}-UNVERIFIED",
                    rule_name=f"{finding.rule_name} (Unverified Statutory Reference)",
                    status=FindingStatus.REVIEW,
                    severity=Severity.REVIEW,
                    penalty=min(finding.penalty, 10),
                    field=finding.field,
                    documents_involved=finding.documents_involved,
                    message=f"[SAFETY INTERCEPT: Downgraded to REVIEW because governing rule lacks verified primary legal citation.] {finding.message}",
                    evidence=finding.evidence,
                    remediation="Consult legal/portal administrator for confirmed scheme notification.",
                    statutory_reference="Constitution of India Art 14 (Due Process & Legal Certainty)"
                )
            return finding

        # Principle FAIL-2: Statutory Reference Verification
        # A finding cannot produce statutory FAIL without a verified legal reference
        if not finding.statutory_reference or "UNVERIFIED" in finding.statutory_reference.upper():
            return Finding(
                rule_id=f"{finding.rule_id}-UNVERIFIED",
                rule_name=f"{finding.rule_name} (Unverified Statutory Reference)",
                status=FindingStatus.REVIEW,
                severity=Severity.REVIEW,
                penalty=min(finding.penalty, 10),
                field=finding.field,
                documents_involved=finding.documents_involved,
                message=f"[SAFETY INTERCEPT: Downgraded to REVIEW because governing rule lacks verified primary legal citation.] {finding.message}",
                evidence=finding.evidence,
                remediation="Consult legal/portal administrator for confirmed scheme notification.",
                statutory_reference="Constitution of India Art 14 (Due Process & Legal Certainty)"
            )

        # Principle FAIL-3: Multi-Document Contradiction Provenance Guarantee
        # If the finding alleges a cross-document contradiction, it MUST have provenance from at least 2 distinct documents
        is_cross_doc = (
            any(kw in finding.rule_id for kw in ["NAME", "DOB", "MISMATCH", "REF-", "BNK-02"])
            or (len(finding.documents_involved) >= 2 and any(kw in (finding.field or "") for kw in ["NAME", "DOB", "MISMATCH", "REF", "ACCOUNT"]))
        )
        if is_cross_doc:
            doc_provenances = set(ev.document_type for ev in finding.evidence if ev.document_type)
            if len(doc_provenances) < 2:
                return Finding(
                    rule_id=f"{finding.rule_id}-SINGLE-SOURCE",
                    rule_name=f"{finding.rule_name} (Single-Source Inconclusive)",
                    status=FindingStatus.UNKNOWN,
                    severity=Severity.CRITICAL,
                    penalty=min(finding.penalty, 15),
                    field=finding.field,
                    documents_involved=finding.documents_involved,
                    message=f"[SAFETY INTERCEPT: Cross-document contradiction claimed but supporting evidence only found in {doc_provenances}. Cannot establish contradiction without dual-document evidence.]",
                    evidence=finding.evidence,
                    remediation="Upload the missing comparator document to substantiate cross-document comparison.",
                    statutory_reference=finding.statutory_reference
                )

        # Principle FAIL-4: OCR Uncertainty & Epistemic State Safety
        # Check all involved documents for low confidence, ambiguity, or unreadable status
        uncertain_evidence_reasons = []
        relevant_fields = self._get_relevant_fields(finding)

        for dt_str in finding.documents_involved:
            try:
                dt = DocumentType(dt_str)
            except Exception:
                continue

            doc = documents.get(dt)
            if not doc:
                continue

            # If the entire document is UNREADABLE or CORRUPTED, FAIL is prohibited
            if doc.status in ["UNREADABLE", "CORRUPTED"]:
                uncertain_evidence_reasons.append(f"{dt.value} is {doc.status}")
                continue

            # Check relevant field evidence states
            for fname, fld in doc.fields.items():
                if relevant_fields and fname not in relevant_fields:
                    continue

                if fld.evidence_state in [EvidenceState.LOW_CONFIDENCE, EvidenceState.UNREADABLE]:
                    uncertain_evidence_reasons.append(
                        f"{dt.value}.{fname} has evidence state '{fld.evidence_state.value}' (calibrated conf: {fld.calibrated_confidence:.1%})"
                    )
                elif fld.evidence_state == EvidenceState.AMBIGUOUS:
                    # If it's an expiration check and the year is clearly expired under both DD/MM interpretations, don't downgrade
                    if "EXP" in finding.rule_id and fname == "issue_date":
                        # Year check: if year is <= 2022 (in 2026), it is expired in either interpretation
                        m_year = re.search(r"\b(19\d\d|20\d\d)\b", str(fld.raw_value))
                        if m_year and int(m_year.group(1)) <= 2022:
                            continue
                    uncertain_evidence_reasons.append(
                        f"{dt.value}.{fname} has ambiguous evidence (calibrated conf: {fld.calibrated_confidence:.1%})"
                    )
                elif fld.is_uncertain:
                    uncertain_evidence_reasons.append(
                        f"{dt.value}.{fname} is uncertain ({fld.uncertainty_reason or 'OCR uncertainty'})"
                    )

        if uncertain_evidence_reasons:
            reasons_str = "; ".join(uncertain_evidence_reasons[:2])
            return Finding(
                rule_id=finding.rule_id,
                rule_name=f"{finding.rule_name} (Evidence Inconclusive)",
                status=FindingStatus.REVIEW,
                severity=Severity.REVIEW,
                penalty=min(finding.penalty, 10),
                field=finding.field,
                documents_involved=finding.documents_involved,
                message=f"[SAFETY INTERCEPT: Statutory FAIL downgraded to REVIEW because supporting evidence is uncertain: {reasons_str}. Direct applicant rejection is legally impermissible on unconfirmed evidence.] {finding.message}",
                evidence=finding.evidence,
                remediation=f"Inspect original document scan manually. {finding.remediation}",
                statutory_reference=finding.statutory_reference
            )

        return finding

    def _audit_pass_finding(
        self,
        finding: Finding,
        documents: Dict[DocumentType, ExtractedDocument],
        scheme_name: str,
        scheme_config: Optional[Any] = None
    ) -> Finding:
        # Principle PASS-1: Traceable Provenance Requirement
        # A PASS finding must have non-empty supporting evidence linking values to source documents
        if not finding.evidence:
            return Finding(
                rule_id=f"{finding.rule_id}-NO-PROVENANCE",
                rule_name=f"{finding.rule_name} (No Evidence Provenance)",
                status=FindingStatus.UNKNOWN,
                severity=Severity.REVIEW,
                penalty=15,
                field=finding.field,
                documents_involved=finding.documents_involved,
                message=f"[SAFETY INTERCEPT: PASS finding lacks supporting evidence provenance. An unverified claim cannot produce statutory PASS.] {finding.message}",
                evidence=[],
                remediation="Ensure document fields are properly extracted with traceable provenance.",
                statutory_reference=finding.statutory_reference
            )

        # Principle PASS-2: Multi-Document Comparison Provenance Guarantee
        # A cross-document match requires evidence from at least 2 distinct documents
        is_cross_doc = (
            any(kw in finding.rule_id for kw in ["NAME", "DOB", "MATCH", "REF-", "BNK-02", "CROSS"])
            or (len(finding.documents_involved) >= 2 and any(kw in (finding.field or "") for kw in ["NAME", "DOB", "MATCH", "REF", "ACCOUNT"]))
        )
        if is_cross_doc:
            doc_provenances = set(ev.document_type for ev in finding.evidence if ev.document_type)
            if len(doc_provenances) < 2:
                return Finding(
                    rule_id=f"{finding.rule_id}-SINGLE-SOURCE",
                    rule_name=f"{finding.rule_name} (Single-Source Inconclusive)",
                    status=FindingStatus.UNKNOWN,
                    severity=Severity.REVIEW,
                    penalty=15,
                    field=finding.field,
                    documents_involved=finding.documents_involved,
                    message=f"[SAFETY INTERCEPT: Cross-document PASS claimed but supporting evidence only found in {doc_provenances}. Cannot establish cross-document consistency without dual-document evidence.] {finding.message}",
                    evidence=finding.evidence,
                    remediation="Upload the missing comparator document to substantiate cross-document comparison.",
                    statutory_reference=finding.statutory_reference
                )

        # Principle PASS-3: Supporting Document Legibility & Presence
        doc_provenances = set(ev.document_type for ev in finding.evidence if ev.document_type)
        for dt_str in doc_provenances:
            try:
                dt = DocumentType(dt_str)
            except Exception:
                continue

            doc = documents.get(dt)
            if not doc or doc.status in ["UNREADABLE", "CORRUPTED", "MISSING"]:
                doc_status = doc.status if doc else "MISSING"
                return Finding(
                    rule_id=finding.rule_id,
                    rule_name=f"{finding.rule_name} (Document {doc_status})",
                    status=FindingStatus.UNKNOWN,
                    severity=Severity.REVIEW,
                    penalty=15,
                    field=finding.field,
                    documents_involved=finding.documents_involved,
                    message=f"[SAFETY INTERCEPT: PASS downgraded to UNKNOWN because supporting document '{dt.value}' is {doc_status}. A valid PASS cannot rely on an unreadable or missing document.] {finding.message}",
                    evidence=finding.evidence,
                    remediation=f"Ensure '{dt.value}' is clearly legible and properly uploaded.",
                    statutory_reference=finding.statutory_reference
                )

        # Principle PASS-4: Field-Level Evidence State and Value Sufficiency
        relevant_fields = self._get_relevant_fields(finding)

        for dt_str in doc_provenances:
            try:
                dt = DocumentType(dt_str)
            except Exception:
                continue

            doc = documents.get(dt)
            if not doc:
                continue

            ev_fields_for_doc = set(ev.extracted_field for ev in finding.evidence if ev.document_type == dt_str and ev.extracted_field)
            fields_to_check = ev_fields_for_doc if ev_fields_for_doc else (relevant_fields.intersection(doc.fields.keys()) if relevant_fields else set())

            if not fields_to_check and relevant_fields:
                fields_to_check = relevant_fields

            for fname in fields_to_check:
                fld = doc.fields.get(fname)
                if not fld or fld.raw_value is None or str(fld.raw_value).strip() == "":
                    return Finding(
                        rule_id=finding.rule_id,
                        rule_name=f"{finding.rule_name} (Missing Field Evidence)",
                        status=FindingStatus.UNKNOWN,
                        severity=Severity.REVIEW,
                        penalty=15,
                        field=finding.field,
                        documents_involved=finding.documents_involved,
                        message=f"[SAFETY INTERCEPT: PASS downgraded to UNKNOWN because supporting field '{dt.value}.{fname}' is missing or empty.] {finding.message}",
                        evidence=finding.evidence,
                        remediation=f"Ensure '{fname}' is clearly visible and extracted on '{dt.value}'.",
                        statutory_reference=finding.statutory_reference
                    )

                if fld.evidence_state in [EvidenceState.UNREADABLE, EvidenceState.NOT_FOUND]:
                    return Finding(
                        rule_id=finding.rule_id,
                        rule_name=f"{finding.rule_name} (Unreadable Field Evidence)",
                        status=FindingStatus.UNKNOWN,
                        severity=Severity.REVIEW,
                        penalty=15,
                        field=finding.field,
                        documents_involved=finding.documents_involved,
                        message=f"[SAFETY INTERCEPT: PASS downgraded to UNKNOWN because supporting field '{dt.value}.{fname}' has evidence state '{fld.evidence_state.value}'.] {finding.message}",
                        evidence=finding.evidence,
                        remediation=f"Re-scan '{dt.value}' to ensure '{fname}' is legible.",
                        statutory_reference=finding.statutory_reference
                    )

                if fld.evidence_state == EvidenceState.LOW_CONFIDENCE or (fld.is_uncertain and "low" in (fld.uncertainty_reason or "").lower()):
                    return Finding(
                        rule_id=finding.rule_id,
                        rule_name=f"{finding.rule_name} (Low Confidence Evidence)",
                        status=FindingStatus.REVIEW,
                        severity=Severity.REVIEW,
                        penalty=10,
                        field=finding.field,
                        documents_involved=finding.documents_involved,
                        message=f"[SAFETY INTERCEPT: PASS downgraded to REVIEW because supporting field '{dt.value}.{fname}' has low confidence ({fld.calibrated_confidence:.1%}). Direct PASS requires confirmed evidence.] {finding.message}",
                        evidence=finding.evidence,
                        remediation=f"Inspect '{dt.value}' manually to confirm '{fname}'.",
                        statutory_reference=finding.statutory_reference
                    )

                if fld.evidence_state == EvidenceState.AMBIGUOUS:
                    # Date expiration check: if year is unambiguously valid under both DD/MM and MM/DD interpretations, preserve PASS
                    if "EXP" in finding.rule_id and fname == "issue_date":
                        m_year = re.search(r"\b(19\d\d|20\d\d)\b", str(fld.raw_value))
                        if m_year and int(m_year.group(1)) >= 2024:
                            continue
                    return Finding(
                        rule_id=finding.rule_id,
                        rule_name=f"{finding.rule_name} (Ambiguous Evidence)",
                        status=FindingStatus.REVIEW,
                        severity=Severity.REVIEW,
                        penalty=10,
                        field=finding.field,
                        documents_involved=finding.documents_involved,
                        message=f"[SAFETY INTERCEPT: PASS downgraded to REVIEW because supporting field '{dt.value}.{fname}' has ambiguous evidence ({fld.uncertainty_reason or 'ambiguous format'}).] {finding.message}",
                        evidence=finding.evidence,
                        remediation=f"Confirm unambiguous format of '{fname}' on '{dt.value}'.",
                        statutory_reference=finding.statutory_reference
                    )

                if fld.is_uncertain:
                    return Finding(
                        rule_id=finding.rule_id,
                        rule_name=f"{finding.rule_name} (Uncertain Evidence)",
                        status=FindingStatus.REVIEW,
                        severity=Severity.REVIEW,
                        penalty=10,
                        field=finding.field,
                        documents_involved=finding.documents_involved,
                        message=f"[SAFETY INTERCEPT: PASS downgraded to REVIEW because supporting field '{dt.value}.{fname}' is uncertain ({fld.uncertainty_reason or 'unconfirmed evidence'}).] {finding.message}",
                        evidence=finding.evidence,
                        remediation=f"Inspect scan manually to confirm '{fname}'.",
                        statutory_reference=finding.statutory_reference
                    )

        return finding

    def _get_relevant_fields(self, finding: Finding) -> Set[str]:
        """Resolves target field names corresponding to a finding's rule scope."""
        relevant_fields = set()
        for ev in finding.evidence:
            if ev.extracted_field:
                relevant_fields.add(ev.extracted_field)

        if not relevant_fields:
            f_upper = f"{finding.rule_id} {finding.field}".upper()
            if "INC" in f_upper:
                relevant_fields.add("annual_income")
            if "NAME" in f_upper:
                relevant_fields.add("applicant_name")
            if "DOB" in f_upper:
                relevant_fields.add("dob")
            if "EXP" in f_upper or "VALID" in f_upper:
                relevant_fields.add("issue_date")
            if "MRK" in f_upper or "PERCENTAGE" in f_upper:
                relevant_fields.add("percentage")
            if "DOM" in f_upper or "STATE" in f_upper:
                relevant_fields.add("state")
            if "CST" in f_upper or "CASTE" in f_upper:
                relevant_fields.add("caste_category")
            if "BNK" in f_upper or "ACCOUNT" in f_upper or "IFSC" in f_upper:
                relevant_fields.update(["account_no", "ifsc"])
            if "REF-INC" in f_upper:
                relevant_fields.update(["certificate_no", "income_cert_no"])
            if "REF-CST" in f_upper:
                relevant_fields.update(["certificate_no", "caste_cert_no"])

        return relevant_fields
