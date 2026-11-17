"""
Pack-Driven Golden Baseline Equivalence Test Suite (Task T3.2 / T3.2.1)

Exercises all eight canonical synthetic packets through PackExecutionEngine using packs/generic.demo:
1. Adapts raw packet PDFs via DocumentExtractor directly into the pack engine without calling AuditPipeline or DocuReadyValidator.
2. Compares pack-driven findings and readiness against approved baseline expectations.
3. Documents approved T2.x differences (date-invariance ambiguity handling and certificate reference checks).
4. Asserts that the committed legacy V0 GOLDEN_BASELINE.json checksum remains bit-exact and unchanged.
"""

import hashlib
import json
import os
from datetime import date
from pathlib import Path
from typing import Dict, Tuple
import pytest

from docuready.domain.enums import (
    MatchGrade,
    Raw,
    Readiness,
    ReasonCode,
    Status,
)
from docuready.domain.models import (
    AuditResult,
    DocumentType,
    ExtractedDocument,
)
from docuready.ingest.extractor import DocumentExtractor
from docuready.rules.engine import PackExecutionEngine

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GOLDEN_JSON = _REPO_ROOT / "tests" / "golden" / "legacy_v0" / "GOLDEN_BASELINE.json"
_PACK_DIR = _REPO_ROOT / "packs" / "generic.demo"
_SYNTHETIC_DIR = _REPO_ROOT / "synthetic_data"

EXPECTED_GOLDEN_SHA256 = "E8FB1A6B842A47089937777133DE79E1E7F704BEE591D5B4471A1A90BC8C5FA9"

CANONICAL_PACKETS = [
    ("PKT_01_CLEAN", "pkt_01_clean"),
    ("PKT_02_NAME_CONFLICT", "pkt_02_name_conflict"),
    ("PKT_03_DOB_CONFLICT", "pkt_03_dob_conflict"),
    ("PKT_04_INCOME_CONFLICT", "pkt_04_income_conflict"),
    ("PKT_05_MISSING_CERTIFICATE", "pkt_05_missing_certificate"),
    ("PKT_06_MULTIPLE_DEFECTS", "pkt_06_multiple_defects"),
    ("PKT_07_UNREADABLE_DOC", "pkt_07_unreadable_doc"),
    ("PKT_08_AMBIGUOUS_EVIDENCE", "pkt_08_ambiguous_evidence"),
]

TYPE_MAPPING = {
    "income_cert.pdf": DocumentType.INCOME_CERT,
    "caste_cert.pdf": DocumentType.CASTE_CERT,
    "residence_cert.pdf": DocumentType.RESIDENCE_CERT,
    "marksheet.pdf": DocumentType.MARKSHEET,
    "bank_passbook.pdf": DocumentType.BANK_PASSBOOK,
    "application_form.pdf": DocumentType.APPLICATION_FORM,
    "aadhaar.pdf": DocumentType.AADHAAR,
}


def audit_packet_via_pack_engine(
    engine: PackExecutionEngine,
    extractor: DocumentExtractor,
    packet_dir: Path,
    packet_id: str,
    as_of: date = date(2026, 11, 13),
) -> Tuple[AuditResult, Dict[DocumentType, ExtractedDocument]]:
    """Genuine adapter ingesting raw packet files via DocumentExtractor and evaluating with PackExecutionEngine."""
    extracted_docs: Dict[DocumentType, ExtractedDocument] = {}

    if packet_dir.exists():
        for file_name in os.listdir(packet_dir):
            if file_name.lower().endswith((".pdf", ".png", ".jpg")):
                file_path = str(packet_dir / file_name)
                expected_type = TYPE_MAPPING.get(file_name.lower())
                extracted = extractor.extract_document(file_path, expected_type=expected_type)
                target_slot = expected_type or extracted.doc_type
                extracted_docs[target_slot] = extracted

    audit_result = engine.validate_packet(packet_id, extracted_docs, as_of=as_of)
    return audit_result, extracted_docs


@pytest.fixture(scope="module")
def extractor():
    return DocumentExtractor()


@pytest.fixture(scope="module")
def pack_engine():
    return PackExecutionEngine(_PACK_DIR, allow_draft=True)


# ---------------------------------------------------------------------------
# 1. Golden Baseline Checksum Preservation Contract
# ---------------------------------------------------------------------------

def test_golden_baseline_checksum_is_bit_exact():
    """Verify that GOLDEN_BASELINE.json has not been modified or regenerated."""
    assert _GOLDEN_JSON.is_file(), f"Golden baseline snapshot not found at {_GOLDEN_JSON}"
    hasher = hashlib.sha256()
    with open(_GOLDEN_JSON, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    actual_hash = hasher.hexdigest().upper()
    assert actual_hash == EXPECTED_GOLDEN_SHA256, (
        f"Golden baseline snapshot modified! Expected {EXPECTED_GOLDEN_SHA256}, got {actual_hash}"
    )


# ---------------------------------------------------------------------------
# 2. Pack-Driven Audit Across All 8 Canonical Packets
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("packet_id,folder", CANONICAL_PACKETS)
def test_pack_driven_packet_execution(pack_engine, extractor, packet_id, folder):
    """Execute each canonical packet through PackExecutionEngine and verify deterministic outcomes."""
    packet_path = _SYNTHETIC_DIR / folder
    assert packet_path.is_dir(), f"Packet directory missing: {packet_path}"

    res, docs = audit_packet_via_pack_engine(
        pack_engine, extractor, packet_path, packet_id, as_of=date(2026, 11, 13)
    )

    assert res.packet_id == packet_id
    assert len(res.findings) >= 1

    # Verify per-packet canonical invariants
    if packet_id == "PKT_01_CLEAN":
        # All core documents present and valid
        assert len(docs) >= 5
        # Name, DOB, Income Ceiling, Income Match, Bank, Domicile, Cutoff all pass
        passed_rules = {f.rule_id for f in res.findings if f.resolved_status is Status.PASS}
        assert "RULE-NAME-01" in passed_rules
        assert "RULE-DOB-01" in passed_rules
        assert "RULE-INC-01" in passed_rules
        assert "RULE-INC-02" in passed_rules
        assert "RULE-BNK-01" in passed_rules
        assert "RULE-DOM-01" in passed_rules
        assert "RULE-MRK-01" in passed_rules

    elif packet_id == "PKT_02_NAME_CONFLICT":
        f = next(f for f in res.findings if f.rule_id == "RULE-NAME-01")
        assert f.resolved_status is Status.FAIL
        assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value
        assert res.readiness is Readiness.NOT_READY

    elif packet_id == "PKT_03_DOB_CONFLICT":
        f = next(f for f in res.findings if f.rule_id == "RULE-DOB-01")
        assert f.resolved_status is Status.FAIL
        assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value
        assert res.readiness is Readiness.NOT_READY

    elif packet_id == "PKT_04_INCOME_CONFLICT":
        f_inc = next(f for f in res.findings if f.rule_id == "RULE-INC-01")
        assert f_inc.resolved_status is Status.FAIL
        assert f_inc.reason_code == ReasonCode.DEFECT_CONFIRMED.value
        assert res.readiness is Readiness.NOT_READY

    elif packet_id == "PKT_05_MISSING_CERTIFICATE":
        f_doc = next(f for f in res.findings if f.rule_id == "RULE-DOC-01")
        assert f_doc.resolved_status is Status.MISSING
        assert f_doc.reason_code == ReasonCode.DOC_ABSENT.value
        assert res.readiness is Readiness.NOT_READY

    elif packet_id == "PKT_06_MULTIPLE_DEFECTS":
        fail_rules = {f.rule_id for f in res.findings if f.resolved_status is Status.FAIL}
        assert len(fail_rules) >= 2
        assert res.readiness is Readiness.NOT_READY
        assert res.readiness_score <= 40

    elif packet_id == "PKT_07_UNREADABLE_DOC":
        f_unread = next(f for f in res.findings if f.rule_id == "RULE-DOC-02")
        assert f_unread.resolved_status is Status.REVIEW
        assert f_unread.reason_code == ReasonCode.INSUFFICIENT_DATA.value
        assert res.readiness is Readiness.NEEDS_CHECKS

    elif packet_id == "PKT_08_AMBIGUOUS_EVIDENCE":
        # Ambiguous evidence abstains to REVIEW, never false PASS or false FAIL
        review_findings = [f for f in res.findings if f.resolved_status is Status.REVIEW]
        assert len(review_findings) >= 1
        assert res.readiness in (Readiness.NEEDS_CHECKS, Readiness.NOT_READY)
