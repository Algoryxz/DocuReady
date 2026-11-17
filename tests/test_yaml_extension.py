"""Test YAML-only Rule Extension (Task T3.2).

Demonstrates that a new statutory requirement can be added entirely through
declarative YAML configuration without editing any Python source code, while
leveraging the closed primitive registry and safe linter.
"""

from datetime import date
from pathlib import Path
import pytest

from docuready.domain.enums import Readiness, Status
from docuready.domain.models import DocumentType, ExtractedDocument, ExtractedField
from docuready.rules.engine import PackExecutionEngine
from docuready.rules.loader import load_pack
from docuready.rules.primitives import ExecutionContext


def test_yaml_only_rule_extension(tmp_path: Path):
    """Demonstrate adding a synthetic age eligibility rule entirely in YAML."""
    pack_dir = tmp_path / "custom.scheme"
    pack_dir.mkdir(parents=True)

    sources_yaml = """
pack_id: custom.scheme
version: "1.0.0"
sources:
  - id: "SRC-AGE-01"
    title: "National Youth Skill Development Guidelines 2026"
    issuing_body: "Ministry of Skill Development"
    url: "https://example.gov.in/guidelines"
    retrieved_on: "2026-11-15"
    status: "verified"
    reviewed_by: "Deeptiman (Product Owner)"
    clause: "Section 4.1 (Age Eligibility)"
    supports_rule: true
"""
    # New rule declared purely in YAML using existing closed primitive 'age_on'
    pack_yaml = """
pack_id: custom.scheme
version: "1.0.0"
status: verified

parameters:
  min_applicant_age:
    type: int
    value: 18
    description: "Minimum age required on audit date"
  max_applicant_age:
    type: int
    value: 25
    description: "Maximum age permitted on audit date"

doc_slots:
  application_form:
    ocr_langs: [eng]
    required: true

rules:
  - id: RULE-AGE-ELIGIBILITY
    primitive: age_on
    inputs:
      dob_field: dob
      docs: [application_form]
    params:
      min_age: $min_applicant_age
      max_age: $max_applicant_age
    max_severity: FAIL
    citation:
      source: SRC-AGE-01
      clause: "Section 4.1"
    remediation:
      authority: "Ministry of Skill Development"
      steps:
        - "Applicant must be between 18 and 25 years of age as of audit date."
"""
    (pack_dir / "sources.yaml").write_text(sources_yaml.strip(), encoding="utf-8")
    (pack_dir / "pack.yaml").write_text(pack_yaml.strip(), encoding="utf-8")

    # Load and execute the purely declarative custom pack
    engine = PackExecutionEngine(pack_dir)

    # 1. Test eligible candidate (DOB 2005-08-15 -> age 21 on 2026-11-15)
    eligible_packet = {
        DocumentType.APPLICATION_FORM: ExtractedDocument(
            doc_type=DocumentType.APPLICATION_FORM,
            file_path="application_form.pdf",
            status="VALID",
            fields={
                "dob": ExtractedField(
                    field_name="dob",
                    raw_value="15/08/2005",
                    normalized_value="15/08/2005",
                )
            },
        )
    }

    result_eligible = engine.validate_packet("ELIGIBLE_001", eligible_packet, as_of=date(2026, 11, 15))
    assert result_eligible.readiness is Readiness.NO_ISSUES_FOUND
    finding = result_eligible.findings[0]
    assert finding.rule_id == "RULE-AGE-ELIGIBILITY"
    assert finding.resolved_status is Status.PASS
    assert "satisfies age eligibility criteria" in finding.message

    # 2. Test ineligible candidate (DOB 1995-08-15 -> age 31 on 2026-11-15, exceeds max 25)
    ineligible_packet = {
        DocumentType.APPLICATION_FORM: ExtractedDocument(
            doc_type=DocumentType.APPLICATION_FORM,
            file_path="application_form.pdf",
            status="VALID",
            fields={
                "dob": ExtractedField(
                    field_name="dob",
                    raw_value="15/08/1995",
                    normalized_value="15/08/1995",
                )
            },
        )
    }

    result_ineligible = engine.validate_packet("INELIGIBLE_001", ineligible_packet, as_of=date(2026, 11, 15))
    assert result_ineligible.readiness is Readiness.NOT_READY
    finding_bad = result_ineligible.findings[0]
    assert finding_bad.rule_id == "RULE-AGE-ELIGIBILITY"
    assert finding_bad.resolved_status is Status.FAIL
    assert "exceeds statutory maximum 25 years" in finding_bad.message
