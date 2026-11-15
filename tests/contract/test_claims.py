"""Contract tests for public claims, positioning honesty, and banned phrases.

Enforces Task T1.1 requirements:
1. Public documentation must not contain unsupported statistics or absolute claims.
2. Banned phrases (e.g., "80 million", "18–32%", "30–45%", "100% DPDP compliant")
   are prohibited.
3. Static test count badges in README are prohibited; only the dynamic CI badge is permitted.
4. Benchmark tables must be explicitly labeled as synthetic.
5. The Claims Register (docs/CLAIMS_REGISTER.md) must exist and remain populated.
"""

from __future__ import annotations

import pathlib
import re
from typing import List

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


def test_claims_register_exists_and_has_required_schema():
    """Verify that docs/CLAIMS_REGISTER.md exists and contains verified claim entries."""
    register_path = _REPO_ROOT / "docs" / "CLAIMS_REGISTER.md"
    assert register_path.is_file(), "Missing docs/CLAIMS_REGISTER.md"

    content = register_path.read_text(encoding="utf-8")
    assert "# DocuReady — Claims Register" in content
    assert "CLM-001" in content
    assert "CLM-002" in content
    assert "CLM-003" in content
    assert "CLM-004" in content
    assert "CLM-005" in content
    assert "CLM-006" in content
    assert "CLM-007" in content
    assert "CLM-008" in content
    assert "CLM-009" in content
    assert "CLM-010" in content

    # Verify standard disposition states are used
    for disposition in ["verified", "softened", "removed"]:
        assert disposition in content


def test_readme_does_not_contain_banned_phrases():
    """Verify README.md contains no unsourced statistics, absolute claims, or static badges."""
    readme_path = _REPO_ROOT / "README.md"
    assert readme_path.is_file(), "Missing README.md"
    content = readme_path.read_text(encoding="utf-8")

    banned_patterns: List[str] = [
        r"80\s*million",
        r"80\s*M",
        r"18\s*[%–-]\s*32\s*%",
        r"30\s*[%–-]\s*45\s*%",
        r"100\s*%\s*DPDP\s*compliant",
        r"guaranteed\s*zero\s*exfiltration",
        r"guaranteed\s*government\s*scholarship",
        r"guaranteed\s*(?:portal\s*)?acceptance",
        r"badge/Tests-\d+",
        r"Every\s*finding\s*cites\s*an\s*enacted\s*statutory\s*clause",
    ]

    for pattern in banned_patterns:
        match = re.search(pattern, content, flags=re.IGNORECASE)
        assert match is None, (
            f"Banned phrase matching '{pattern}' found in README.md: '{match.group(0) if match else ''}'"
        )


def test_publication_report_does_not_contain_banned_phrases():
    """Verify PUBLICATION_REPORT.md has been sanitized of unsourced percentages and absolute claims."""
    report_path = _REPO_ROOT / "PUBLICATION_REPORT.md"
    if not report_path.is_file():
        return

    content = report_path.read_text(encoding="utf-8")
    banned_patterns = [
        r"18\s*[%–-]\s*32\s*%",
        r"30\s*[%–-]\s*45\s*%",
        r"100\s*%\s*local\s*compliance\s*with\s*the\s*Digital\s*Personal\s*Data\s*Protection",
    ]

    for pattern in banned_patterns:
        match = re.search(pattern, content, flags=re.IGNORECASE)
        assert match is None, (
            f"Banned phrase matching '{pattern}' found in PUBLICATION_REPORT.md: '{match.group(0) if match else ''}'"
        )


def test_research_docs_do_not_contain_unsourced_numbers():
    """Verify research documentation does not cite unsupported population counts or absolute claims."""
    research_dir = _REPO_ROOT / "docs" / "03-RESEARCH"
    if not research_dir.is_dir():
        return

    banned_patterns = [
        r"80\s*million",
        r"18\s*%\s*to\s*32\s*%",
        r"Zero\s*Data\s*Exfiltration",
    ]

    for doc in research_dir.glob("*.md"):
        content = doc.read_text(encoding="utf-8")
        for pattern in banned_patterns:
            match = re.search(pattern, content, flags=re.IGNORECASE)
            assert match is None, (
                f"Banned pattern '{pattern}' found in {doc.name}: '{match.group(0) if match else ''}'"
            )


def test_readme_benchmarks_labeled_synthetic():
    """Verify all benchmark references in README explicitly disclose synthetic dataset origin."""
    readme_path = _REPO_ROOT / "README.md"
    content = readme_path.read_text(encoding="utf-8")

    assert "Synthetic Benchmark Evaluation" in content or "Synthetic Benchmark Dataset" in content
    assert "Synthetic Dataset Notice" in content
    assert "do not represent field portal acceptance guarantees" in content.lower()


def test_readme_preserves_presubmission_advisory_disclaimer():
    """Verify README retains the prominent pre-submission advisory disclaimer."""
    readme_path = _REPO_ROOT / "README.md"
    content = readme_path.read_text(encoding="utf-8")

    assert "Pre-Submission Advisory Only" in content
    assert "does not guarantee scheme approval" in content.lower() or "not an official government portal" in content.lower()
