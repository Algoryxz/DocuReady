"""Contract, domain, and boundary tests for the odisha.subhadra scheme pack (Task T3.3).

Verifies:
1. Pack manifest and source registry integrity against official W&CD Department records.
2. Exact clause references from Gazette No. 1637, Guidelines Letter No. 19188, and SOP Letter No. 26139.
3. Exclusive age boundary arithmetic (at least 21 and below 60 on 01.07.2024).
4. Aadhaar evidence semantics: scan absence/unreadability yields REVIEW, not statutory FAIL.
5. Income self-declaration under SOP Annexure 3: conditional on absence of NFSA/SFSS, capped at REVIEW.
6. Absence of fabricated FAIL-capable rules for external database exclusions (vehicles, land, taxes).
7. Application window marked UNVERIFIED in source registry.
8. Historical report header scoping.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict

import pytest

from docuready.domain.enums import (
    EvidenceState,
    MaxSeverity,
    Raw,
    Readiness,
    ReasonCode,
    Status,
)
from docuready.domain.models import (
    AuditResult,
    DEMO_SNAPSHOT_DISCLAIMER_BODY,
    DEMO_SNAPSHOT_DISCLAIMER_TITLE,
    DocumentType,
    EvidenceProvenance,
    ExtractedDocument,
    ExtractedField,
    Severity,
)
from docuready.report.exporter import (
    export_audit_report_json,
    generate_readiness_summary_markdown,
)
from docuready.rules.engine import PackExecutionEngine
from docuready.rules.lint import lint_pack
from docuready.rules.loader import load_pack
from docuready.rules.schema import PackStatus

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SUBHADRA_PACK_DIR = _REPO_ROOT / "packs" / "odisha.subhadra"


def _make_field(
    doc_type: str,
    name: str,
    raw: str,
    norm: Any = None,
    is_uncertain: bool = False,
) -> ExtractedField:
    return ExtractedField(
        field_name=name,
        raw_value=raw,
        normalized_value=norm if norm is not None else raw,
        is_uncertain=is_uncertain,
        provenance=EvidenceProvenance(
            document_type=doc_type,
            file_name=f"{doc_type.lower()}.pdf",
            extracted_field=name,
            raw_snippet=raw,
        ),
    )


def _make_subhadra_packet(
    dob: str = "15/05/1990",
    name: str = "Pravasini Sahoo",
    passbook_name: str | None = "Pravasini Sahoo",
    annual_income: float | None = None,
    nfsa_status: str | None = "NON_NFSA",
    nfsa_is_uncertain: bool = False,
    omit_aadhaar: bool = False,
    corrupt_aadhaar: bool = False,
    income_file_name: str = "income_declaration.pdf",
) -> Dict[DocumentType, ExtractedDocument]:
    packet: Dict[DocumentType, ExtractedDocument] = {}

    if not omit_aadhaar:
        packet[DocumentType.AADHAAR] = ExtractedDocument(
            doc_type=DocumentType.AADHAAR,
            file_path="aadhaar_card.pdf",
            status="UNREADABLE" if corrupt_aadhaar else "VALID",
            raw_text="Aadhaar Card" if not corrupt_aadhaar else "",
            fields={} if corrupt_aadhaar else {
                "applicant_name": _make_field("AADHAAR", "applicant_name", name),
                "dob": _make_field("AADHAAR", "dob", dob),
            },
        )

    if passbook_name is not None:
        packet[DocumentType.BANK_PASSBOOK] = ExtractedDocument(
            doc_type=DocumentType.BANK_PASSBOOK,
            file_path="bank_passbook.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_field("BANK_PASSBOOK", "applicant_name", passbook_name),
                "account_no": _make_field("BANK_PASSBOOK", "account_no", "987654321012"),
                "ifsc": _make_field("BANK_PASSBOOK", "ifsc", "SBIN0001234"),
            },
        )

    if annual_income is not None:
        packet[DocumentType.INCOME_CERT] = ExtractedDocument(
            doc_type=DocumentType.INCOME_CERT,
            file_path=income_file_name,
            status="VALID",
            fields={
                "annual_income": _make_field(
                    "INCOME_CERT", "annual_income", str(annual_income), annual_income
                ),
            },
        )

    if nfsa_status is not None:
        packet[DocumentType.APPLICATION_FORM] = ExtractedDocument(
            doc_type=DocumentType.APPLICATION_FORM,
            file_path="subhadra_application_form.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_field("APPLICATION_FORM", "applicant_name", name),
                "nfsa_sfss_status": _make_field(
                    "APPLICATION_FORM",
                    "nfsa_sfss_status",
                    nfsa_status,
                    is_uncertain=nfsa_is_uncertain,
                ),
            },
        )

    return packet


@pytest.fixture(scope="module")
def subhadra_engine() -> PackExecutionEngine:
    return PackExecutionEngine(_SUBHADRA_PACK_DIR)


# =============================================================================
# 1. Source Clause References & Verification Integrity
# =============================================================================

def test_subhadra_pack_lints_cleanly():
    """Verify that odisha.subhadra passes all linter invariants with 0 errors."""
    result = lint_pack(_SUBHADRA_PACK_DIR)
    assert result.is_valid, f"Lint failed: {result.errors}"
    assert len(result.errors) == 0


def test_subhadra_exact_official_clause_citations():
    """Verify that sources cite actual official clause numbers and URLs."""
    pack, sources = load_pack(_SUBHADRA_PACK_DIR)
    sources_by_id = {s.id: s for s in sources.sources}

    # 1. Guidelines (Letter No. 19188/WCD dated 29.08.2024): Sections 5.1, 5.2, 6, 7
    guidelines = sources_by_id.get("SRC-SUB-GUIDELINES-2024")
    assert guidelines is not None
    assert "19188" in guidelines.url
    assert "5.1" in guidelines.clause and "5.2" in guidelines.clause
    assert guidelines.status.value == "verified"
    assert guidelines.retrieved_on == date(2026, 11, 21)

    # 2. Gazette Resolution (No. 1637 dated 05.09.2024): Sections 1(e), 2(a), 3.1(c)–(e), 3.2, 5(a)(i), 5(a)(iii)
    gazette = sources_by_id.get("SRC-SUB-GAZETTE-2024")
    assert gazette is not None
    assert "1637" in gazette.url
    assert "2(a)" in gazette.clause and "3.1(c)" in gazette.clause and "5(a)(i)" in gazette.clause
    assert gazette.status.value == "verified"
    assert gazette.retrieved_on == date(2026, 11, 21)

    # 3. SOP (Letter No. 26139/WCD dated 11.11.2024): Sections 2, 4, 4.1, Annexure 3
    sop = sources_by_id.get("SRC-SUB-SOP-2024")
    assert sop is not None
    assert "26139" in sop.url
    assert "2" in sop.clause and "Annexure 3" in sop.clause
    assert sop.status.value == "verified"
    assert sop.retrieved_on == date(2026, 11, 21)

    # 4. Application Intake Window is UNVERIFIED
    window_src = sources_by_id.get("SRC-SUB-INTAKE-WINDOW")
    assert window_src is not None
    assert window_src.status.value == "unverified"
    assert window_src.supports_rule is False


def test_subhadra_rules_citation_clause_mapping():
    """Verify each declarative rule cites the exact official clause and RULE-SUB-DOC-01 is absent."""
    pack, _ = load_pack(_SUBHADRA_PACK_DIR)
    rules_by_id = {r.id: r for r in pack.rules}

    assert len(pack.rules) == 3
    assert len(pack.parameters) == 3
    assert "income_ceiling" not in pack.parameters
    assert "RULE-SUB-INC-01" not in rules_by_id
    assert "RULE-SUB-DOC-01" not in rules_by_id
    assert "aadhaar_card" in pack.doc_slots
    assert pack.doc_slots["aadhaar_card"].required is False

    assert rules_by_id["RULE-SUB-FLD-01"].citation.clause == "Section 2, Section 4.1"
    assert rules_by_id["RULE-SUB-AGE-01"].citation.clause == "Section 3.1(c)–(e)"
    assert rules_by_id["RULE-SUB-NAME-01"].citation.clause == "Section 1(e), Section 5(a)(iii)"


# =============================================================================
# 2. Aadhaar Evidence Semantics (Optional Upload; REVIEW Abstention)
# =============================================================================

def test_subhadra_aadhaar_scan_unavailable_yields_review_not_missing_or_fail(subhadra_engine):
    """Absence of optional Aadhaar scan yields no Status.MISSING; dependent rules (incl. NAME-01) abstain to REVIEW."""
    packet = _make_subhadra_packet(
        omit_aadhaar=True,
        passbook_name="Pravasini Sahoo",
        annual_income=None,
        nfsa_status=None,
    )
    result = subhadra_engine.validate_packet("PKT_NO_AADHAAR_SCAN", packet, as_of=date(2024, 7, 1))

    assert result.readiness is Readiness.NEEDS_CHECKS
    assert not any(f.resolved_status is Status.FAIL for f in result.findings)
    assert not any(f.resolved_status is Status.MISSING for f in result.findings)
    assert not any(f.rule_id in ("RULE-DOC-01", "RULE-SUB-DOC-01") for f in result.findings)

    f_fld = next((f for f in result.findings if f.rule_id == "RULE-SUB-FLD-01"), None)
    assert f_fld is not None
    assert f_fld.raw_result is Raw.INDETERMINATE
    assert f_fld.resolved_status is Status.REVIEW
    assert f_fld.reason_code == ReasonCode.INSUFFICIENT_DATA.value

    f_age = next((f for f in result.findings if f.rule_id == "RULE-SUB-AGE-01"), None)
    assert f_age is not None
    assert f_age.raw_result is Raw.INDETERMINATE
    assert f_age.resolved_status is Status.REVIEW
    assert f_age.reason_code == ReasonCode.INSUFFICIENT_DATA.value

    f_name = next((f for f in result.findings if f.rule_id == "RULE-SUB-NAME-01"), None)
    assert f_name is not None
    assert f_name.raw_result is Raw.INDETERMINATE
    assert f_name.resolved_status is Status.REVIEW
    assert f_name.reason_code == ReasonCode.INSUFFICIENT_DATA.value


def test_subhadra_unreadable_or_corrupted_aadhaar_yields_review_not_ineligibility(subhadra_engine):
    """Unreadable or corrupted Aadhaar scan yields REVIEW/INSUFFICIENT_DATA across all Aadhaar-dependent rules."""
    for bad_status in ("UNREADABLE", "CORRUPTED"):
        packet = {
            DocumentType.AADHAAR: ExtractedDocument(
                doc_type=DocumentType.AADHAAR,
                file_path="aadhaar_card.pdf",
                status=bad_status,
                raw_text="",
                fields={},
            ),
            DocumentType.BANK_PASSBOOK: ExtractedDocument(
                doc_type=DocumentType.BANK_PASSBOOK,
                file_path="bank_passbook.pdf",
                status="VALID",
                raw_text="SAVINGS BANK PASSBOOK",
                fields={
                    "applicant_name": _make_field("BANK_PASSBOOK", "applicant_name", "Pravasini Sahoo"),
                },
            ),
        }
        result = subhadra_engine.validate_packet(f"PKT_{bad_status}_AADHAAR", packet, as_of=date(2024, 7, 1))

        assert result.readiness is Readiness.NEEDS_CHECKS
        assert not any(f.resolved_status is Status.FAIL for f in result.findings)
        assert not any(f.resolved_status is Status.MISSING for f in result.findings)

        f_fld = next((f for f in result.findings if f.rule_id == "RULE-SUB-FLD-01"), None)
        assert f_fld is not None
        assert f_fld.raw_result is Raw.INDETERMINATE
        assert f_fld.resolved_status is Status.REVIEW
        assert f_fld.reason_code == ReasonCode.INSUFFICIENT_DATA.value

        f_age = next((f for f in result.findings if f.rule_id == "RULE-SUB-AGE-01"), None)
        assert f_age is not None
        assert f_age.raw_result is Raw.INDETERMINATE
        assert f_age.resolved_status is Status.REVIEW
        assert f_age.reason_code == ReasonCode.INSUFFICIENT_DATA.value

        f_name = next((f for f in result.findings if f.rule_id == "RULE-SUB-NAME-01"), None)
        assert f_name is not None
        assert f_name.raw_result is Raw.INDETERMINATE
        assert f_name.resolved_status is Status.REVIEW
        assert f_name.reason_code == ReasonCode.INSUFFICIENT_DATA.value


def test_subhadra_aadhaar_name_evidence_states_preserved(subhadra_engine):
    """RULE-SUB-FLD-01 preserves VERIFIED, PROVISIONAL, and UNCERTAIN evidence semantics."""
    for ev_state, is_unc, expected_status, expected_reason in (
        (EvidenceState.VERIFIED, False, Status.PASS, ReasonCode.CONFIRMED_OK.value),
        (EvidenceState.PROVISIONAL, False, Status.REVIEW, ReasonCode.CANNOT_CONFIRM.value),
        (EvidenceState.UNCERTAIN, True, Status.REVIEW, ReasonCode.CANNOT_CONFIRM.value),
    ):
        packet = _make_subhadra_packet(dob="15/05/1990", annual_income=180000.0)
        packet[DocumentType.AADHAAR].fields["applicant_name"] = ExtractedField(
            field_name="applicant_name",
            raw_value="Pravasini Sahoo",
            normalized_value="Pravasini Sahoo",
            evidence_state=ev_state,
            is_uncertain=is_unc,
        )
        result = subhadra_engine.validate_packet(f"PKT_SUB_FLD_{ev_state.value}", packet, as_of=date(2024, 7, 1))
        f_fld = next(f for f in result.findings if f.rule_id == "RULE-SUB-FLD-01")
        assert f_fld.raw_result is Raw.SATISFIED
        assert f_fld.resolved_status is expected_status
        assert f_fld.reason_code == expected_reason


# =============================================================================
# 3. Exact Age Boundary Tests (At least 21 and below 60 on 01.07.2024)
# =============================================================================

def test_subhadra_clean_packet_has_no_supported_document_findings(subhadra_engine):
    """No issues found in the currently implemented document checks. This result does not establish complete statutory eligibility or guarantee government acceptance."""
    packet = _make_subhadra_packet(dob="15/05/1990", annual_income=180000.0)
    result = subhadra_engine.validate_packet("PKT_SUB_CLEAN", packet, as_of=date(2024, 7, 1))
    assert result.readiness is Readiness.NO_ISSUES_FOUND
    assert result.readiness_score == 100

    f_age = next((f for f in result.findings if f.rule_id == "RULE-SUB-AGE-01"), None)
    assert f_age is not None
    assert f_age.resolved_status is Status.PASS


def test_subhadra_age_exact_lower_bound_eligible(subhadra_engine):
    """Woman born on 01.07.2003 turns exactly 21 on 01.07.2024: SATISFIED (§3.1(c))."""
    packet = _make_subhadra_packet(dob="01/07/2003", annual_income=180000.0)
    result = subhadra_engine.validate_packet("PKT_SUB_EXACT_21", packet, as_of=date(2024, 7, 1))
    f_age = next((f for f in result.findings if f.rule_id == "RULE-SUB-AGE-01"), None)
    assert f_age is not None
    assert f_age.resolved_status is Status.PASS


def test_subhadra_age_just_below_lower_bound_underage(subhadra_engine):
    """Woman born on 02.07.2003 is 20 years 364 days on 01.07.2024: VIOLATED (FAIL)."""
    packet = _make_subhadra_packet(dob="02/07/2003", annual_income=180000.0)
    result = subhadra_engine.validate_packet("PKT_SUB_UNDERAGE_20", packet, as_of=date(2024, 7, 1))
    assert result.readiness is Readiness.NOT_READY

    f_age = next((f for f in result.findings if f.rule_id == "RULE-SUB-AGE-01"), None)
    assert f_age is not None
    assert f_age.resolved_status is Status.FAIL
    assert "below statutory minimum" in f_age.message.lower()


def test_subhadra_age_exact_upper_bound_eligible(subhadra_engine):
    """Woman born on 02.07.1964 is 59 years 364 days on 01.07.2024: SATISFIED (strictly below 60)."""
    packet = _make_subhadra_packet(dob="02/07/1964", annual_income=180000.0)
    result = subhadra_engine.validate_packet("PKT_SUB_EXACT_59", packet, as_of=date(2024, 7, 1))
    f_age = next((f for f in result.findings if f.rule_id == "RULE-SUB-AGE-01"), None)
    assert f_age is not None
    assert f_age.resolved_status is Status.PASS


def test_subhadra_age_exact_upper_bound_excluded(subhadra_engine):
    """Woman born on 01.07.1964 completed exactly 60 years on 01.07.2024: VIOLATED (FAIL)."""
    packet = _make_subhadra_packet(dob="01/07/1964", annual_income=180000.0)
    result = subhadra_engine.validate_packet("PKT_SUB_EXACT_60", packet, as_of=date(2024, 7, 1))
    assert result.readiness is Readiness.NOT_READY

    f_age = next((f for f in result.findings if f.rule_id == "RULE-SUB-AGE-01"), None)
    assert f_age is not None
    assert f_age.resolved_status is Status.FAIL
    assert "exceeds statutory maximum" in f_age.message.lower()


def test_subhadra_statutory_age_reference_date_precedes_execution_context_as_of(subhadra_engine):
    """Statutory reference date (2024-07-01) takes precedence over runtime ExecutionContext.as_of date.

    An audit executed on 2026-11-21 against an applicant born on 02/07/2003:
    - At runtime as_of (2026-11-21), applicant is 23 years old (would pass).
    - As of statutory reference date (2024-07-01), applicant is 20 years 364 days old (must fail).
    This proves the configured reference_date ($age_reference_date) takes precedence over as_of.
    """
    # 1. Underage on 2024-07-01 (born 02/07/2003) fails even if audited in 2026
    packet_underage = _make_subhadra_packet(dob="02/07/2003", annual_income=180000.0)
    result_underage = subhadra_engine.validate_packet(
        "PKT_SUB_STATUTORY_REF_UNDERAGE", packet_underage, as_of=date(2026, 11, 21)
    )
    f_age_under = next((f for f in result_underage.findings if f.rule_id == "RULE-SUB-AGE-01"), None)
    assert f_age_under is not None
    assert f_age_under.resolved_status is Status.FAIL
    assert "below statutory minimum" in f_age_under.message.lower()

    # 2. Eligible on 2024-07-01 (born 02/07/1964) passes even if 62 years old in 2026
    packet_upper = _make_subhadra_packet(dob="02/07/1964", annual_income=180000.0)
    result_upper = subhadra_engine.validate_packet(
        "PKT_SUB_STATUTORY_REF_UPPER", packet_upper, as_of=date(2026, 11, 21)
    )
    f_age_upper = next((f for f in result_upper.findings if f.rule_id == "RULE-SUB-AGE-01"), None)
    assert f_age_upper is not None
    assert f_age_upper.resolved_status is Status.PASS


# =============================================================================
# 4. Income Conditional Applicability & Unimplemented Database Demarcation
# =============================================================================

def test_subhadra_applicant_declared_nfsa_cannot_establish_exemption(subhadra_engine):
    """Applicant-declared NFSA status cannot independently establish statutory exemption (NOT_APPLICABLE).

    Under Subhadra Guidelines §5.1, NFSA coverage exempts households from the ₹2.50 lakh
    income ceiling. However, DocuReady has no trusted government database verification
    interface (e.g. Odisha FS&CW portal). Therefore, applicant declarations cannot trigger
    an exemption verdict or NOT_APPLICABLE finding.
    """
    packet = _make_subhadra_packet(annual_income=None, nfsa_status="NFSA", nfsa_is_uncertain=False)
    result = subhadra_engine.validate_packet("PKT_SUB_NFSA_DECL", packet, as_of=date(2024, 7, 1))

    # No income rule exists to generate NOT_APPLICABLE
    assert not any(f.rule_id == "RULE-SUB-INC-01" for f in result.findings)
    assert not any(f.resolved_status is Status.NOT_APPLICABLE for f in result.findings)


def test_subhadra_applicant_declared_sfss_cannot_establish_exemption(subhadra_engine):
    """Applicant-declared SFSS status cannot independently establish statutory exemption (NOT_APPLICABLE)."""
    packet = _make_subhadra_packet(annual_income=None, nfsa_status="SFSS", nfsa_is_uncertain=False)
    result = subhadra_engine.validate_packet("PKT_SUB_SFSS_DECL", packet, as_of=date(2024, 7, 1))

    assert not any(f.rule_id == "RULE-SUB-INC-01" for f in result.findings)
    assert not any(f.resolved_status is Status.NOT_APPLICABLE for f in result.findings)


def test_subhadra_applicant_declared_non_nfsa_cannot_establish_income_ceiling_applies(subhadra_engine):
    """Applicant-declared NON_NFSA status cannot establish that the income ceiling applies.

    Without trusted government database coverage verification, applicant self-declarations
    cannot establish whether an applicant is subject to the ₹2.50 lakh income ceiling.
    No executable income ceiling rule evaluates the applicant.
    """
    packet = _make_subhadra_packet(annual_income=180000.0, nfsa_status="NON_NFSA")
    result = subhadra_engine.validate_packet("PKT_SUB_NON_NFSA", packet, as_of=date(2024, 7, 1))

    # The pack does not contain an income ceiling rule
    assert not any(f.rule_id == "RULE-SUB-INC-01" for f in result.findings)


def test_subhadra_unknown_coverage_status_cannot_generate_income_pass(subhadra_engine):
    """Unknown coverage status cannot generate an income eligibility PASS.

    A household with unknown NFSA/SFSS status cannot be evaluated as passing income criteria,
    because the applicability of the income cap itself is undetermined.
    """
    packet = _make_subhadra_packet(annual_income=150000.0, nfsa_status=None)
    result = subhadra_engine.validate_packet("PKT_SUB_UNKNOWN_COVERAGE", packet, as_of=date(2024, 7, 1))

    # No income rule passes or executes
    assert not any(f.rule_id == "RULE-SUB-INC-01" for f in result.findings)
    income_passes = [
        f for f in result.findings
        if "income" in f.rule_id.lower() and f.resolved_status is Status.PASS
    ]
    assert len(income_passes) == 0


def test_subhadra_absence_of_trusted_verification_does_not_generate_not_applicable(subhadra_engine):
    """The absence of trusted NFSA/SFSS verification does not generate NOT_APPLICABLE.

    Since no trusted government verification interface exists, the pack intentionally omits
    automated income ceiling evaluation rather than fabricating NOT_APPLICABLE verdicts.
    """
    packet = _make_subhadra_packet(annual_income=300000.0, nfsa_status="NFSA")
    result = subhadra_engine.validate_packet("PKT_SUB_NO_TRUSTED_VERIF", packet, as_of=date(2024, 7, 1))

    assert not any(f.resolved_status is Status.NOT_APPLICABLE for f in result.findings)


def test_subhadra_annexure_3_income_self_declaration_slot_mapping_only():
    """SOP Annexure 3 gross family annual income self-declaration is a slot-level mapping only.

    Demonstrates that Annexure 3 evidence maps into the applicant packet fact structure
    (e.g., INCOME_CERT annual_income or APPLICATION_FORM nfsa_sfss_status), but confirms
    that DocuReady does NOT treat this mapping as proof of automated statutory eligibility determination.
    """
    packet = _make_subhadra_packet(
        annual_income=180000.0,
        nfsa_status="NON_NFSA",
        income_file_name="sop_annexure_3_self_declaration.pdf",
    )
    # Slot-level extraction check: the fact is present in the extracted document fields
    inc_doc = packet.get(DocumentType.INCOME_CERT)
    assert inc_doc is not None
    assert inc_doc.file_path == "sop_annexure_3_self_declaration.pdf"
    assert inc_doc.fields["annual_income"].normalized_value == 180000.0

    app_form = packet.get(DocumentType.APPLICATION_FORM)
    assert app_form is not None
    assert app_form.fields["nfsa_sfss_status"].normalized_value == "NON_NFSA"

    # Confirm the pack does NOT evaluate this slot via an executable income rule
    pack, _ = load_pack(_SUBHADRA_PACK_DIR)
    rule_ids = {r.id for r in pack.rules}
    assert "RULE-SUB-INC-01" not in rule_ids


def test_subhadra_absence_of_optional_bank_passbook_does_not_fail(subhadra_engine):
    """Absence of optional bank passbook triggers name-reconciliation advisory, not rejection."""
    packet = _make_subhadra_packet(passbook_name=None, annual_income=180000.0)
    result = subhadra_engine.validate_packet("PKT_SUB_NO_PASSBOOK", packet, as_of=date(2024, 7, 1))
    assert result.readiness is Readiness.NEEDS_CHECKS
    assert not any(f.resolved_status is Status.FAIL for f in result.findings)

    f_name = next((f for f in result.findings if f.rule_id == "RULE-SUB-NAME-01"), None)
    assert f_name is not None
    assert f_name.resolved_status is Status.REVIEW


def test_subhadra_bank_passbook_name_mismatch_yields_review_not_fail(subhadra_engine):
    """Name discrepancy between Aadhaar and Bank Passbook yields advisory REVIEW."""
    packet = _make_subhadra_packet(
        name="Pravasini Sahoo", passbook_name="Pravasini Patra", annual_income=180000.0
    )
    result = subhadra_engine.validate_packet("PKT_SUB_NAME_MISMATCH", packet, as_of=date(2024, 7, 1))
    assert result.readiness is Readiness.NEEDS_CHECKS

    f_name = next((f for f in result.findings if f.rule_id == "RULE-SUB-NAME-01"), None)
    assert f_name is not None
    assert f_name.resolved_status is Status.REVIEW


# =============================================================================
# 5. External Database Exclusions & Report Header Formatting
# =============================================================================

def test_subhadra_external_database_exclusions_not_falsely_claimed():
    """Verify pack manifest does NOT fabricate FAIL-capable rules for unextracted exclusions."""
    pack, _ = load_pack(_SUBHADRA_PACK_DIR)
    rule_ids = {r.id for r in pack.rules}

    # Prohibited: rules pretending to check external tax, vehicle, or government employment DBs
    prohibited_fabrications = {
        "RULE-SUB-TAX-01",
        "RULE-SUB-VEHICLE-01",
        "RULE-SUB-GOV-EMP-01",
        "RULE-SUB-LAND-01",
    }
    overlap = rule_ids.intersection(prohibited_fabrications)
    assert not overlap, f"Prohibited fabricated rules found: {overlap}"

    # Exactly 3 declarative rules, 3 parameters, no income ceiling, no RULE-SUB-DOC-01
    assert len(pack.rules) == 3
    assert len(pack.parameters) == 3
    assert "income_ceiling" not in pack.parameters
    assert "RULE-SUB-INC-01" not in rule_ids
    assert "RULE-SUB-DOC-01" not in rule_ids

    # Only statutory age check is FAIL-capable
    fail_capable_rules = [r for r in pack.rules if r.max_severity == MaxSeverity.FAIL]
    assert len(fail_capable_rules) == 1
    assert fail_capable_rules[0].id == "RULE-SUB-AGE-01"


def test_subhadra_report_markdown_contains_approved_disclaimer(subhadra_engine):
    """Production Markdown exporter emits the exact PO-approved demo-snapshot disclaimer."""
    packet = _make_subhadra_packet(dob="15/05/1990", annual_income=180000.0)
    result = subhadra_engine.validate_packet("PKT_SUB_MD_DISC", packet, as_of=date(2024, 7, 1))
    assert result.pack_status == PackStatus.DEMO_SNAPSHOT.value

    md = generate_readiness_summary_markdown(result, redact=True)
    assert f"**{DEMO_SNAPSHOT_DISCLAIMER_TITLE}**" in md
    assert DEMO_SNAPSHOT_DISCLAIMER_BODY in md


def test_subhadra_report_json_contains_structured_disclaimer(subhadra_engine, tmp_path: Path):
    """Production JSON exporter preserves the demo-snapshot disclaimer in structured form without leaking pack_status."""
    packet = _make_subhadra_packet(dob="15/05/1990", annual_income=180000.0)
    result = subhadra_engine.validate_packet("PKT_SUB_JSON_DISC", packet, as_of=date(2024, 7, 1))

    out_path = tmp_path / "subhadra_report.json"
    export_audit_report_json(result, str(out_path), redact=True)
    payload = json.loads(out_path.read_text(encoding="utf-8"))

    assert "pack_status" not in payload
    assert payload["demo_snapshot_disclaimer"] == {
        "title": DEMO_SNAPSHOT_DISCLAIMER_TITLE,
        "body": DEMO_SNAPSHOT_DISCLAIMER_BODY,
    }

    # Canonical export retains the structured disclaimer without volatile fields
    canon_path = tmp_path / "subhadra_report_canonical.json"
    export_audit_report_json(result, str(canon_path), redact=True, canonical=True)
    canon_payload = json.loads(canon_path.read_text(encoding="utf-8"))
    assert canon_payload["demo_snapshot_disclaimer"] == {
        "title": DEMO_SNAPSHOT_DISCLAIMER_TITLE,
        "body": DEMO_SNAPSHOT_DISCLAIMER_BODY,
    }
    assert "execution_time_ms" not in canon_payload
    assert "timestamp" not in canon_payload


def test_non_demo_report_omits_subhadra_disclaimer_and_preserves_shape(tmp_path: Path):
    """Verified-pack and legacy (pack_status=None) reports omit demo_snapshot_disclaimer and pack_status."""
    base_kwargs = dict(
        packet_id="PKT_NON_DEMO",
        scheme_name="generic.demo",
        readiness_score=100,
        overall_status=Readiness.NO_ISSUES_FOUND,
        findings=[],
        summary_counts={},
        execution_time_ms=1.0,
        timestamp="2026-11-27T00:00:00",
    )
    legacy_result = AuditResult(**base_kwargs)
    verified_result = AuditResult(**base_kwargs, pack_status=PackStatus.VERIFIED.value)

    legacy_md = generate_readiness_summary_markdown(legacy_result, redact=True)
    verified_md = generate_readiness_summary_markdown(verified_result, redact=True)
    assert DEMO_SNAPSHOT_DISCLAIMER_TITLE not in legacy_md
    assert DEMO_SNAPSHOT_DISCLAIMER_BODY not in legacy_md
    assert verified_md == legacy_md

    legacy_path = tmp_path / "non_demo_legacy.json"
    verified_path = tmp_path / "non_demo_verified.json"
    export_audit_report_json(legacy_result, str(legacy_path), redact=True)
    export_audit_report_json(verified_result, str(verified_path), redact=True)
    legacy_payload = json.loads(legacy_path.read_text(encoding="utf-8"))
    verified_payload = json.loads(verified_path.read_text(encoding="utf-8"))

    for payload in (legacy_payload, verified_payload):
        assert "demo_snapshot_disclaimer" not in payload
        assert "pack_status" not in payload
    assert verified_payload == legacy_payload
