"""Unit and integration tests for Scheme Pack linter (Task T3.1).

Tests every lint rule with dedicated valid and failing fixtures.
"""

from pathlib import Path
import pytest

from docuready.rules.lint import lint_all_packs, lint_pack


@pytest.fixture
def base_pack(tmp_path):
    """Creates a minimal valid pack fixture in tmp_path."""
    pack_dir = tmp_path / "valid_pack"
    pack_dir.mkdir()

    pack_yaml = """
pack_id: test.valid
version: "1.0.0"
status: verified
effective:
  from: 2026-04-01
  to: 2027-03-31
parameters:
  income_cap_inr: 250000
doc_slots:
  INCOME_CERT:
    ocr_langs: [eng]
    required: true
rules:
  - id: RULE-INC-01
    primitive: numeric_cap
    inputs: { field: income.annual, docs: [INCOME_CERT] }
    params: { cap: $income_cap_inr }
    max_severity: FAIL
    citation: { source: SRC-01, clause: "Clause 3.1" }
    remediation:
      authority: "Revenue Officer"
      replacement_document: "INCOME_CERT"
      steps: ["Apply for revised income certificate"]
"""
    sources_yaml = """
pack_id: test.valid
version: "1.0.0"
reviewed_by: "Lead Auditor"
sources:
  - id: SRC-01
    title: "Post-Matric Scholarship Guidelines"
    issuing_body: "Ministry of Social Justice and Empowerment"
    url: "https://socialjustice.gov.in/schemes/31"
    retrieved_on: "2026-11-15"
    status: verified
    reviewed_by: "Lead Auditor"
    clause: "Clause 3.1"
    supports_rule: true
"""
    (pack_dir / "pack.yaml").write_text(pack_yaml, encoding="utf-8")
    (pack_dir / "sources.yaml").write_text(sources_yaml, encoding="utf-8")
    return pack_dir


def test_lint_clean_pack_passes(base_pack):
    result = lint_pack(base_pack)
    assert result.is_valid, f"Expected clean pack to pass, got errors: {result.errors}"
    assert len(result.errors) == 0
    assert len(result.warnings) == 0


def test_lint_draft_pack_rejected_without_allow_draft(base_pack):
    # Change status to draft
    pack_yaml = (base_pack / "pack.yaml").read_text(encoding="utf-8").replace("status: verified", "status: draft")
    (base_pack / "pack.yaml").write_text(pack_yaml, encoding="utf-8")

    result = lint_pack(base_pack, allow_draft=False)
    assert not result.is_valid
    assert any("Draft packs are rejected" in str(e) for e in result.errors)

    # With allow_draft=True, it passes
    result_allowed = lint_pack(base_pack, allow_draft=True)
    assert result_allowed.is_valid


def test_lint_unknown_primitive_rejected(base_pack):
    pack_yaml = (base_pack / "pack.yaml").read_text(encoding="utf-8").replace("primitive: numeric_cap", "primitive: execute_custom_python")
    (base_pack / "pack.yaml").write_text(pack_yaml, encoding="utf-8")

    result = lint_pack(base_pack)
    assert not result.is_valid
    assert any("Unknown primitive 'execute_custom_python'" in str(e) for e in result.errors)


def test_lint_missing_remediation_authority_rejected(base_pack):
    pack_yaml = (base_pack / "pack.yaml").read_text(encoding="utf-8").replace('authority: "Revenue Officer"', 'authority: "   "')
    (base_pack / "pack.yaml").write_text(pack_yaml, encoding="utf-8")

    result = lint_pack(base_pack)
    assert not result.is_valid
    assert any("missing required remediation authority" in str(e) for e in result.errors)


def test_lint_unresolved_citation_source_rejected(base_pack):
    pack_yaml = (base_pack / "pack.yaml").read_text(encoding="utf-8").replace("source: SRC-01", "source: SRC-NONEXISTENT")
    (base_pack / "pack.yaml").write_text(pack_yaml, encoding="utf-8")

    result = lint_pack(base_pack)
    assert not result.is_valid
    assert any("does not resolve in sources.yaml" in str(e) for e in result.errors)


def test_lint_unverified_source_emits_warning(base_pack):
    sources_yaml = (base_pack / "sources.yaml").read_text(encoding="utf-8").replace("status: verified", "status: unverified\n    notes: 'Operational heuristic'")
    (base_pack / "sources.yaml").write_text(sources_yaml, encoding="utf-8")

    result = lint_pack(base_pack)
    assert result.is_valid  # Warnings do not invalidate pack
    assert len(result.warnings) > 0
    assert any("source pending verification" in str(w) for w in result.warnings)


def test_lint_unresolved_param_reference_rejected(base_pack):
    pack_yaml = (base_pack / "pack.yaml").read_text(encoding="utf-8").replace("$income_cap_inr", "$undefined_param")
    (base_pack / "pack.yaml").write_text(pack_yaml, encoding="utf-8")

    result = lint_pack(base_pack)
    assert not result.is_valid
    assert any("References undefined parameter '$undefined_param'" in str(e) for e in result.errors)


def test_lint_param_type_incompatibility_rejected(base_pack):
    # Set numeric_cap parameter to a string value
    pack_yaml = (base_pack / "pack.yaml").read_text(encoding="utf-8").replace("income_cap_inr: 250000", "income_cap_inr: 'two_lakh_fifty_thousand'")
    (base_pack / "pack.yaml").write_text(pack_yaml, encoding="utf-8")

    result = lint_pack(base_pack)
    assert not result.is_valid
    assert any("must be numeric" in str(e) for e in result.errors)


def test_lint_verified_source_missing_url_or_date_rejected(base_pack):
    sources_yaml = """
pack_id: test.valid
version: "1.0.0"
sources:
  - id: SRC-01
    title: "Post-Matric Scholarship Guidelines"
    issuing_body: "Ministry of Social Justice and Empowerment"
    status: verified
"""
    (base_pack / "sources.yaml").write_text(sources_yaml, encoding="utf-8")

    result = lint_pack(base_pack)
    assert not result.is_valid
    assert any("Verified source missing required metadata" in str(e) for e in result.errors)


def test_lint_unverified_source_missing_notes_rejected(base_pack):
    sources_yaml = """
pack_id: test.valid
version: "1.0.0"
sources:
  - id: SRC-01
    title: "Guidelines"
    issuing_body: "NSP"
    status: unverified
"""
    (base_pack / "sources.yaml").write_text(sources_yaml, encoding="utf-8")

    result = lint_pack(base_pack)
    assert not result.is_valid
    assert any("Unverified source must provide explanatory notes" in str(e) for e in result.errors)


def test_lint_duplicate_key_in_yaml_rejected(base_pack):
    dup_pack = (base_pack / "pack.yaml").read_text(encoding="utf-8") + "\nstatus: verified\n"
    (base_pack / "pack.yaml").write_text(dup_pack, encoding="utf-8")

    result = lint_pack(base_pack)
    assert not result.is_valid
    assert any("Duplicate mapping key" in str(e) for e in result.errors)


def test_lint_all_packs_discovery(tmp_path):
    # Create two packs in a parent directory
    p1 = tmp_path / "pack1"
    p2 = tmp_path / "pack2"
    p1.mkdir()
    p2.mkdir()

    for p, pid in [(p1, "p1"), (p2, "p2")]:
        (p / "pack.yaml").write_text(f"pack_id: {pid}\nversion: '1.0'\nstatus: draft\n", encoding="utf-8")
        (p / "sources.yaml").write_text(f"pack_id: {pid}\nversion: '1.0'\n", encoding="utf-8")

    results = lint_all_packs(tmp_path, allow_draft=True)
    assert len(results) == 2
    assert {r.pack_id for r in results} == {"p1", "p2"}
