"""Contract tests verifying public-facing claims and anti-overreach guarantees (T1.1).

Enforces:
1. Absence of banned hyperbolic/unsubstantiated phrases across public surfaces.
2. Mandatory inclusion of the advisory disclaimer.
3. Explicit synthetic qualification of benchmark performance figures.
4. Completeness and integrity of docs/CLAIMS_REGISTER.md (CLM-001 through CLM-011).
"""

from pathlib import Path
import re
import pytest

BANNED_PHRASES = [
    "guaranteed approval",
    "universal validity",
    "100% accurate",
    "statutory guarantee",
    "official government approval",
    "government-certified",
]

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_readme_does_not_contain_banned_phrases():
    readme_path = REPO_ROOT / "README.md"
    assert readme_path.exists(), "README.md must exist at repository root"
    content = readme_path.read_text(encoding="utf-8").lower()

    for phrase in BANNED_PHRASES:
        assert phrase not in content, (
            f"Banned overreaching phrase '{phrase}' found in README.md"
        )


def test_readme_contains_advisory_disclaimer():
    readme_path = REPO_ROOT / "README.md"
    content = readme_path.read_text(encoding="utf-8")

    assert "Advisory Disclaimer" in content, "README.md must feature an Advisory Disclaimer"
    assert "not an official government portal" in content, (
        "README.md must explicitly clarify that DocuReady is not an official government portal"
    )
    assert "pre-submission" in content.lower(), (
        "README.md must clearly characterize DocuReady as a pre-submission verification tool"
    )


def test_benchmark_cites_synthetic_corpus_not_field_guarantee():
    readme_path = REPO_ROOT / "README.md"
    content = readme_path.read_text(encoding="utf-8")

    assert "Verified Benchmarks" in content, "README.md must include the Verified Benchmarks section"
    assert "synthetic" in content.lower(), "Benchmark descriptions must cite synthetic test data"
    assert "do not represent field portal acceptance guarantees" in content, (
        "Benchmarks must explicitly disclaim field portal acceptance guarantees"
    )


def test_claims_register_completeness():
    register_path = REPO_ROOT / "docs" / "CLAIMS_REGISTER.md"
    assert register_path.exists(), "docs/CLAIMS_REGISTER.md must exist"
    content = register_path.read_text(encoding="utf-8")

    # Verify CLM-001 through CLM-011 are catalogued
    for i in range(1, 12):
        claim_id = f"CLM-{i:03d}"
        assert claim_id in content, f"Missing required claim {claim_id} in docs/CLAIMS_REGISTER.md"

    # Verify all dispositions are one of Verified, Qualified, Removed
    for disposition in ["Verified", "Qualified"]:
        assert disposition in content


def test_rules_heading_and_exp_qualification_in_readme():
    readme_path = REPO_ROOT / "README.md"
    content = readme_path.read_text(encoding="utf-8")

    # Must not have bare unmodified 'Statutory Rules Engine' as section heading
    assert "## Statutory Rules Engine\n" not in content, (
        "Rules engine heading must be qualified to reflect verified citations and heuristics"
    )
    assert "Document Consistency & Scheme Requirement Rules Engine" in content, (
        "Rules engine section must accurately describe document consistency and scheme requirements"
    )

    # Must qualify income certificate validity (RULE-EXP-01)
    assert "heuristic" in content.lower(), (
        "Certificate validity rule must be qualified as an operational heuristic"
    )
