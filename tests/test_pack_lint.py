"""Unit and integration tests for Scheme Pack linter (Task T3.1).

Tests every lint rule with dedicated valid and failing fixtures, typed parameter
contracts, multi-pack discovery, and error reporting.
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
  cert_validity_days: 365
  name_match_grade: "name"
  allowed_categories: ["SC", "ST"]
  min_legible_conf: 0.75
  ref_date: 2026-04-01
  min_student_age: 18
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
    assert any("remediation authority" in str(e).lower() for e in result.errors)


def test_lint_unresolved_citation_source_rejected(base_pack):
    pack_yaml = (base_pack / "pack.yaml").read_text(encoding="utf-8").replace("source: SRC-01", "source: SRC-NONEXISTENT")
    (base_pack / "pack.yaml").write_text(pack_yaml, encoding="utf-8")

    result = lint_pack(base_pack)
    assert not result.is_valid
    assert any("does not resolve in sources.yaml" in str(e) for e in result.errors)


def test_lint_unverified_source_emits_warning(base_pack):
    sources_yaml = (base_pack / "sources.yaml").read_text(encoding="utf-8").replace(
        "status: verified",
        "status: unverified\n    notes: 'Operational heuristic'",
    )
    (base_pack / "sources.yaml").write_text(sources_yaml, encoding="utf-8")

    result = lint_pack(base_pack)
    assert result.is_valid  # Warnings do not invalidate pack
    assert len(result.warnings) > 0
    assert any("source pending verification" in str(w) for w in result.warnings)


def test_lint_unresolved_param_references_across_locations(base_pack):
    # 1. Unresolved param in rule.params
    p1 = (base_pack / "pack.yaml").read_text(encoding="utf-8").replace("$income_cap_inr", "$missing_param")
    (base_pack / "pack.yaml").write_text(p1, encoding="utf-8")
    res1 = lint_pack(base_pack)
    assert not res1.is_valid
    assert any("references undefined parameter '$missing_param' in 'cap'" in str(e) for e in res1.errors)

    # 2. Unresolved param in rule.inputs
    p2 = (base_pack / "pack.yaml").read_text(encoding="utf-8").replace("cap: $missing_param", "cap: 250000").replace("docs: [INCOME_CERT]", "docs: [$missing_slot]")
    (base_pack / "pack.yaml").write_text(p2, encoding="utf-8")
    res2 = lint_pack(base_pack)
    assert not res2.is_valid
    assert any("references undefined parameter '$missing_slot' in 'inputs'" in str(e) for e in res2.errors)

    # 3. Unresolved param in rule.exempt_when
    p3 = (base_pack / "pack.yaml").read_text(encoding="utf-8").replace("docs: [$missing_slot]", "docs: [INCOME_CERT]") + "\n    exempt_when: { fact: applicant.category, in: $missing_categories }\n"
    (base_pack / "pack.yaml").write_text(p3, encoding="utf-8")
    res3 = lint_pack(base_pack)
    assert not res3.is_valid
    assert any("references undefined parameter '$missing_categories' in 'exempt_when'" in str(e) for e in res3.errors)


def test_lint_param_type_contracts_across_primitives(tmp_path):
    # Construct rules testing type compatibility across primitives
    pack_dir = tmp_path / "typed_pack"
    pack_dir.mkdir()

    sources_yaml = """
pack_id: test.typed
version: "1.0.0"
reviewed_by: "Auditor"
sources:
  - id: S1
    title: "Title"
    issuing_body: "Body"
    url: "https://example.gov.in"
    retrieved_on: "2026-11-15"
    status: verified
"""
    (pack_dir / "sources.yaml").write_text(sources_yaml, encoding="utf-8")

    # Incompatible numeric_cap: string provided for cap
    bad_cap_yaml = """
pack_id: test.typed
version: "1.0.0"
status: verified
parameters:
  bad_cap: "two_lakhs"
rules:
  - id: R1
    primitive: numeric_cap
    params: { cap: $bad_cap }
    max_severity: FAIL
    citation: { source: S1 }
    remediation: { authority: "Auth" }
"""
    (pack_dir / "pack.yaml").write_text(bad_cap_yaml, encoding="utf-8")
    res_cap = lint_pack(pack_dir)
    assert not res_cap.is_valid
    assert any("must be number, got string" in str(e) for e in res_cap.errors)

    # Incompatible within_validity: string provided for validity_days
    bad_val_yaml = """
pack_id: test.typed
version: "1.0.0"
status: verified
parameters:
  bad_days: "365_days"
rules:
  - id: R2
    primitive: within_validity
    params: { validity_days: $bad_days }
    max_severity: FAIL
    citation: { source: S1 }
    remediation: { authority: "Auth" }
"""
    (pack_dir / "pack.yaml").write_text(bad_val_yaml, encoding="utf-8")
    res_val = lint_pack(pack_dir)
    assert not res_val.is_valid
    assert any("must be int, got string" in str(e) for e in res_val.errors)

    # Incompatible match_across: invalid grade string
    bad_grade_yaml = """
pack_id: test.typed
version: "1.0.0"
status: verified
parameters:
  bad_grade: "fuzzy_phonetic"
rules:
  - id: R3
    primitive: match_across
    params: { grade: $bad_grade }
    max_severity: FAIL
    citation: { source: S1 }
    remediation: { authority: "Auth" }
"""
    (pack_dir / "pack.yaml").write_text(bad_grade_yaml, encoding="utf-8")
    res_grade = lint_pack(pack_dir)
    assert not res_grade.is_valid
    assert any("Invalid match grade 'fuzzy_phonetic'" in str(e) for e in res_grade.errors)

    # Incompatible enum_in: non-list provided for allowed
    bad_enum_yaml = """
pack_id: test.typed
version: "1.0.0"
status: verified
parameters:
  bad_list: 12345
rules:
  - id: R4
    primitive: enum_in
    params: { allowed: $bad_list }
    max_severity: FAIL
    citation: { source: S1 }
    remediation: { authority: "Auth" }
"""
    (pack_dir / "pack.yaml").write_text(bad_enum_yaml, encoding="utf-8")
    res_enum = lint_pack(pack_dir)
    assert not res_enum.is_valid
    assert any("must be list, got int" in str(e) for e in res_enum.errors)

    # Incompatible exempt_when: non-list provided for 'in' condition
    bad_exempt_yaml = """
pack_id: test.typed
version: "1.0.0"
status: verified
parameters:
  not_a_list: "SINGLE_CATEGORY"
rules:
  - id: R5
    primitive: field_present
    inputs: { field: "name" }
    exempt_when: { fact: "cat", in: $not_a_list }
    max_severity: FAIL
    citation: { source: S1 }
    remediation: { authority: "Auth" }
"""
    (pack_dir / "pack.yaml").write_text(bad_exempt_yaml, encoding="utf-8")
    res_exempt = lint_pack(pack_dir)
    assert not res_exempt.is_valid
    assert any("for exempt_when 'in' condition must be list, got string" in str(e) for e in res_exempt.errors)


def test_lint_unsupported_primitive_parameter_rejected(tmp_path):
    pack_dir = tmp_path / "unsupported_param_pack"
    pack_dir.mkdir()

    sources_yaml = """
pack_id: test.unsupported
version: "1.0.0"
reviewed_by: "Auditor"
sources:
  - id: S1
    title: "T"
    issuing_body: "B"
    url: "https://example.gov.in"
    retrieved_on: "2026-11-15"
    status: verified
"""
    pack_yaml = """
pack_id: test.unsupported
version: "1.0.0"
status: verified
rules:
  - id: R1
    primitive: require_document
    params: { completely_unknown_param: 123 }
    max_severity: FAIL
    citation: { source: S1 }
    remediation: { authority: "Auth" }
"""
    (pack_dir / "pack.yaml").write_text(pack_yaml, encoding="utf-8")
    (pack_dir / "sources.yaml").write_text(sources_yaml, encoding="utf-8")

    result = lint_pack(pack_dir)
    assert not result.is_valid
    assert any("unsupported parameter 'completely_unknown_param' for primitive 'require_document'" in str(e) for e in result.errors)


def test_lint_missing_mandatory_primitive_parameters(tmp_path):
    pack_dir = tmp_path / "missing_param_pack"
    pack_dir.mkdir()

    sources_yaml = """
pack_id: test.missing
version: "1.0.0"
reviewed_by: "Auditor"
sources:
  - id: S1
    title: "T"
    issuing_body: "B"
    url: "https://example.gov.in"
    retrieved_on: "2026-11-15"
    status: verified
"""
    # numeric_cap without cap parameter
    pack_yaml = """
pack_id: test.missing
version: "1.0.0"
status: verified
rules:
  - id: R1
    primitive: numeric_cap
    params: {}
    max_severity: FAIL
    citation: { source: S1 }
    remediation: { authority: "Auth" }
"""
    (pack_dir / "pack.yaml").write_text(pack_yaml, encoding="utf-8")
    (pack_dir / "sources.yaml").write_text(sources_yaml, encoding="utf-8")

    result = lint_pack(pack_dir)
    assert not result.is_valid
    assert any("missing required parameter 'cap'" in str(e) for e in result.errors)


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


def test_lint_all_packs_discovery_and_malformed_directories(tmp_path):
    root = tmp_path / "packs_root"
    root.mkdir()

    # 1. Valid pack
    valid_dir = root / "pack_valid"
    valid_dir.mkdir()
    (valid_dir / "pack.yaml").write_text("pack_id: p_valid\nversion: '1.0'\nstatus: draft\nrules: []\n", encoding="utf-8")
    (valid_dir / "sources.yaml").write_text("pack_id: p_valid\nversion: '1.0'\n", encoding="utf-8")

    # 2. Malformed pack: missing sources.yaml (only pack.yaml)
    missing_sources_dir = root / "pack_only_pack_yaml"
    missing_sources_dir.mkdir()
    (missing_sources_dir / "pack.yaml").write_text("pack_id: p_no_sources\nversion: '1.0'\nstatus: draft\nrules: []\n", encoding="utf-8")

    # 3. Malformed pack: missing pack.yaml (only sources.yaml)
    missing_pack_dir = root / "pack_only_sources_yaml"
    missing_pack_dir.mkdir()
    (missing_pack_dir / "sources.yaml").write_text("pack_id: p_no_pack\nversion: '1.0'\n", encoding="utf-8")

    # 4. Malformed pack: completely empty child directory
    empty_child_dir = root / "pack_empty_dir"
    empty_child_dir.mkdir()

    results = lint_all_packs(root, allow_draft=True)
    # Must report on ALL 4 child directories, not silently omit them!
    assert len(results) == 4

    results_by_name = {r.pack_dir.name: r for r in results}
    assert results_by_name["pack_valid"].is_valid is True
    assert results_by_name["pack_only_pack_yaml"].is_valid is False
    assert any("Missing required sources registry" in str(e) for e in results_by_name["pack_only_pack_yaml"].errors)

    assert results_by_name["pack_only_sources_yaml"].is_valid is False
    assert any("Missing required pack manifest" in str(e) for e in results_by_name["pack_only_sources_yaml"].errors)

    assert results_by_name["pack_empty_dir"].is_valid is False
    assert any("Missing required pack manifest" in str(e) for e in results_by_name["pack_empty_dir"].errors)


def test_lint_all_packs_empty_and_missing_root(tmp_path):
    # Empty packs root (directory with no subdirectories)
    empty_root = tmp_path / "empty_root"
    empty_root.mkdir()
    assert lint_all_packs(empty_root) == []

    # Non-existent packs root
    non_existent = tmp_path / "does_not_exist"
    assert lint_all_packs(non_existent) == []


def test_lint_match_across_missing_grade_rejected(tmp_path):
    pack_dir = tmp_path / "match_across_no_grade"
    pack_dir.mkdir()

    sources_yaml = """
pack_id: test.match
version: "1.0.0"
reviewed_by: "Auditor"
sources:
  - id: S1
    title: "T"
    issuing_body: "B"
    url: "https://example.gov.in"
    retrieved_on: "2026-11-15"
    status: verified
"""
    # match_across without grade
    pack_yaml = """
pack_id: test.match
version: "1.0.0"
status: verified
rules:
  - id: R1
    primitive: match_across
    inputs: { fields: ["name", "applicant_name"] }
    params: { threshold: 0.85 }
    max_severity: FAIL
    citation: { source: S1 }
    remediation: { authority: "Auth" }
"""
    (pack_dir / "pack.yaml").write_text(pack_yaml, encoding="utf-8")
    (pack_dir / "sources.yaml").write_text(sources_yaml, encoding="utf-8")

    result = lint_pack(pack_dir)
    assert not result.is_valid
    assert any("missing required parameter 'grade'" in str(e) for e in result.errors)


def test_lint_input_contracts_and_param_type_compatibility(tmp_path):
    pack_dir = tmp_path / "input_contracts_pack"
    pack_dir.mkdir()

    sources_yaml = """
pack_id: test.inputs
version: "1.0.0"
reviewed_by: "Auditor"
sources:
  - id: S1
    title: "T"
    issuing_body: "B"
    url: "https://example.gov.in"
    retrieved_on: "2026-11-15"
    status: verified
"""
    (pack_dir / "sources.yaml").write_text(sources_yaml, encoding="utf-8")

    # 1. Unsupported input field without param
    p1 = """
pack_id: test.inputs
version: "1.0.0"
status: verified
rules:
  - id: R1
    primitive: numeric_cap
    inputs: { unsupported_field: "val" }
    params: { cap: 250000 }
    max_severity: FAIL
    citation: { source: S1 }
    remediation: { authority: "Auth" }
"""
    (pack_dir / "pack.yaml").write_text(p1, encoding="utf-8")
    r1 = lint_pack(pack_dir)
    assert not r1.is_valid
    assert any("unsupported input field 'unsupported_field'" in str(e) for e in r1.errors)

    # 2. Parameter reference in uncontracted input field
    p2 = """
pack_id: test.inputs
version: "1.0.0"
status: verified
parameters:
  my_param: "field_name"
rules:
  - id: R1
    primitive: numeric_cap
    inputs: { arbitrary_field: $my_param }
    params: { cap: 250000 }
    max_severity: FAIL
    citation: { source: S1 }
    remediation: { authority: "Auth" }
"""
    (pack_dir / "pack.yaml").write_text(p2, encoding="utf-8")
    r2 = lint_pack(pack_dir)
    assert not r2.is_valid
    assert any("uncontracted input field 'arbitrary_field'" in str(e) for e in r2.errors)

    # 3. Type mismatch: string expected for 'field', got integer param
    p3 = """
pack_id: test.inputs
version: "1.0.0"
status: verified
parameters:
  int_param: 12345
rules:
  - id: R1
    primitive: numeric_cap
    inputs: { field: $int_param }
    params: { cap: 250000 }
    max_severity: FAIL
    citation: { source: S1 }
    remediation: { authority: "Auth" }
"""
    (pack_dir / "pack.yaml").write_text(p3, encoding="utf-8")
    r3 = lint_pack(pack_dir)
    assert not r3.is_valid
    assert any("numeric_cap.inputs.field must be string, got int" in str(e) for e in r3.errors)

    # 4. Type mismatch: string expected inside docs list, got integer param
    p4 = """
pack_id: test.inputs
version: "1.0.0"
status: verified
parameters:
  bad_slot_param: 999
rules:
  - id: R1
    primitive: numeric_cap
    inputs: { field: "income.annual", docs: [$bad_slot_param] }
    params: { cap: 250000 }
    max_severity: FAIL
    citation: { source: S1 }
    remediation: { authority: "Auth" }
"""
    (pack_dir / "pack.yaml").write_text(p4, encoding="utf-8")
    r4 = lint_pack(pack_dir)
    assert not r4.is_valid
    assert any("numeric_cap.inputs.docs list must be string, got int" in str(e) for e in r4.errors)

    # 5. Valid typed input parameter reference passes
    p5 = """
pack_id: test.inputs
version: "1.0.0"
status: verified
parameters:
  valid_field_name: "income.annual"
  valid_slot_name: "income_certificate"
rules:
  - id: R1
    primitive: numeric_cap
    inputs: { field: $valid_field_name, docs: [$valid_slot_name] }
    params: { cap: 250000 }
    max_severity: FAIL
    citation: { source: S1 }
    remediation: { authority: "Auth" }
"""
    (pack_dir / "pack.yaml").write_text(p5, encoding="utf-8")
    r5 = lint_pack(pack_dir)
    assert r5.is_valid


def test_lint_absent_parameter_value_rejected_when_referenced(tmp_path):
    pack_dir = tmp_path / "absent_param_value_pack"
    pack_dir.mkdir()

    sources_yaml = """
pack_id: test.absent
version: "1.0.0"
reviewed_by: "Auditor"
sources:
  - id: S1
    title: "T"
    issuing_body: "B"
    url: "https://example.gov.in"
    retrieved_on: "2026-11-15"
    status: verified
"""
    (pack_dir / "sources.yaml").write_text(sources_yaml, encoding="utf-8")

    # 1. Parameter with omitted value in rule.params
    p1 = """
pack_id: test.absent
version: "1.0.0"
status: verified
parameters:
  unconfigured_cap:
    type: number
rules:
  - id: R1
    primitive: numeric_cap
    params: { cap: $unconfigured_cap }
    max_severity: FAIL
    citation: { source: S1 }
    remediation: { authority: "Auth" }
"""
    (pack_dir / "pack.yaml").write_text(p1, encoding="utf-8")
    r1 = lint_pack(pack_dir)
    assert not r1.is_valid
    assert any("has no configured value; absent parameter values cannot be treated as executable configuration" in str(e) for e in r1.errors)

    # 2. Parameter with omitted value in rule.inputs
    p2 = """
pack_id: test.absent
version: "1.0.0"
status: verified
parameters:
  unconfigured_field:
    type: string
rules:
  - id: R1
    primitive: numeric_cap
    inputs: { field: $unconfigured_field }
    params: { cap: 250000 }
    max_severity: FAIL
    citation: { source: S1 }
    remediation: { authority: "Auth" }
"""
    (pack_dir / "pack.yaml").write_text(p2, encoding="utf-8")
    r2 = lint_pack(pack_dir)
    assert not r2.is_valid
    assert any("has no configured value; absent parameter values cannot be treated as executable configuration" in str(e) for e in r2.errors)

    # 3. Unreferenced parameter with omitted value passes linting
    p3 = """
pack_id: test.absent
version: "1.0.0"
status: verified
parameters:
  abstract_schema_param:
    type: number
rules:
  - id: R1
    primitive: numeric_cap
    params: { cap: 250000 }
    max_severity: FAIL
    citation: { source: S1 }
    remediation: { authority: "Auth" }
"""
    (pack_dir / "pack.yaml").write_text(p3, encoding="utf-8")
    r3 = lint_pack(pack_dir)
    assert r3.is_valid
