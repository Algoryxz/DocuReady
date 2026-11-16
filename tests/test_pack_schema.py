"""Unit tests for Scheme Pack and Source Manifest Pydantic schemas (Task T3.1)."""

from datetime import date
import pytest
from pydantic import ValidationError

from docuready.domain.enums import MaxSeverity
from docuready.rules.schema import (
    CitationReference,
    DateRange,
    DocSlotDefinition,
    PackManifest,
    PackStatus,
    RemediationMetadata,
    RuleDefinition,
    SourceDefinition,
    SourceManifest,
    SourceStatus,
)


def test_pack_status_and_source_status_enums():
    assert PackStatus.DRAFT.value == "draft"
    assert PackStatus.DEMO_SNAPSHOT.value == "demo_snapshot"
    assert PackStatus.VERIFIED.value == "verified"

    assert SourceStatus.VERIFIED.value == "verified"
    assert SourceStatus.PLACEHOLDER.value == "placeholder"
    assert SourceStatus.UNVERIFIED.value == "unverified"


def test_date_range_valid_and_invalid():
    # Valid range
    dr = DateRange(from_date=date(2026, 4, 1), to_date=date(2026, 4, 30))
    assert dr.from_date == date(2026, 4, 1)
    assert dr.to_date == date(2026, 4, 30)

    # Valid with aliases from and to
    dr_alias = DateRange.model_validate({"from": "2026-04-01", "to": "2026-04-30"})
    assert dr_alias.from_date == date(2026, 4, 1)
    assert dr_alias.to_date == date(2026, 4, 30)

    # Valid open-ended
    dr_open = DateRange.model_validate({"from": "2026-04-01"})
    assert dr_open.from_date == date(2026, 4, 1)
    assert dr_open.to_date is None

    # Invalid range: from > to
    with pytest.raises(ValidationError) as exc:
        DateRange.model_validate({"from": "2026-05-01", "to": "2026-04-01"})
    assert "Effective date range invalid" in str(exc.value)


def test_doc_slot_definition_defaults_and_forbid_extra():
    slot = DocSlotDefinition()
    assert slot.ocr_langs == ["eng"]
    assert slot.required is True

    # Extra fields forbidden
    with pytest.raises(ValidationError):
        DocSlotDefinition.model_validate({"ocr_langs": ["eng"], "extra_field": "disallowed"})


def test_rule_definition_validation():
    rule_data = {
        "id": "RULE-TEST-01",
        "primitive": "numeric_cap",
        "inputs": {"field": "income.annual", "docs": ["INCOME_CERT"]},
        "params": {"cap": 250000},
        "max_severity": "FAIL",
        "citation": {"source": "SRC-01", "clause": "Clause 3.1"},
        "remediation": {
            "authority": "Tehsildar",
            "replacement_document": "INCOME_CERT",
            "steps": ["Apply online"],
        },
    }
    rule = RuleDefinition.model_validate(rule_data)
    assert rule.id == "RULE-TEST-01"
    assert rule.primitive == "numeric_cap"
    assert rule.max_severity == MaxSeverity.FAIL
    assert rule.citation.source == "SRC-01"
    assert rule.remediation.authority == "Tehsildar"

    # Empty id forbidden
    with pytest.raises(ValidationError):
        bad = dict(rule_data, id="   ")
        RuleDefinition.model_validate(bad)

    # Extra fields forbidden
    with pytest.raises(ValidationError):
        bad = dict(rule_data, unexpected_field="boom")
        RuleDefinition.model_validate(bad)


def test_pack_manifest_unique_rule_ids():
    rule1 = {
        "id": "RULE-DUP-01",
        "primitive": "field_present",
        "max_severity": "FAIL",
        "citation": {"source": "S1"},
        "remediation": {"authority": "Auth"},
    }
    rule2 = {
        "id": "RULE-DUP-01",
        "primitive": "field_present",
        "max_severity": "WARN",
        "citation": {"source": "S1"},
        "remediation": {"authority": "Auth"},
    }

    manifest_data = {
        "pack_id": "test.pack",
        "version": "1.0.0",
        "status": "draft",
        "rules": [rule1, rule2],
    }

    with pytest.raises(ValidationError) as exc:
        PackManifest.model_validate(manifest_data)
    assert "Duplicate rule id 'RULE-DUP-01'" in str(exc.value)


def test_source_definition_alias_normalization():
    src_data = {
        "id": "SRC-01",
        "source_title": "Centrally Sponsored Scheme Guidelines",
        "issuing_body": "MSJE",
        "official_url": "https://socialjustice.gov.in/schemes/31",
        "retrieval_date": "2026-11-15",
        "status": "verified",
        "reviewed_by": "Deeptiman",
        "clause": "Section 7",
        "supports_rule": True,
    }
    src = SourceDefinition.model_validate(src_data)
    assert src.id == "SRC-01"
    assert src.title == "Centrally Sponsored Scheme Guidelines"
    assert src.url == "https://socialjustice.gov.in/schemes/31"
    assert src.retrieved_on == date(2026, 11, 15)


def test_source_manifest_unique_source_ids():
    s1 = {
        "id": "SRC-01",
        "title": "T1",
        "issuing_body": "B1",
        "status": "verified",
    }
    s2 = {
        "id": "SRC-01",
        "title": "T2",
        "issuing_body": "B2",
        "status": "unverified",
    }
    manifest_data = {
        "pack_id": "test.pack",
        "version": "1.0.0",
        "sources": [s1, s2],
    }
    with pytest.raises(ValidationError) as exc:
        SourceManifest.model_validate(manifest_data)
    assert "Duplicate source id 'SRC-01'" in str(exc.value)
