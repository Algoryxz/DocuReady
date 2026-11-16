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
    ParameterDeclaration,
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


def test_rule_definition_validation_and_required_fields():
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

    # Missing citation rejected
    with pytest.raises(ValidationError):
        bad = dict(rule_data)
        del bad["citation"]
        RuleDefinition.model_validate(bad)

    # Missing remediation rejected
    with pytest.raises(ValidationError):
        bad = dict(rule_data)
        del bad["remediation"]
        RuleDefinition.model_validate(bad)

    # Missing max_severity rejected
    with pytest.raises(ValidationError):
        bad = dict(rule_data)
        del bad["max_severity"]
        RuleDefinition.model_validate(bad)

    # Empty rule id rejected
    with pytest.raises(ValidationError):
        bad = dict(rule_data, id="   ")
        RuleDefinition.model_validate(bad)

    # Empty primitive rejected
    with pytest.raises(ValidationError):
        bad = dict(rule_data, primitive="   ")
        RuleDefinition.model_validate(bad)

    # Extra fields forbidden
    with pytest.raises(ValidationError):
        bad = dict(rule_data, unexpected_field="boom")
        RuleDefinition.model_validate(bad)


def test_citation_reference_and_remediation_non_empty():
    # Empty citation source rejected
    with pytest.raises(ValidationError):
        CitationReference.model_validate({"source": "  "})

    # Empty remediation authority rejected
    with pytest.raises(ValidationError):
        RemediationMetadata.model_validate({"authority": "   "})


def test_parameter_declaration_validation():
    # Valid declarations across all supported types
    p_int = ParameterDeclaration.model_validate({"type": "int", "value": 250000})
    assert p_int.type == "int"
    assert p_int.value == 250000

    p_float = ParameterDeclaration.model_validate({"type": "float", "value": 3.14})
    assert p_float.type == "float"
    assert p_float.value == 3.14

    p_float_int = ParameterDeclaration.model_validate({"type": "float", "value": 10})
    assert p_float_int.type == "float"
    assert p_float_int.value == 10

    p_num = ParameterDeclaration.model_validate({"type": "number", "value": 100})
    assert p_num.type == "number"
    assert p_num.value == 100

    p_str = ParameterDeclaration.model_validate({"type": "string", "value": "test"})
    assert p_str.type == "string"
    assert p_str.value == "test"

    p_str_alias = ParameterDeclaration.model_validate({"type": "str", "value": "demo"})
    assert p_str_alias.type == "str"
    assert p_str_alias.value == "demo"

    p_bool = ParameterDeclaration.model_validate({"type": "bool", "value": True})
    assert p_bool.type == "bool"
    assert p_bool.value is True

    p_boolean = ParameterDeclaration.model_validate({"type": "boolean", "value": False})
    assert p_boolean.type == "boolean"
    assert p_boolean.value is False

    p_date_obj = ParameterDeclaration.model_validate({"type": "date", "value": date(2026, 4, 1)})
    assert p_date_obj.type == "date"
    assert p_date_obj.value == date(2026, 4, 1)

    p_date_str = ParameterDeclaration.model_validate({"type": "date", "value": "2026-04-15"})
    assert p_date_str.type == "date"
    assert p_date_str.value == "2026-04-15"

    p_list = ParameterDeclaration.model_validate({"type": "list", "value": ["a", "b"]})
    assert p_list.type == "list"
    assert p_list.value == ["a", "b"]

    # Boundary cases: omitted value permitted at schema level
    p_none = ParameterDeclaration.model_validate({"type": "int", "value": None})
    assert p_none.type == "int"
    assert p_none.value is None

    p_omitted = ParameterDeclaration.model_validate({"type": "string"})
    assert p_omitted.type == "string"
    assert p_omitted.value is None

    # Invalid declared type
    with pytest.raises(ValidationError) as exc:
        ParameterDeclaration.model_validate({"type": "unknown_type"})
    assert "Invalid parameter type" in str(exc.value)

    # Type/value inconsistencies across all types
    # 1. int cannot be boolean or string
    with pytest.raises(ValidationError) as exc:
        ParameterDeclaration.model_validate({"type": "int", "value": True})
    assert "Parameter of type 'int' must contain an integer" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        ParameterDeclaration.model_validate({"type": "int", "value": "250000"})
    assert "Parameter of type 'int' must contain an integer" in str(exc.value)

    # 2. float cannot be boolean or string
    with pytest.raises(ValidationError) as exc:
        ParameterDeclaration.model_validate({"type": "float", "value": False})
    assert "Parameter of type 'float' must contain a valid numeric value" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        ParameterDeclaration.model_validate({"type": "float", "value": "3.14"})
    assert "Parameter of type 'float' must contain a valid numeric value" in str(exc.value)

    # 3. number cannot be boolean or string
    with pytest.raises(ValidationError) as exc:
        ParameterDeclaration.model_validate({"type": "number", "value": True})
    assert "Parameter of type 'number' must contain an integer or float" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        ParameterDeclaration.model_validate({"type": "number", "value": "100"})
    assert "Parameter of type 'number' must contain an integer or float" in str(exc.value)

    # 4. string cannot be int or bool
    with pytest.raises(ValidationError) as exc:
        ParameterDeclaration.model_validate({"type": "string", "value": 123})
    assert "Parameter of type 'string' must contain a string" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        ParameterDeclaration.model_validate({"type": "string", "value": True})
    assert "Parameter of type 'string' must contain a string" in str(exc.value)

    # 5. bool cannot be int or string
    with pytest.raises(ValidationError) as exc:
        ParameterDeclaration.model_validate({"type": "bool", "value": 1})
    assert "Parameter of type 'bool' must contain a boolean" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        ParameterDeclaration.model_validate({"type": "bool", "value": "true"})
    assert "Parameter of type 'bool' must contain a boolean" in str(exc.value)

    # 6. date cannot be bool, int, or malformed string
    with pytest.raises(ValidationError) as exc:
        ParameterDeclaration.model_validate({"type": "date", "value": True})
    assert "Parameter of type 'date' cannot be a boolean" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        ParameterDeclaration.model_validate({"type": "date", "value": 20260401})
    assert "Parameter of type 'date' must contain a valid date representation" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        ParameterDeclaration.model_validate({"type": "date", "value": "not-a-date"})
    assert "invalid date string" in str(exc.value)

    # 7. list cannot be string or int
    with pytest.raises(ValidationError) as exc:
        ParameterDeclaration.model_validate({"type": "list", "value": "not a list"})
    assert "Parameter of type 'list' must contain a list" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        ParameterDeclaration.model_validate({"type": "list", "value": 123})
    assert "Parameter of type 'list' must contain a list" in str(exc.value)


def test_pack_manifest_unique_rule_ids_and_typed_parameters():
    rule1 = {
        "id": "RULE-01",
        "primitive": "field_present",
        "max_severity": "FAIL",
        "citation": {"source": "S1"},
        "remediation": {"authority": "Auth"},
    }
    rule2 = {
        "id": "RULE-02",
        "primitive": "field_present",
        "max_severity": "WARN",
        "citation": {"source": "S1"},
        "remediation": {"authority": "Auth"},
    }

    manifest_data = {
        "pack_id": "test.pack",
        "version": "1.0.0",
        "status": "draft",
        "parameters": {
            "cap_val": {"type": "int", "value": 250000},
            "ratio": 60.5,
            "category": "SC",
            "is_active": True,
            "slots": ["A", "B"],
        },
        "rules": [rule1, rule2],
    }
    manifest = PackManifest.model_validate(manifest_data)
    assert manifest.pack_id == "test.pack"
    assert len(manifest.rules) == 2

    # Duplicate rule id rejected
    bad_data = dict(manifest_data, rules=[rule1, dict(rule1)])
    with pytest.raises(ValidationError) as exc:
        PackManifest.model_validate(bad_data)
    assert "Duplicate rule id 'RULE-01'" in str(exc.value)


def test_source_definition_canonical_requirements():
    valid = {
        "id": "SRC-01",
        "title": "Title 1",
        "issuing_body": "Body 1",
        "status": "verified",
        "url": "https://example.gov.in",
        "retrieved_on": "2026-11-15",
    }
    src = SourceDefinition.model_validate(valid)
    assert src.id == "SRC-01"
    assert src.title == "Title 1"
    assert src.issuing_body == "Body 1"

    # Missing title rejected
    with pytest.raises(ValidationError) as exc:
        bad = dict(valid)
        del bad["title"]
        SourceDefinition.model_validate(bad)
    assert "title" in str(exc.value)

    # Blank title rejected
    with pytest.raises(ValidationError) as exc:
        bad = dict(valid, title="   ")
        SourceDefinition.model_validate(bad)
    assert "must be a non-empty string" in str(exc.value)

    # Missing issuing_body rejected
    with pytest.raises(ValidationError) as exc:
        bad = dict(valid)
        del bad["issuing_body"]
        SourceDefinition.model_validate(bad)
    assert "issuing_body" in str(exc.value)

    # Blank issuing_body rejected
    with pytest.raises(ValidationError) as exc:
        bad = dict(valid, issuing_body="   ")
        SourceDefinition.model_validate(bad)
    assert "must be a non-empty string" in str(exc.value)

    # Missing id rejected
    with pytest.raises(ValidationError) as exc:
        bad = dict(valid)
        del bad["id"]
        SourceDefinition.model_validate(bad)
    assert "id" in str(exc.value)


def test_source_definition_legacy_aliases_normalization():
    # Only legacy aliases supplied -> normalized to canonical
    legacy_data = {
        "id": "SRC-LEGACY",
        "source_title": "Legacy Guidelines Title",
        "issuing_body": "Department of Welfare",
        "official_url": "https://welfare.gov.in/rules",
        "retrieval_date": "2026-11-15",
        "status": "verified",
        "reviewed_by": "Deeptiman",
        "clause": "Rule 4",
        "supports_rule": True,
    }
    src = SourceDefinition.model_validate(legacy_data)
    assert src.id == "SRC-LEGACY"
    assert src.title == "Legacy Guidelines Title"
    assert src.url == "https://welfare.gov.in/rules"
    assert src.retrieved_on == date(2026, 11, 15)


def test_source_definition_conflicting_aliases_rejected():
    base = {
        "id": "SRC-01",
        "issuing_body": "Ministry of Social Justice",
        "status": "verified",
    }

    # Conflicting title vs source_title
    with pytest.raises(ValidationError) as exc:
        SourceDefinition.model_validate(dict(
            base,
            title="Canonical Title",
            source_title="Conflicting Legacy Title",
        ))
    assert "Conflicting aliases for title" in str(exc.value)

    # Conflicting url vs official_url
    with pytest.raises(ValidationError) as exc:
        SourceDefinition.model_validate(dict(
            base,
            title="Valid Title",
            url="https://site-a.gov.in",
            official_url="https://site-b.gov.in",
        ))
    assert "Conflicting aliases for url" in str(exc.value)

    # Conflicting retrieved_on vs retrieval_date
    with pytest.raises(ValidationError) as exc:
        SourceDefinition.model_validate(dict(
            base,
            title="Valid Title",
            retrieved_on="2026-11-15",
            retrieval_date="2026-11-16",
        ))
    assert "Conflicting aliases for retrieved_on" in str(exc.value)


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
