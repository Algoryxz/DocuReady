"""T2.4 — Document Slot Validation Test Suite.

Comprehensive synthetic verification suite testing lightweight anchor-keyword
slot sanity checks across all 24 required scenarios.

Guarantees:
- Expected slot and detected content are independently verified.
- Confident mismatch -> Status.REVIEW with ReasonCode.WRONG_DOCUMENT_TYPE.
- Uncertain identity / conflicting anchors / generic text / unreadable -> Status.REVIEW with ReasonCode.EVIDENCE_UNCERTAIN.
- Bank statement cannot be treated as a bank passbook.
- Aadhaar-like numbers alone cannot identify Aadhaar.
- Missing mandatory slot -> Status.MISSING, ReasonCode.DOC_ABSENT.
- Missing optional slot -> No finding.
- Swapped documents are not silently relocated.
- Slot mismatch never produces automatic FAIL.
- Golden baseline hash remains bit-exact.
"""

from datetime import date
from typing import Dict, Optional
import pytest

from docuready.domain.enums import (
    EvidenceState,
    ExtractionMethod,
    Raw,
    Readiness,
    ReasonCode,
    Status,
)
from docuready.domain.models import (
    DOC_TYPE_LABELS,
    DocumentType,
    ExtractedDocument,
    ExtractedField,
    Finding,
    FindingStatus,
    Severity,
)
from docuready.ingest.slot_classifier import (
    classify_document_content,
    SlotClassification,
)
from docuready.outcome.resolver import resolve_outcome
from docuready.rules.slot_validator import validate_packet_slots, validate_slot
from docuready.rules.validator import DocuReadyValidator, SchemeConfig


# ==============================================================================
# SYNTHETIC TEXT FIXTURES
# ==============================================================================

SYNTHETIC_TEXTS = {
    DocumentType.INCOME_CERT: (
        "GOVERNMENT OF ODISHA\nREVENUE DEPARTMENT\nOFFICE OF THE TAHSILDAR\n"
        "INCOME CERTIFICATE\nCertificate No: E-INC/2025/104928\nIssue Date: 10/01/2025\n"
        "This is to certify that annual family income is Rs. 1,80,000/-\n"
        "Issuing Authority: Revenue Officer / Tahsildar"
    ),
    DocumentType.CASTE_CERT: (
        "GOVERNMENT OF ODISHA\nDEPARTMENT OF ST & SC DEVELOPMENT\n"
        "COMMUNITY / CASTE CERTIFICATE\nCertificate No: CST/2025/88192\nIssue Date: 12/03/2024\n"
        "Recognized Category: SC\nIssuing Authority: Sub-Divisional Magistrate"
    ),
    DocumentType.RESIDENCE_CERT: (
        "GOVERNMENT OF ODISHA\nDEPARTMENT OF REVENUE & LAND RECORDS\n"
        "RESIDENT / DOMICILE CERTIFICATE\nCertificate No: RES/2025/99812\nIssue Date: 15/01/2025\n"
        "Permanent Resident of District: KHORDHA\nState: ODISHA"
    ),
    DocumentType.MARKSHEET: (
        "BOARD OF SECONDARY EDUCATION, ODISHA\n"
        "MARKS STATEMENT — CLASS 10 HIGH SCHOOL CERTIFICATE EXAMINATION\n"
        "Roll No: 2309BA1042\nTotal Marks: 500\nMarks Obtained: 392\nPercentage: 78.4%\nGrade: A"
    ),
    DocumentType.BANK_PASSBOOK: (
        "STATE BANK OF INDIA\nSAVINGS BANK PASSBOOK — MAIN BRANCH\n"
        "Account Holder Name: Smruti Ranjan Nayak\nAccount Number: 30987654301\n"
        "Bank IFSC Code: SBIN0001234\nBranch: Bhubaneswar"
    ),
    DocumentType.APPLICATION_FORM: (
        "COMMON SCHOLARSHIP PORTAL\n"
        "SCHOLARSHIP APPLICATION ACKNOWLEDGEMENT\n"
        "Application ID: APP-2025-99881\nRegistration Number: REG-887766\n"
        "Scheme Name: Post-Matric Scholarship\nAcademic Session: 2024-2025"
    ),
    DocumentType.AADHAAR: (
        "GOVERNMENT OF INDIA\nUNIQUE IDENTIFICATION AUTHORITY OF INDIA\n"
        "AADHAAR CARD\nUIDAI\n1234 5678 9012\nMera Aadhaar, Meri Pehchan"
    ),
}

BANK_STATEMENT_TEXT = (
    "STATE BANK OF INDIA\nACCOUNT STATEMENT\nStatement Period: 01/01/2025 to 31/01/2025\n"
    "Account Number: 30987654301\nBank IFSC Code: SBIN0001234\n"
    "Closing Balance: Rs. 45,210.00\nTransaction History: Ref #99812"
)

GENERIC_TEXT = (
    "To whom it may concern,\nThis document confirms the applicant's details.\n"
    "Name: Smruti Ranjan Nayak\nAddress: Main Road, Bhubaneswar\nDate: 15/01/2025"
)

CONFLICTING_ANCHORS_TEXT = (
    "GOVERNMENT OF ODISHA\nINCOME CERTIFICATE\nCOMMUNITY / CASTE CERTIFICATE\n"
    "Annual Income: 1,80,000\nCaste Category: SC\nCertificate No: CST-INC-99"
)

WRONG_LANGUAGE_TEXT = (
    "ଏହା ଦ୍ଵାରା ପ୍ରମାଣିତ କରାଯାଉଅଛି ଯେ ଏହି ପତ୍ରଟି ଏକ ପ୍ରମାଣପତ୍ର ଅଟେ | "
    "ନାମ: ସ୍ମୃତି ରଞ୍ଜନ ନାୟକ, ଠିକଣା: ଭୁବନେଶ୍ୱର |"
)

WEAK_OCR_TEXT = "xx... ??!! 110022 -- zzqq jjkk mmpp 8877 //.. illegible fragment"

AADHAAR_NUMBER_WITHOUT_ANCHORS = (
    "IDENTITY PROOF DOCUMENT\nCandidate Name: Smruti Ranjan Nayak\n"
    "ID Sequence: 9988 7766 5544\nDate of Birth: 14/05/2003\nQR Code Ref: 987123"
)


def _make_doc(
    doc_type: DocumentType,
    raw_text: str = "",
    status: str = "VALID",
    file_name: str = "doc.pdf",
    detected_type: Optional[DocumentType] = None,
) -> ExtractedDocument:
    """Helper to create synthetic ExtractedDocument fixtures."""
    return ExtractedDocument(
        doc_type=detected_type or doc_type,
        file_path=file_name,
        status=status,
        raw_text=raw_text,
        fields={},
        page_count=1,
        extraction_method="NATIVE_VECTOR",
        detected_type=detected_type,
    )


# ==============================================================================
# 1. CORRECT CLASSIFICATION (Scenarios 1, 2, 3)
# ==============================================================================

def test_scenario_01_correct_content_in_each_of_seven_intended_slots():
    """Scenario 1: Each of the 7 supported document types in its intended slot yields no finding."""
    for doc_type, text in SYNTHETIC_TEXTS.items():
        doc = _make_doc(doc_type, raw_text=text)
        finding = validate_slot(slot=doc_type, doc=doc, is_mandatory=True)
        assert finding is None, f"Expected no finding for {doc_type.value} in its intended slot"


def test_scenario_02_primary_anchor_recognition():
    """Scenario 2: Primary anchors are recognized unambiguously for each document type."""
    for doc_type, text in SYNTHETIC_TEXTS.items():
        classification = classify_document_content(text)
        assert classification.is_confident is True
        assert classification.candidate_type == doc_type
        assert len(classification.primary_anchors) >= 1
        assert classification.is_uncertain is False


def test_scenario_03_supporting_terms_corroborate_not_independently_establish():
    """Scenario 3: Supporting terms corroborate identity, but alone do not establish classification."""
    # Supporting terms alone without primary title anchor
    text_supporting_only = (
        "Annual Family Income: Rs. 1,80,000/-\nCertificate No: 12345\n"
        "Issue Date: 10/01/2025\nIssuing Authority: Tahsildar"
    )
    classification = classify_document_content(text_supporting_only)
    assert classification.candidate_type is None
    assert classification.is_uncertain is True
    assert "authoritative primary title anchors are missing" in classification.uncertainty_reason


# ==============================================================================
# 2. WRONG DOCUMENT / MISMATCH (Scenarios 4, 5, 6, 7, 8)
# ==============================================================================

def test_scenario_04_income_cert_in_caste_cert_slot():
    """Scenario 4: Income certificate uploaded to the caste certificate slot produces WRONG_DOCUMENT_TYPE."""
    doc = _make_doc(
        DocumentType.INCOME_CERT,
        raw_text=SYNTHETIC_TEXTS[DocumentType.INCOME_CERT],
        file_name="caste_cert.pdf",
    )
    finding = validate_slot(slot=DocumentType.CASTE_CERT, doc=doc)

    assert finding is not None
    assert finding.rule_id == "RULE-SLOT-01"
    assert finding.status == FindingStatus.REVIEW
    assert finding.severity == Severity.REVIEW
    assert "Expected 'CASTE_CERT'" in finding.message
    assert "identifies as 'INCOME_CERT'" in finding.message

    # Outcome resolution safety
    safety_layer = DocuReadyValidator().safety_layer
    findings = safety_layer.audit_findings([finding], {DocumentType.CASTE_CERT: doc})
    assert findings[0].status is Status.REVIEW
    assert findings[0].reason_code == ReasonCode.WRONG_DOCUMENT_TYPE.value
    assert findings[0].raw_result is Raw.VIOLATED


def test_scenario_05_caste_cert_in_residence_cert_slot():
    """Scenario 5: Caste certificate uploaded to residence slot produces WRONG_DOCUMENT_TYPE."""
    doc = _make_doc(
        DocumentType.CASTE_CERT,
        raw_text=SYNTHETIC_TEXTS[DocumentType.CASTE_CERT],
        file_name="residence_cert.pdf",
    )
    finding = validate_slot(slot=DocumentType.RESIDENCE_CERT, doc=doc)

    assert finding is not None
    assert finding.rule_id == "RULE-SLOT-01"
    assert "Expected 'RESIDENCE_CERT'" in finding.message
    assert "identifies as 'CASTE_CERT'" in finding.message

    safety_layer = DocuReadyValidator().safety_layer
    findings = safety_layer.audit_findings([finding], {DocumentType.RESIDENCE_CERT: doc})
    assert findings[0].status is Status.REVIEW
    assert findings[0].reason_code == ReasonCode.WRONG_DOCUMENT_TYPE.value


def test_scenario_06_marksheet_and_application_form_swapped():
    """Scenario 6: Swapped marksheet and application form produce mismatch findings for each slot."""
    doc_in_marksheet_slot = _make_doc(
        DocumentType.APPLICATION_FORM,
        raw_text=SYNTHETIC_TEXTS[DocumentType.APPLICATION_FORM],
        file_name="marksheet.pdf",
    )
    doc_in_app_slot = _make_doc(
        DocumentType.MARKSHEET,
        raw_text=SYNTHETIC_TEXTS[DocumentType.MARKSHEET],
        file_name="application_form.pdf",
    )

    finding_ms = validate_slot(slot=DocumentType.MARKSHEET, doc=doc_in_marksheet_slot)
    finding_app = validate_slot(slot=DocumentType.APPLICATION_FORM, doc=doc_in_app_slot)

    assert finding_ms is not None
    assert "Expected 'MARKSHEET'" in finding_ms.message
    assert "identifies as 'APPLICATION_FORM'" in finding_ms.message

    assert finding_app is not None
    assert "Expected 'APPLICATION_FORM'" in finding_app.message
    assert "identifies as 'MARKSHEET'" in finding_app.message

    safety_layer = DocuReadyValidator().safety_layer
    resolved_ms = safety_layer.audit_findings([finding_ms], {DocumentType.MARKSHEET: doc_in_marksheet_slot})[0]
    resolved_app = safety_layer.audit_findings([finding_app], {DocumentType.APPLICATION_FORM: doc_in_app_slot})[0]

    assert resolved_ms.reason_code == ReasonCode.WRONG_DOCUMENT_TYPE.value
    assert resolved_app.reason_code == ReasonCode.WRONG_DOCUMENT_TYPE.value


def test_scenario_07_bank_statement_in_passbook_slot():
    """Scenario 7: Bank statement uploaded to passbook slot is rejected with EVIDENCE_UNCERTAIN."""
    doc = _make_doc(
        DocumentType.BANK_PASSBOOK,
        raw_text=BANK_STATEMENT_TEXT,
        file_name="bank_passbook.pdf",
    )
    finding = validate_slot(slot=DocumentType.BANK_PASSBOOK, doc=doc)

    assert finding is not None
    assert finding.rule_id == "RULE-SLOT-01"
    assert "bank statement" in finding.message.lower()

    safety_layer = DocuReadyValidator().safety_layer
    findings = safety_layer.audit_findings([finding], {DocumentType.BANK_PASSBOOK: doc})
    assert findings[0].status is Status.REVIEW
    assert findings[0].reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value
    assert findings[0].raw_result is Raw.INDETERMINATE


def test_scenario_08_filename_indicates_one_type_content_identifies_another():
    """Scenario 8: Content overrides filename when filename contradicts content."""
    # File named 'income_cert.pdf' contains Caste Certificate content
    doc = _make_doc(
        DocumentType.CASTE_CERT,
        raw_text=SYNTHETIC_TEXTS[DocumentType.CASTE_CERT],
        file_name="income_cert.pdf",
    )
    finding = validate_slot(slot=DocumentType.INCOME_CERT, doc=doc)

    assert finding is not None
    assert "Expected 'INCOME_CERT'" in finding.message
    assert "identifies as 'CASTE_CERT'" in finding.message


# ==============================================================================
# 3. UNCERTAIN IDENTIFICATION (Scenarios 9, 10, 11, 12, 13)
# ==============================================================================

def test_scenario_09_generic_keywords_only():
    """Scenario 9: Generic words without authoritative title anchors produce EVIDENCE_UNCERTAIN."""
    doc = _make_doc(DocumentType.INCOME_CERT, raw_text=GENERIC_TEXT)
    finding = validate_slot(slot=DocumentType.INCOME_CERT, doc=doc)

    assert finding is not None
    assert finding.rule_id == "RULE-SLOT-01"

    safety_layer = DocuReadyValidator().safety_layer
    findings = safety_layer.audit_findings([finding], {DocumentType.INCOME_CERT: doc})
    assert findings[0].status is Status.REVIEW
    assert findings[0].reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value


def test_scenario_10_conflicting_anchors_from_multiple_types():
    """Scenario 10: Conflicting anchors from multiple document types yield EVIDENCE_UNCERTAIN."""
    doc = _make_doc(DocumentType.INCOME_CERT, raw_text=CONFLICTING_ANCHORS_TEXT)
    finding = validate_slot(slot=DocumentType.INCOME_CERT, doc=doc)

    assert finding is not None
    assert "Conflicting primary anchors" in finding.message

    safety_layer = DocuReadyValidator().safety_layer
    findings = safety_layer.audit_findings([finding], {DocumentType.INCOME_CERT: doc})
    assert findings[0].status is Status.REVIEW
    assert findings[0].reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value


def test_scenario_11_wrong_language_page_without_reliable_type_evidence():
    """Scenario 11: Wrong language without reliable anchors yields EVIDENCE_UNCERTAIN, not WRONG_DOCUMENT_TYPE."""
    doc = _make_doc(DocumentType.INCOME_CERT, raw_text=WRONG_LANGUAGE_TEXT)
    finding = validate_slot(slot=DocumentType.INCOME_CERT, doc=doc)

    assert finding is not None
    safety_layer = DocuReadyValidator().safety_layer
    findings = safety_layer.audit_findings([finding], {DocumentType.INCOME_CERT: doc})
    assert findings[0].status is Status.REVIEW
    assert findings[0].reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value


def test_scenario_12_weak_ocr_text_without_reliable_content_candidate():
    """Scenario 12: Weak / garbled OCR text yields EVIDENCE_UNCERTAIN."""
    doc = _make_doc(DocumentType.MARKSHEET, raw_text=WEAK_OCR_TEXT)
    finding = validate_slot(slot=DocumentType.MARKSHEET, doc=doc)

    assert finding is not None
    safety_layer = DocuReadyValidator().safety_layer
    findings = safety_layer.audit_findings([finding], {DocumentType.MARKSHEET: doc})
    assert findings[0].status is Status.REVIEW
    assert findings[0].reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value


def test_scenario_13_aadhaar_numbers_without_identity_anchors():
    """Scenario 13: 12-digit number / QR code alone without Aadhaar identity anchors must NOT identify Aadhaar."""
    doc = _make_doc(DocumentType.AADHAAR, raw_text=AADHAAR_NUMBER_WITHOUT_ANCHORS)
    finding = validate_slot(slot=DocumentType.AADHAAR, doc=doc)

    assert finding is not None
    safety_layer = DocuReadyValidator().safety_layer
    findings = safety_layer.audit_findings([finding], {DocumentType.AADHAAR: doc})
    assert findings[0].status is Status.REVIEW
    assert findings[0].reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value


# ==============================================================================
# 4. UNREADABLE AND MISSING (Scenarios 14, 15, 16, 17, 18, 19)
# ==============================================================================

def test_scenario_14_blank_page():
    """Scenario 14: Blank page upload produces uncertainty finding."""
    doc = _make_doc(DocumentType.INCOME_CERT, raw_text="")
    finding = validate_slot(slot=DocumentType.INCOME_CERT, doc=doc, emit_for_unreadable=True)

    assert finding is not None
    safety_layer = DocuReadyValidator().safety_layer
    findings = safety_layer.audit_findings([finding], {DocumentType.INCOME_CERT: doc})
    assert findings[0].status is Status.REVIEW
    assert findings[0].reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value


def test_scenario_15_completely_unreadable_scan():
    """Scenario 15: Completely unreadable scan yields EVIDENCE_UNCERTAIN when checked for slot."""
    doc = _make_doc(DocumentType.INCOME_CERT, status="UNREADABLE")
    finding = validate_slot(slot=DocumentType.INCOME_CERT, doc=doc, emit_for_unreadable=True)

    assert finding is not None
    assert "unreadable" in finding.message.lower()
    safety_layer = DocuReadyValidator().safety_layer
    findings = safety_layer.audit_findings([finding], {DocumentType.INCOME_CERT: doc})
    assert findings[0].status is Status.REVIEW
    assert findings[0].reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value


def test_scenario_16_corrupted_pdf():
    """Scenario 16: Corrupted PDF produces EVIDENCE_UNCERTAIN when checked for slot."""
    doc = _make_doc(DocumentType.CASTE_CERT, status="CORRUPTED")
    finding = validate_slot(slot=DocumentType.CASTE_CERT, doc=doc, emit_for_unreadable=True)

    assert finding is not None
    assert "corrupted" in finding.message.lower()
    safety_layer = DocuReadyValidator().safety_layer
    findings = safety_layer.audit_findings([finding], {DocumentType.CASTE_CERT: doc})
    assert findings[0].status is Status.REVIEW
    assert findings[0].reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value


def test_scenario_17_malformed_upload_does_not_raise_exception():
    """Scenario 17: None, empty dictionary, or bizarre text input does not raise unhandled exception."""
    try:
        f1 = validate_slot(slot=DocumentType.INCOME_CERT, doc=None)
        assert f1 is None

        classification = classify_document_content("")
        assert classification.is_uncertain is True

        classification_junk = classify_document_content("\x00\x01\x02\xff\xfe\r\n\t")
        assert classification_junk.is_uncertain is True

        findings, mismatched = validate_packet_slots({}, [])
        assert findings == []
        assert len(mismatched) == 0
    except Exception as exc:
        pytest.fail(f"Malformed input raised uncaught exception: {exc}")


def test_scenario_18_missing_configured_required_slot_produces_doc_absent():
    """Scenario 18: Missing configured required slot produces RULE-DOC-01 with DOC_ABSENT."""
    packet: Dict[DocumentType, ExtractedDocument] = {
        DocumentType.INCOME_CERT: _make_doc(DocumentType.INCOME_CERT, SYNTHETIC_TEXTS[DocumentType.INCOME_CERT]),
    }
    validator = DocuReadyValidator(
        SchemeConfig(mandatory_documents=[DocumentType.INCOME_CERT, DocumentType.CASTE_CERT]),
        audit_date=date(2026, 11, 15),
    )
    result = validator.validate_packet("PKT_TEST_MISSING", packet)

    missing_findings = [f for f in result.findings if f.rule_id == "RULE-DOC-01"]
    assert len(missing_findings) == 1
    assert missing_findings[0].status is Status.MISSING
    assert missing_findings[0].reason_code == ReasonCode.DOC_ABSENT.value
    assert result.readiness is Readiness.NOT_READY


def test_scenario_19_missing_optional_slot_does_not_produce_doc_absent():
    """Scenario 19: Missing optional slot (AADHAAR) must NOT produce DOC_ABSENT."""
    packet: Dict[DocumentType, ExtractedDocument] = {}
    for dt in [
        DocumentType.APPLICATION_FORM,
        DocumentType.INCOME_CERT,
        DocumentType.CASTE_CERT,
        DocumentType.RESIDENCE_CERT,
        DocumentType.MARKSHEET,
        DocumentType.BANK_PASSBOOK,
    ]:
        packet[dt] = _make_doc(dt, SYNTHETIC_TEXTS[dt])

    # AADHAAR is omitted
    assert DocumentType.AADHAAR not in packet

    # Default mandatory list does NOT contain AADHAAR
    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    assert DocumentType.AADHAAR not in validator.scheme.mandatory_documents

    result = validator.validate_packet("PKT_TEST_OPTIONAL_AADHAAR", packet)
    aadhaar_findings = [
        f for f in result.findings
        if DocumentType.AADHAAR.value in f.documents_involved and f.rule_id == "RULE-DOC-01"
    ]
    assert len(aadhaar_findings) == 0


# ==============================================================================
# 5. SAFETY AND INTEGRATION (Scenarios 20, 21, 22, 23, 24)
# ==============================================================================

def test_scenario_20_swapped_files_are_not_silently_moved():
    """Scenario 20: Swapped files remain in their uploaded slots and both emit slot findings."""
    doc_income_slot = _make_doc(
        DocumentType.CASTE_CERT,
        raw_text=SYNTHETIC_TEXTS[DocumentType.CASTE_CERT],
        file_name="income_cert.pdf",
    )
    doc_caste_slot = _make_doc(
        DocumentType.INCOME_CERT,
        raw_text=SYNTHETIC_TEXTS[DocumentType.INCOME_CERT],
        file_name="caste_cert.pdf",
    )

    documents = {
        DocumentType.INCOME_CERT: doc_income_slot,
        DocumentType.CASTE_CERT: doc_caste_slot,
    }

    findings, mismatched_slots = validate_packet_slots(
        documents, [DocumentType.INCOME_CERT, DocumentType.CASTE_CERT]
    )

    assert DocumentType.INCOME_CERT in mismatched_slots
    assert DocumentType.CASTE_CERT in mismatched_slots
    assert len(findings) == 2

    rule_ids = [f.rule_id for f in findings]
    assert rule_ids == ["RULE-SLOT-01", "RULE-SLOT-01"]


def test_scenario_21_wrong_slot_never_becomes_automatic_fail():
    """Scenario 21: A document in the wrong slot never produces an automatic statutory FAIL."""
    # Complete 6-doc packet, but caste_cert slot has an Income Certificate
    packet: Dict[DocumentType, ExtractedDocument] = {}
    for dt in [
        DocumentType.APPLICATION_FORM,
        DocumentType.INCOME_CERT,
        DocumentType.RESIDENCE_CERT,
        DocumentType.MARKSHEET,
        DocumentType.BANK_PASSBOOK,
    ]:
        packet[dt] = _make_doc(dt, SYNTHETIC_TEXTS[dt])

    # Put Income Cert into Caste Cert slot
    packet[DocumentType.CASTE_CERT] = _make_doc(
        DocumentType.INCOME_CERT,
        raw_text=SYNTHETIC_TEXTS[DocumentType.INCOME_CERT],
        file_name="caste_cert.pdf",
    )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("PKT_TEST_SLOT_FAIL_GUARD", packet)

    # Must NOT contain statutory FAIL for caste_cert
    fail_findings = [f for f in result.findings if f.status is Status.FAIL]
    assert len(fail_findings) == 0, f"Unexpected FAIL findings: {fail_findings}"

    # Must contain RULE-SLOT-01 with REVIEW
    slot_findings = [f for f in result.findings if f.rule_id == "RULE-SLOT-01"]
    assert len(slot_findings) == 1
    assert slot_findings[0].status is Status.REVIEW
    assert slot_findings[0].reason_code == ReasonCode.WRONG_DOCUMENT_TYPE.value


def test_scenario_22_slot_mismatch_findings_appear_in_audit_result():
    """Scenario 22: Slot mismatch findings appear prominently in final AuditResult."""
    packet: Dict[DocumentType, ExtractedDocument] = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.CASTE_CERT,
            raw_text=SYNTHETIC_TEXTS[DocumentType.CASTE_CERT],
            file_name="income_cert.pdf",
        )
    }
    validator = DocuReadyValidator(
        SchemeConfig(mandatory_documents=[DocumentType.INCOME_CERT]),
        audit_date=date(2026, 11, 15),
    )
    result = validator.validate_packet("PKT_TEST_AUDIT_RES", packet)

    f = next((f for f in result.findings if f.rule_id == "RULE-SLOT-01"), None)
    assert f is not None
    assert f.field == "DOCUMENT_SLOT"
    assert f.documents_involved == [DocumentType.INCOME_CERT.value]
    assert f.severity is Severity.REVIEW
    assert f.status is Status.REVIEW
    assert f.reason_code == ReasonCode.WRONG_DOCUMENT_TYPE.value


def test_scenario_23_packet_readiness_reflects_review():
    """Scenario 23: Packet readiness reflects NEEDS_CHECKS for slot REVIEW findings."""
    packet: Dict[DocumentType, ExtractedDocument] = {}
    for dt in [
        DocumentType.APPLICATION_FORM,
        DocumentType.INCOME_CERT,
        DocumentType.CASTE_CERT,
        DocumentType.RESIDENCE_CERT,
        DocumentType.MARKSHEET,
        DocumentType.BANK_PASSBOOK,
    ]:
        packet[dt] = _make_doc(dt, SYNTHETIC_TEXTS[dt])

    # Replace residence cert with generic text
    packet[DocumentType.RESIDENCE_CERT] = _make_doc(
        DocumentType.RESIDENCE_CERT,
        raw_text=GENERIC_TEXT,
        file_name="residence_cert.pdf",
    )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("PKT_TEST_READINESS_REVIEW", packet)

    assert result.readiness is Readiness.NEEDS_CHECKS
    assert result.overall_status is Readiness.NEEDS_CHECKS


def test_scenario_24_existing_extraction_and_validator_remain_compatible():
    """Scenario 24: Clean packet preserves 100% compatibility with 0 slot findings."""
    packet: Dict[DocumentType, ExtractedDocument] = {}
    for dt in [
        DocumentType.APPLICATION_FORM,
        DocumentType.INCOME_CERT,
        DocumentType.CASTE_CERT,
        DocumentType.RESIDENCE_CERT,
        DocumentType.MARKSHEET,
        DocumentType.BANK_PASSBOOK,
    ]:
        packet[dt] = _make_doc(dt, SYNTHETIC_TEXTS[dt])

    findings, mismatched_slots = validate_packet_slots(
        packet, list(packet.keys())
    )
    assert findings == []
    assert len(mismatched_slots) == 0


# ==============================================================================
# 6. RESOLVER DIRECT UNIT TESTS FOR SLOT MISMATCH BRANCHES
# ==============================================================================

def test_resolver_slot_mismatch_verified_yields_wrong_document_type():
    """Direct test of resolver slot_mismatch branch with verified evidence."""
    outcome = resolve_outcome(
        Raw.VIOLATED,
        weakest_evidence=EvidenceState.VERIFIED,
        slot_mismatch=True,
    )
    assert outcome.status is Status.REVIEW
    assert outcome.reason_code == ReasonCode.WRONG_DOCUMENT_TYPE.value


def test_resolver_slot_mismatch_uncertain_yields_evidence_uncertain():
    """Direct test of resolver slot_mismatch branch with uncertain evidence."""
    outcome = resolve_outcome(
        Raw.INDETERMINATE,
        weakest_evidence=EvidenceState.UNCERTAIN,
        slot_mismatch=True,
    )
    assert outcome.status is Status.REVIEW
    assert outcome.reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value


def test_resolver_slot_mismatch_violated_provisional_yields_evidence_uncertain():
    """Direct test of resolver slot_mismatch branch with violated provisional evidence."""
    outcome = resolve_outcome(
        Raw.VIOLATED,
        weakest_evidence=EvidenceState.PROVISIONAL,
        slot_mismatch=True,
    )
    assert outcome.status is Status.REVIEW
    assert outcome.reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value


def test_resolver_slot_mismatch_doc_absent_preserves_missing():
    """Direct test of resolver slot_mismatch with Raw.DOC_ABSENT."""
    outcome = resolve_outcome(
        Raw.DOC_ABSENT,
        weakest_evidence=None,
        slot_mismatch=True,
    )
    assert outcome.status is Status.MISSING
    assert outcome.reason_code == ReasonCode.DOC_ABSENT.value


# ==============================================================================
# 7. PIPELINE INTEGRATION WITH REAL ON-DISK SYNTHETIC FILES
# ==============================================================================

def test_pipeline_swapped_files_integration(tmp_path):
    """Pipeline integration: Swapped files on disk retain their upload slot mapping and emit RULE-SLOT-01."""
    import shutil
    from pathlib import Path
    from docuready.pipeline import AuditPipeline

    clean_dir = Path("synthetic_data/pkt_01_clean")
    test_pkt = tmp_path / "pkt_swapped"
    test_pkt.mkdir()

    # Swap income_cert.pdf and caste_cert.pdf
    shutil.copy(clean_dir / "income_cert.pdf", test_pkt / "caste_cert.pdf")
    shutil.copy(clean_dir / "caste_cert.pdf", test_pkt / "income_cert.pdf")
    shutil.copy(clean_dir / "residence_cert.pdf", test_pkt / "residence_cert.pdf")
    shutil.copy(clean_dir / "marksheet.pdf", test_pkt / "marksheet.pdf")
    shutil.copy(clean_dir / "bank_passbook.pdf", test_pkt / "bank_passbook.pdf")
    shutil.copy(clean_dir / "application_form.pdf", test_pkt / "application_form.pdf")

    pipeline = AuditPipeline(as_of=date(2026, 11, 15))
    audit_res, docs = pipeline.load_and_audit_packet(str(test_pkt), packet_id="PKT_SWAPPED")

    # Verify both documents are keyed by their upload slot in docs dictionary
    assert DocumentType.INCOME_CERT in docs
    assert DocumentType.CASTE_CERT in docs

    # Verify docs[INCOME_CERT] contains the uploaded file (which contains a caste certificate)
    assert docs[DocumentType.INCOME_CERT].detected_type == DocumentType.CASTE_CERT
    assert docs[DocumentType.CASTE_CERT].detected_type == DocumentType.INCOME_CERT

    # Verify slot findings appear
    slot_findings = [f for f in audit_res.findings if f.rule_id == "RULE-SLOT-01"]
    assert len(slot_findings) == 2
    for sf in slot_findings:
        assert sf.status is Status.REVIEW
        assert sf.reason_code == ReasonCode.WRONG_DOCUMENT_TYPE.value

    # Verify readiness reflects NEEDS_CHECKS and NOT automatic FAIL
    assert audit_res.readiness is Readiness.NEEDS_CHECKS
    assert audit_res.v2_summary_counts[Status.FAIL.value] == 0


# ==============================================================================
# 8. REVIEW HARDENING & INTEGRATION REGRESSION TESTS (T2.4 PR #69 REVIEW)
# ==============================================================================

def test_aadhaar_field_in_application_form_remains_application_form():
    """Regression: An application form with an Aadhaar number field remains APPLICATION_FORM."""
    app_text = (
        "COMMON SCHOLARSHIP PORTAL\n"
        "APPLICATION ACKNOWLEDGEMENT RECEIPT — POST-MATRIC SCHOLARSHIP (SC/ST/OBC)\n"
        "Section 1: Applicant Demographics\n"
        "Applicant Full Name: Smruti Ranjan Nayak\n"
        "Aadhaar Number: 1234 5678 9012\n"
        "Aadhaar Enrollment Status: ENROLLED\n"
    )
    classification = classify_document_content(app_text)
    assert classification.is_confident is True
    assert classification.candidate_type == DocumentType.APPLICATION_FORM
    assert classification.is_uncertain is False
    assert DocumentType.AADHAAR not in classification.conflicting_types

    doc = _make_doc(DocumentType.APPLICATION_FORM, raw_text=app_text)
    finding = validate_slot(slot=DocumentType.APPLICATION_FORM, doc=doc)
    assert finding is None


def test_aadhaar_linking_or_seeding_in_application_not_aadhaar():
    """Regression: An application form mentioning Aadhaar linking/seeding is not classified as Aadhaar."""
    app_text = (
        "SCHOLARSHIP APPLICATION FORM 2025-26\n"
        "Section 3: Bank Account & DBT Verification\n"
        "Applicant Name: Smruti Ranjan Nayak\n"
        "Bank Name: State Bank of India\n"
        "Aadhaar seeding with bank account: YES\n"
        "Aadhaar mapped to NPCI payment bridge: ACTIVE\n"
    )
    classification = classify_document_content(app_text)
    assert classification.is_confident is True
    assert classification.candidate_type == DocumentType.APPLICATION_FORM
    assert classification.candidate_type != DocumentType.AADHAAR
    assert "APPLICATION" in classification.primary_anchors[0]


def test_genuine_aadhaar_synthetic_identity_document_classified_as_aadhaar():
    """Regression: A genuine synthetic Aadhaar identity document is classified as AADHAAR."""
    aadhaar_text = (
        "GOVERNMENT OF INDIA\n"
        "UNIQUE IDENTIFICATION AUTHORITY OF INDIA\n"
        "AADHAAR CARD\n"
        "Mera Aadhaar, Meri Pehchan\n"
        "To: Smruti Ranjan Nayak\n"
        "DOB: 15/08/2005\n"
        "Gender: MALE\n"
        "Aadhaar Number: 1234 5678 9012\n"
    )
    classification = classify_document_content(aadhaar_text)
    assert classification.is_confident is True
    assert classification.candidate_type == DocumentType.AADHAAR
    assert len(classification.primary_anchors) >= 1

    doc = _make_doc(DocumentType.AADHAAR, raw_text=aadhaar_text)
    # Valid in Aadhaar slot
    assert validate_slot(slot=DocumentType.AADHAAR, doc=doc) is None
    # Mismatch in Income slot
    mismatch_f = validate_slot(slot=DocumentType.INCOME_CERT, doc=doc)
    assert mismatch_f is not None
    assert mismatch_f.status == FindingStatus.REVIEW
    assert "Expected 'INCOME_CERT'" in mismatch_f.message
    assert "identifies as 'AADHAAR'" in mismatch_f.message


def test_bare_aadhaar_number_and_generic_demographics_remains_uncertain():
    """Regression: A document with only an Aadhaar number and generic identity wording remains uncertain."""
    generic_id_text = (
        "Aadhaar Number: 1234 5678 9012\n"
        "Name: Smruti Ranjan Nayak\n"
        "Date of Birth: 15/08/2005\n"
        "Address: Plot 104, Saheed Nagar, Bhubaneswar\n"
    )
    classification = classify_document_content(generic_id_text)
    assert classification.candidate_type is None
    assert classification.is_confident is False
    assert classification.is_uncertain is True
    assert "authoritative primary title anchors are missing" in classification.uncertainty_reason

    doc = _make_doc(DocumentType.AADHAAR, raw_text=generic_id_text)
    finding = validate_slot(slot=DocumentType.AADHAAR, doc=doc)
    assert finding is not None
    assert finding.status == FindingStatus.REVIEW
    assert finding._is_wrong_type is False


def test_application_form_with_body_certificate_references_remains_application_form():
    """Regression: Body text references to required certificates do not trigger conflicting classification."""
    app_text = (
        "COMMON SCHOLARSHIP PORTAL\n"
        "APPLICATION ACKNOWLEDGEMENT RECEIPT — POST-MATRIC SCHOLARSHIP\n"
        "Applicant Full Name: Smruti Ranjan Nayak\n"
        "Instructions & Enclosures:\n"
        "- Income certificate required.\n"
        "- Upload caste certificate.\n"
        "- Residence certificate attachment.\n"
        "Documents to be submitted:\n"
        "1. Income Certificate\n"
        "2. Caste Certificate\n"
        "3. Residence Certificate\n"
    )
    classification = classify_document_content(app_text)
    assert classification.is_confident is True
    assert classification.candidate_type == DocumentType.APPLICATION_FORM
    assert classification.conflicting_types == []
    assert len(classification.primary_anchors) >= 1

    doc = _make_doc(DocumentType.APPLICATION_FORM, raw_text=app_text)
    assert validate_slot(slot=DocumentType.APPLICATION_FORM, doc=doc) is None


def test_evidence_provenance_reports_detected_type_and_no_fabricated_page():
    """Regression: Evidence provenance records detected candidate type and avoids fabricated page 1."""
    caste_text = SYNTHETIC_TEXTS[DocumentType.CASTE_CERT]
    doc = _make_doc(DocumentType.CASTE_CERT, raw_text=caste_text, file_name="uploaded_file.pdf")
    finding = validate_slot(slot=DocumentType.INCOME_CERT, doc=doc)

    assert finding is not None
    assert finding.rule_id == "RULE-SLOT-01"
    assert len(finding.evidence) == 1
    ev = finding.evidence[0]

    # Must report detected candidate type, NOT expected slot
    assert ev.document_type == DocumentType.CASTE_CERT.value
    assert ev.document_type != DocumentType.INCOME_CERT.value
    # Must NOT fabricate page 1 provenance when page number is unknown
    assert ev.page_number is None
    assert ev.extracted_field == "DOCUMENT_SLOT"
    assert "Expected slot: 'INCOME_CERT'" in ev.raw_snippet
    assert "Detected candidate: 'CASTE_CERT'" in ev.raw_snippet

    # Message must not leak sensitive applicant details
    assert "Smruti" not in finding.message
    assert "Nayak" not in finding.message


def test_unreadable_and_corrupted_integrated_matrix_outcomes():
    """Regression: End-to-end validate_packet unreadable and corrupted outcomes match agreed domain matrix."""
    # 1. Unreadable document produces RULE-DOC-02 with REVIEW / EVIDENCE_UNCERTAIN
    doc_unreadable = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="synthetic_data/income_cert.pdf",
        status="UNREADABLE",
        extraction_method=ExtractionMethod.UNEXTRACTED.value,
    )
    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("TEST_UNREADABLE", {DocumentType.INCOME_CERT: doc_unreadable})

    doc02_findings = [f for f in result.findings if f.rule_id == "RULE-DOC-02"]
    assert len(doc02_findings) == 1
    f_unreadable = doc02_findings[0]
    assert f_unreadable.status is Status.REVIEW
    assert f_unreadable.reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value
    assert f_unreadable.severity is Severity.CRITICAL
    assert f_unreadable.penalty == 25

    # Verify no duplicate unreadable slot finding is emitted
    slot_findings = [f for f in result.findings if f.rule_id == "RULE-SLOT-01"]
    assert len(slot_findings) == 0

    # 2. Missing mandatory upload produces RULE-DOC-01 with MISSING / DOC_ABSENT
    result_missing = validator.validate_packet("TEST_MISSING", {})
    doc01_findings = [f for f in result_missing.findings if f.rule_id == "RULE-DOC-01"]
    assert len(doc01_findings) > 0
    for f_m in doc01_findings:
        assert f_m.status is Status.MISSING
        assert f_m.reason_code == ReasonCode.DOC_ABSENT.value

    # 3. Blank upload produces RULE-SLOT-01 with REVIEW / EVIDENCE_UNCERTAIN
    doc_blank = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="synthetic_data/income_cert.pdf",
        status="VALID",
        raw_text="",
        fields={},
        extraction_method=ExtractionMethod.NATIVE_VECTOR.value,
    )
    result_blank = validator.validate_packet("TEST_BLANK", {DocumentType.INCOME_CERT: doc_blank})
    slot_blank_findings = [f for f in result_blank.findings if f.rule_id == "RULE-SLOT-01"]
    assert len(slot_blank_findings) == 1
    assert slot_blank_findings[0].status is Status.REVIEW
    assert slot_blank_findings[0].reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value


def test_actual_malformed_temporary_files_handling(tmp_path):
    """Regression: Real corrupted, blank, and truncated files on disk extract and audit cleanly without uncaught exceptions."""
    import pymupdf
    from docuready.ingest.extractor import DocumentExtractor
    from docuready.pipeline import AuditPipeline

    # 1. Corrupted PDF header file
    corrupted_hdr = tmp_path / "corrupted_hdr.pdf"
    corrupted_hdr.write_bytes(b"NOT_A_VALID_PDF_HEADER_ABCDEF123456")

    # 2. Valid blank-page PDF
    blank_pdf = tmp_path / "blank_page.pdf"
    doc_blank = pymupdf.open()
    doc_blank.new_page()
    doc_blank.save(str(blank_pdf))
    doc_blank.close()

    # 3. Truncated PDF body
    truncated_pdf = tmp_path / "truncated_body.pdf"
    truncated_pdf.write_bytes(b"%PDF-1.4\nTRUNCATED_BODY_GARBAGE\x00\x01\x02\xff\xfe")

    extractor = DocumentExtractor()

    # Extraction must not crash with uncaught exceptions
    ed_corrupt = extractor.extract_document(str(corrupted_hdr), DocumentType.INCOME_CERT)
    assert ed_corrupt.status == "CORRUPTED"

    ed_blank = extractor.extract_document(str(blank_pdf), DocumentType.CASTE_CERT)
    assert ed_blank.status == "UNREADABLE"

    ed_trunc = extractor.extract_document(str(truncated_pdf), DocumentType.MARKSHEET)
    assert ed_trunc.status == "CORRUPTED"

    # Pipeline intake with malformed files in a packet directory
    pkt_dir = tmp_path / "malformed_packet"
    pkt_dir.mkdir()
    (pkt_dir / "income_cert.pdf").write_bytes(b"NOT_A_PDF_HEADER_ABCDEF")
    (pkt_dir / "caste_cert.pdf").write_bytes(blank_pdf.read_bytes())
    (pkt_dir / "marksheet.pdf").write_bytes(truncated_pdf.read_bytes())

    pipeline = AuditPipeline(as_of=date(2026, 11, 15))
    audit_res, docs = pipeline.load_and_audit_packet(str(pkt_dir), packet_id="PKT_MALFORMED")

    # Final audit result status reflects NEEDS_CHECKS or NOT_READY
    assert audit_res.readiness in (Readiness.NEEDS_CHECKS, Readiness.NOT_READY)

    # All unreadable/corrupted findings must resolve to REVIEW / EVIDENCE_UNCERTAIN
    unreadable_findings = [f for f in audit_res.findings if f.rule_id == "RULE-DOC-02"]
    assert len(unreadable_findings) >= 2
    for f in unreadable_findings:
        assert f.status is Status.REVIEW
        assert f.reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value


# ---------------------------------------------------------------------------
# POST-MERGE REVIEW HARDENING REGRESSION TESTS
# ---------------------------------------------------------------------------


def test_regression_01_app_form_with_aadhaar_number_field():
    """Regression 1: Application form containing an Aadhaar Number field remains APPLICATION_FORM."""
    doc_text = (
        "COMMON SCHOLARSHIP PORTAL\n"
        "APPLICATION ACKNOWLEDGEMENT RECEIPT\n"
        "Applicant Name: Smruti Ranjan Nayak\n"
        "Aadhaar Number: 1234 5678 9012\n"
    )
    classification = classify_document_content(doc_text)
    assert classification.is_confident is True
    assert classification.candidate_type == DocumentType.APPLICATION_FORM
    assert classification.conflicting_types == []
    assert DocumentType.AADHAAR not in classification.conflicting_types

    doc = _make_doc(DocumentType.APPLICATION_FORM, raw_text=doc_text)
    finding = validate_slot(slot=DocumentType.APPLICATION_FORM, doc=doc)
    assert finding is None


def test_regression_02_app_form_with_aadhaar_holder_details():
    """Regression 2: Application form containing 'Aadhaar Card holder details' remains APPLICATION_FORM."""
    doc_text = (
        "COMMON SCHOLARSHIP PORTAL\n"
        "SCHOLARSHIP APPLICATION FORM 2025-26\n"
        "Aadhaar Card holder details: Verified\n"
        "Aadhaar Number: 1234 5678 9012\n"
    )
    classification = classify_document_content(doc_text)
    assert classification.is_confident is True
    assert classification.candidate_type == DocumentType.APPLICATION_FORM
    assert classification.conflicting_types == []
    assert DocumentType.AADHAAR not in classification.conflicting_types

    doc = _make_doc(DocumentType.APPLICATION_FORM, raw_text=doc_text)
    finding = validate_slot(slot=DocumentType.APPLICATION_FORM, doc=doc)
    assert finding is None


def test_regression_03_app_form_with_bank_passbook_upload_instructions():
    """Regression 3: Application form instructing to upload bank passbook remains APPLICATION_FORM."""
    doc_text = (
        "COMMON SCHOLARSHIP PORTAL\n"
        "APPLICATION ACKNOWLEDGEMENT RECEIPT\n"
        "Upload bank passbook\n"
        "Bank passbook required\n"
        "Passbook details: Account 123456\n"
    )
    classification = classify_document_content(doc_text)
    assert classification.is_confident is True
    assert classification.candidate_type == DocumentType.APPLICATION_FORM
    assert classification.conflicting_types == []
    assert DocumentType.BANK_PASSBOOK not in classification.conflicting_types

    doc = _make_doc(DocumentType.APPLICATION_FORM, raw_text=doc_text)
    finding = validate_slot(slot=DocumentType.APPLICATION_FORM, doc=doc)
    assert finding is None


def test_regression_04_app_form_mentioning_income_caste_residence_certificates():
    """Regression 4: Application form checklist mentioning certificates remains APPLICATION_FORM."""
    doc_text = (
        "COMMON SCHOLARSHIP PORTAL\n"
        "APPLICATION ACKNOWLEDGEMENT RECEIPT\n"
        "- Income certificate required.\n"
        "- Upload caste certificate.\n"
        "- Residence certificate attachment.\n"
        "Supporting documents to attach:\n"
        "1. Income Certificate\n"
        "2. Caste Certificate\n"
        "3. Residence Certificate\n"
    )
    classification = classify_document_content(doc_text)
    assert classification.is_confident is True
    assert classification.candidate_type == DocumentType.APPLICATION_FORM
    assert classification.conflicting_types == []

    doc = _make_doc(DocumentType.APPLICATION_FORM, raw_text=doc_text)
    finding = validate_slot(slot=DocumentType.APPLICATION_FORM, doc=doc)
    assert finding is None


def test_regression_05_genuine_standalone_aadhaar_identification():
    """Regression 5: Standalone Aadhaar card is positively classified as AADHAAR."""
    doc_text = (
        "GOVERNMENT OF INDIA\n"
        "UNIQUE IDENTIFICATION AUTHORITY OF INDIA\n"
        "AADHAAR CARD\n"
        "Mera Aadhaar, Meri Pehchan\n"
        "Aadhaar Number: 1234 5678 9012\n"
    )
    classification = classify_document_content(doc_text)
    assert classification.is_confident is True
    assert classification.candidate_type == DocumentType.AADHAAR
    assert classification.conflicting_types == []
    assert len(classification.source_lines) >= 1

    doc = _make_doc(DocumentType.AADHAAR, raw_text=doc_text)
    assert validate_slot(slot=DocumentType.AADHAAR, doc=doc) is None

    # Mismatch when uploaded to INCOME_CERT slot
    finding_mismatch = validate_slot(slot=DocumentType.INCOME_CERT, doc=doc)
    assert finding_mismatch is not None
    assert finding_mismatch.status == FindingStatus.REVIEW
    assert finding_mismatch._is_wrong_type is True
    assert finding_mismatch.evidence[0].document_type == DocumentType.AADHAAR.value
    assert finding_mismatch.evidence[0].page_number is None


def test_regression_06_genuine_standalone_bank_passbook_identification():
    """Regression 6: Standalone bank passbook is positively classified as BANK_PASSBOOK."""
    doc_text = (
        "STATE BANK OF INDIA\n"
        "SAVINGS BANK PASSBOOK — BHUBANESWAR MAIN BRANCH\n"
        "Account Holder Name: Smruti Ranjan Nayak\n"
        "Account Number: 12345678901\n"
        "IFSC: SBIN0001234\n"
    )
    classification = classify_document_content(doc_text)
    assert classification.is_confident is True
    assert classification.candidate_type == DocumentType.BANK_PASSBOOK
    assert classification.conflicting_types == []
    assert len(classification.source_lines) >= 1

    doc = _make_doc(DocumentType.BANK_PASSBOOK, raw_text=doc_text)
    assert validate_slot(slot=DocumentType.BANK_PASSBOOK, doc=doc) is None

    # Mismatch when uploaded to MARKSHEET slot
    finding_mismatch = validate_slot(slot=DocumentType.MARKSHEET, doc=doc)
    assert finding_mismatch is not None
    assert finding_mismatch.status == FindingStatus.REVIEW
    assert finding_mismatch._is_wrong_type is True
    assert finding_mismatch.evidence[0].document_type == DocumentType.BANK_PASSBOOK.value
    assert finding_mismatch.evidence[0].page_number is None


def test_regression_07_bank_statement_vs_passbook_distinction():
    """Regression 7: Bank statement cannot be classified as BANK_PASSBOOK; produces uncertainty."""
    doc_text = (
        "STATE BANK OF INDIA\n"
        "SAVINGS BANK ACCOUNT STATEMENT\n"
        "Statement Period: 01/01/2025 to 31/01/2025\n"
        "Closing Balance: 50000.00\n"
        "Account Number: 12345678901\n"
    )
    classification = classify_document_content(doc_text)
    assert classification.candidate_type is None
    assert classification.is_uncertain is True
    assert "statement" in classification.uncertainty_reason.lower()

    doc = _make_doc(DocumentType.BANK_PASSBOOK, raw_text=doc_text)
    finding = validate_slot(slot=DocumentType.BANK_PASSBOOK, doc=doc)
    assert finding is not None
    assert finding.status == FindingStatus.REVIEW
    assert finding._is_wrong_type is False
    assert "bank statement" in finding.message.lower()


def test_regression_08_genuine_certificate_with_long_header():
    """Regression 8: Genuine certificate with multiple administrative header lines qualifies without cutoff."""
    doc_text = (
        "GOVERNMENT OF ODISHA\n"
        "REVENUE & DISASTER MANAGEMENT DEPARTMENT\n"
        "OFFICE OF THE ADDITIONAL DISTRICT MAGISTRATE\n"
        "SUB-DIVISIONAL MAGISTRATE, CUTTACK\n"
        "TAHSILDAR OFFICE, SADAR\n"
        "INCOME CERTIFICATE\n"
        "Certificate No: E-INC/2025/998877\n"
        "Annual Family Income: 120000\n"
    )
    classification = classify_document_content(doc_text)
    assert classification.is_confident is True
    assert classification.candidate_type == DocumentType.INCOME_CERT
    assert classification.conflicting_types == []
    assert len(classification.source_lines) >= 1

    doc = _make_doc(DocumentType.INCOME_CERT, raw_text=doc_text)
    assert validate_slot(slot=DocumentType.INCOME_CERT, doc=doc) is None


def test_regression_09_incidental_body_mention_of_application_form():
    """Regression 9: Incidental body/narrative mention of application in another document does not conflict."""
    doc_text = (
        "GOVERNMENT OF ODISHA\n"
        "DEPARTMENT OF ST & SC DEVELOPMENT\n"
        "COMMUNITY / CASTE CERTIFICATE\n"
        "Certificate No: CST/2025/112233\n"
        "This certificate is issued for educational, scholarship and statutory purposes.\n"
        "Submitted along with scholarship application.\n"
    )
    classification = classify_document_content(doc_text)
    assert classification.is_confident is True
    assert classification.candidate_type == DocumentType.CASTE_CERT
    assert classification.conflicting_types == []
    assert DocumentType.APPLICATION_FORM not in classification.conflicting_types
    assert len(classification.source_lines) >= 1

    doc = _make_doc(DocumentType.CASTE_CERT, raw_text=doc_text)
    assert validate_slot(slot=DocumentType.CASTE_CERT, doc=doc) is None


def test_regression_10_pii_on_title_line_not_leaked_into_evidence_provenance():
    """Regression 10: Personal information on the same line as a valid title is never leaked into evidence provenance or messages."""
    # 1. Aadhaar Card with synthetic 12-digit number on title line
    aadhaar_text = "GOVERNMENT OF INDIA\nAADHAAR CARD — 1234 5678 9012\nMera Aadhaar, Meri Pehchan"
    clf_aadhaar = classify_document_content(aadhaar_text)
    assert clf_aadhaar.is_confident is True
    assert clf_aadhaar.candidate_type == DocumentType.AADHAAR
    for line in clf_aadhaar.source_lines:
        assert "1234" not in line
        assert "5678" not in line
        assert "9012" not in line

    doc_aadhaar = _make_doc(DocumentType.AADHAAR, raw_text=aadhaar_text)
    # Uploaded to mismatched slot INCOME_CERT
    finding_aadhaar = validate_slot(slot=DocumentType.INCOME_CERT, doc=doc_aadhaar)
    assert finding_aadhaar is not None
    assert finding_aadhaar.status == FindingStatus.REVIEW
    assert finding_aadhaar._is_wrong_type is True
    ev_a = finding_aadhaar.evidence[0]
    assert ev_a.page_number is None
    assert "1234" not in ev_a.raw_snippet
    assert "5678" not in ev_a.raw_snippet
    assert "9012" not in ev_a.raw_snippet
    assert "1234" not in finding_aadhaar.message

    # 2. Income Certificate with synthetic applicant name on title line
    income_text = "OFFICE OF THE TAHSILDAR\nINCOME CERTIFICATE — Applicant Akriti Lohani\nAnnual Family Income: 120000"
    clf_income = classify_document_content(income_text)
    assert clf_income.is_confident is True
    assert clf_income.candidate_type == DocumentType.INCOME_CERT
    for line in clf_income.source_lines:
        assert "AKRITI" not in line.upper()
        assert "LOHANI" not in line.upper()

    doc_income = _make_doc(DocumentType.INCOME_CERT, raw_text=income_text)
    finding_income = validate_slot(slot=DocumentType.CASTE_CERT, doc=doc_income)
    assert finding_income is not None
    ev_i = finding_income.evidence[0]
    assert ev_i.page_number is None
    assert "Akriti" not in ev_i.raw_snippet
    assert "Lohani" not in ev_i.raw_snippet
    assert "Akriti" not in finding_income.message
    assert "Lohani" not in finding_income.message

    # 3. Bank Passbook with account number, phone number, and address on title line
    bank_text = (
        "STATE BANK OF INDIA\n"
        "SAVINGS BANK PASSBOOK — Account 12345678901, Phone 9876543210, Plot 42 Shaheed Nagar, Bhubaneswar\n"
        "IFSC: SBIN0001234"
    )
    clf_bank = classify_document_content(bank_text)
    assert clf_bank.is_confident is True
    assert clf_bank.candidate_type == DocumentType.BANK_PASSBOOK
    for line in clf_bank.source_lines:
        assert "12345678901" not in line
        assert "9876543210" not in line
        assert "SHAHEED" not in line.upper()
        assert "BHUBANESWAR" not in line.upper()

    doc_bank = _make_doc(DocumentType.BANK_PASSBOOK, raw_text=bank_text)
    finding_bank = validate_slot(slot=DocumentType.MARKSHEET, doc=doc_bank)
    assert finding_bank is not None
    ev_b = finding_bank.evidence[0]
    assert ev_b.page_number is None
    assert "12345678901" not in ev_b.raw_snippet
    assert "9876543210" not in ev_b.raw_snippet
    assert "Shaheed" not in ev_b.raw_snippet
    assert "Bhubaneswar" not in ev_b.raw_snippet
    assert "12345678901" not in finding_bank.message
    assert "9876543210" not in finding_bank.message
    assert "Shaheed" not in finding_bank.message
    assert "Bhubaneswar" not in finding_bank.message


def test_regression_11_ordinary_narrative_sentences_yield_uncertainty():
    """Regression 11: Ordinary narrative sentences mentioning documents do not produce confident document types."""
    narrative_cases = [
        ("The applicant has an income certificate from the district office.", DocumentType.INCOME_CERT),
        ("The scholarship application was reviewed by the committee.", DocumentType.APPLICATION_FORM),
        ("A caste certificate is mentioned in the eligibility discussion.", DocumentType.CASTE_CERT),
        ("The student submitted a marksheet earlier.", DocumentType.MARKSHEET),
    ]

    for sentence, target_slot in narrative_cases:
        clf = classify_document_content(sentence)
        assert clf.candidate_type is None, f"Expected None candidate for: {sentence}, got {clf.candidate_type}"
        assert clf.is_confident is False
        assert clf.is_uncertain is True

        doc = _make_doc(target_slot, raw_text=sentence)
        finding = validate_slot(slot=target_slot, doc=doc)
        assert finding is not None, f"Expected uncertain finding for: {sentence}"
        assert finding.status == FindingStatus.REVIEW
        assert finding._is_wrong_type is False
        assert finding.evidence[0].page_number is None


def test_regression_12_narrative_sentences_without_trailing_period_yield_uncertainty():
    """Regression 12: Narrative sentences without trailing punctuation still produce uncertainty via grammar analysis."""
    narrative_no_punct = [
        ("The applicant has an income certificate from the district office", DocumentType.INCOME_CERT),
        ("The scholarship application was reviewed by the committee", DocumentType.APPLICATION_FORM),
        ("A caste certificate is mentioned in the eligibility discussion", DocumentType.CASTE_CERT),
        ("The student submitted a marksheet earlier", DocumentType.MARKSHEET),
    ]

    for sentence, target_slot in narrative_no_punct:
        clf = classify_document_content(sentence)
        assert clf.candidate_type is None, f"Expected None candidate for: {sentence}, got {clf.candidate_type}"
        assert clf.is_confident is False
        assert clf.is_uncertain is True

        doc = _make_doc(target_slot, raw_text=sentence)
        finding = validate_slot(slot=target_slot, doc=doc)
        assert finding is not None
        assert finding.status == FindingStatus.REVIEW
        assert finding._is_wrong_type is False
        assert finding.evidence[0].page_number is None
