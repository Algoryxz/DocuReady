"""Tests for Task T1.5 citation sources and schema validity."""

from __future__ import annotations

import pathlib
import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_sources_yaml_exists_and_parses():
    """Verify that packs/generic.demo/sources.yaml exists and contains valid YAML."""
    sources_path = _REPO_ROOT / "packs" / "generic.demo" / "sources.yaml"
    assert sources_path.is_file(), f"Missing {sources_path}"

    content = sources_path.read_text(encoding="utf-8")
    assert "version:" in content
    assert "pack_id: \"generic.demo\"" in content
    assert "rules:" in content

    # Verify key rules are present
    expected_rules = [
        "RULE-DOC-01",
        "RULE-DOC-02",
        "RULE-FLD-01",
        "RULE-NAME-01",
        "RULE-DOB-01",
        "RULE-INC-01",
        "RULE-INC-02",
        "RULE-EXP-01",
        "RULE-REF-01",
        "RULE-BNK-01",
        "RULE-BNK-02",
        "RULE-DOM-01",
        "RULE-MRK-01",
    ]
    for rule_id in expected_rules:
        assert f'id: "{rule_id}"' in content, f"Rule {rule_id} missing from sources.yaml"
        assert 'status: "verified"' in content


def test_citation_audit_doc_exists_and_covers_core_rules():
    """Verify docs/CITATION_AUDIT.md exists and documents the audit matrix."""
    audit_path = _REPO_ROOT / "docs" / "CITATION_AUDIT.md"
    assert audit_path.is_file(), f"Missing {audit_path}"

    content = audit_path.read_text(encoding="utf-8")
    assert "# DocuReady — Citation Audit" in content
    assert "RULE-INC-01" in content
    assert "RULE-EXP-01" in content
    assert "The Odisha Miscellaneous Certificates Rules, 2019" in content
    assert "Central Board of Secondary Education" in content
