"""
Independent Decision Safety Layer for DocuReady Loop 3
Intercepts validation findings before applicant presentation to guarantee that
uncertain, ambiguous, unverified, or single-source evidence never triggers
an illegal or unsupported statutory rejection (FAIL).
"""

import re
from typing import Dict, List, Optional
from docuready.domain.models import (
    DocumentType, ExtractedDocument, ExtractedField, EvidenceState,
    Finding, FindingStatus, Severity
)


class DecisionSafetyLayer:
    """
    Independent safety firewall between extraction and finding generation.
    Enforces strict due-process guarantees and non-rejection axioms.
    """

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode

    def audit_findings(
        self,
        findings: List[Finding],
        documents: Dict[DocumentType, ExtractedDocument],
        scheme_name: str
    ) -> List[Finding]:
        """
        Audits a list of raw findings and applies safety downgrades where evidence is inconclusive.
        """
        safe_findings: List[Finding] = []

        for f in findings:
            safe_f = self._audit_single_finding(f, documents, scheme_name)
            safe_findings.append(safe_f)

        return safe_findings

    def _audit_single_finding(
        self,
        finding: Finding,
        documents: Dict[DocumentType, ExtractedDocument],
        scheme_name: str
    ) -> Finding:
        # Principle 1: PASS, REVIEW, UNKNOWN need no safety downgrade from FAIL
        if finding.status != FindingStatus.FAIL:
            return finding

        # Principle 2: Statutory Reference Verification
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

        # Principle 3: Multi-Document Contradiction Provenance Guarantee
        # If the finding alleges a cross-document contradiction, it MUST have provenance from at least 2 distinct documents
        is_cross_doc = any(kw in finding.rule_id for kw in ["NAME", "DOB", "MISMATCH", "REF-", "BNK-02"])
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

        # Principle 4: OCR Uncertainty & Epistemic State Safety
        # Check all involved documents for low confidence, ambiguity, or unreadable status
        uncertain_evidence_reasons = []

        # Determine relevant fields for this finding to avoid false downgrades from unrelated fields
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
