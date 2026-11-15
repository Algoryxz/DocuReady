"""Contract tests for citation audit, sources.yaml schema, and verification integrity (Task T1.5)."""

from __future__ import annotations

import pathlib
import pytest
import yaml

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_sources_yaml_parses_with_strict_schema():
    """Verify that packs/generic.demo/sources.yaml parses with PyYAML and satisfies strict schema."""
    sources_path = _REPO_ROOT / "packs" / "generic.demo" / "sources.yaml"
    assert sources_path.is_file(), f"Missing {sources_path}"

    data = yaml.safe_load(sources_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "sources.yaml must contain a top-level dictionary"
    assert data.get("pack_id") == "generic.demo"
    assert "version" in data
    assert "rules" in data
    assert isinstance(data["rules"], list)
    assert len(data["rules"]) >= 10, "Expected at least 10 rules in generic.demo pack"

    allowed_statuses = {"verified", "placeholder", "unverified"}
    rule_ids_seen = set()

    for idx, rule in enumerate(data["rules"]):
        assert isinstance(rule, dict), f"Rule at index {idx} must be a dictionary"
        rule_id = rule.get("id")
        assert rule_id, f"Rule at index {idx} missing 'id'"
        assert rule_id not in rule_ids_seen, f"Duplicate rule id '{rule_id}' in sources.yaml"
        rule_ids_seen.add(rule_id)

        assert "name" in rule and rule["name"], f"Rule {rule_id} missing 'name'"
        status = rule.get("status")
        assert status in allowed_statuses, (
            f"Rule {rule_id} has invalid status '{status}'; allowed: {allowed_statuses}"
        )

        # Strict validation for 'verified' entries
        if status == "verified":
            assert rule.get("source_title"), f"Verified rule {rule_id} missing 'source_title'"
            assert rule.get("issuing_body"), f"Verified rule {rule_id} missing 'issuing_body'"
            assert rule.get("clause"), f"Verified rule {rule_id} missing 'clause'"
            assert rule.get("retrieval_date"), f"Verified rule {rule_id} missing 'retrieval_date'"
            assert rule.get("supports_rule") is True, (
                f"Verified rule {rule_id} must have supports_rule: true"
            )
            url = rule.get("official_url", "")
            assert url.startswith("http://") or url.startswith("https://"), (
                f"Verified rule {rule_id} must have a valid official http(s) URL"
            )

        # Strict validation for 'unverified' entries
        if status == "unverified":
            assert rule.get("notes"), f"Unverified rule {rule_id} must have explanatory notes"


def test_validator_rules_mapped_to_source_registry():
    """Verify that all core checks in validator.py are mapped in sources.yaml."""
    sources_path = _REPO_ROOT / "packs" / "generic.demo" / "sources.yaml"
    data = yaml.safe_load(sources_path.read_text(encoding="utf-8"))
    registered_ids = {r["id"] for r in data["rules"]}

    # The 10 core rule check categories implemented in validator.py
    core_validator_categories = [
        "RULE-DOC-01",  # Document completeness
        "RULE-FLD-01",  # Field completeness
        "RULE-NAME-01", # Applicant name consistency
        "RULE-DOB-01",  # Date of birth consistency
        "RULE-INC-01",  # Income ceiling compliance
        "RULE-INC-02",  # Income declaration match
        "RULE-EXP-01",  # Certificate validity period
        "RULE-REF-01",  # Certificate reference number match
        "RULE-BNK-01",  # Bank account & IFSC format
        "RULE-MRK-01",  # Academic cutoff compliance
    ]

    for cat_id in core_validator_categories:
        assert cat_id in registered_ids, (
            f"Core validator check '{cat_id}' is not mapped in packs/generic.demo/sources.yaml"
        )


def test_citation_audit_doc_corrects_known_historical_errors():
    """Verify that docs/CITATION_AUDIT.md documents specific corrected historical citations."""
    audit_path = _REPO_ROOT / "docs" / "CITATION_AUDIT.md"
    assert audit_path.is_file(), f"Missing {audit_path}"
    content = audit_path.read_text(encoding="utf-8")

    # Verify Odisha 2019 Rule 8 correction is documented
    assert "Cancellation of miscellaneous certificate" in content
    assert "Rule 8" in content

    # Verify CBSE Rule 69.2 correction is documented
    assert "Rule 69.2" in content
    assert "Change/Correction in Date of Birth" in content

    # Verify e-District SDA correction is documented
    assert "State Designated Agencies" in content or "e-District" in content


def test_no_fictitious_statutory_claims_in_unverified_rules():
    """Verify that unverified rules in sources.yaml do not claim to support primary statutory mandates."""
    sources_path = _REPO_ROOT / "packs" / "generic.demo" / "sources.yaml"
    data = yaml.safe_load(sources_path.read_text(encoding="utf-8"))

    for rule in data["rules"]:
        if rule.get("status") == "unverified":
            assert rule.get("supports_rule") is False, (
                f"Rule {rule['id']} is unverified but asserts supports_rule: true"
            )
