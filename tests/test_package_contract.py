"""
Test Package Contract and Distribution Verification (Task T0.3 / Gate G0)
Validates package metadata, console script entry points, import contracts,
and pyproject.toml extras declarations.
"""

import sys
import subprocess
import tomllib
from pathlib import Path
import docuready


_REPO_ROOT = Path(__file__).resolve().parent.parent


def test_package_metadata():
    """Verify package version and export contracts."""
    assert hasattr(docuready, "__version__"), "docuready must expose __version__"
    assert docuready.__version__ == "0.1.0", f"Expected version 0.1.0, got {docuready.__version__}"


def test_console_script_entry_point():
    """Verify console script callable entry point defined in pyproject.toml."""
    from docuready.interfaces.cli import main
    assert callable(main), "docuready.interfaces.cli:main must be callable"


def test_core_subpackages_importable():
    """Verify core architectural subpackages are importable without side-effects."""
    import docuready.domain
    import docuready.domain.models
    import docuready.ingest
    import docuready.ingest.extractor
    import docuready.evidence
    import docuready.evidence.calibrator
    import docuready.normalize
    import docuready.normalize.normalizer
    import docuready.rules
    import docuready.rules.validator
    import docuready.outcome
    import docuready.outcome.safety_layer
    import docuready.report
    import docuready.report.exporter
    import docuready.interfaces
    import docuready.interfaces.cli
    import docuready.pipeline

    assert docuready.domain.models.DocumentType is not None
    assert docuready.pipeline.AuditPipeline is not None


def test_pyproject_contract():
    """Verify pyproject.toml declarations match package and distribution specifications."""
    pyproject_path = _REPO_ROOT / "pyproject.toml"
    assert pyproject_path.is_file(), "pyproject.toml must exist at repository root"

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    project = pyproject.get("project", {})
    assert project.get("name") == "docuready"
    assert project.get("version") == "0.1.0"
    assert project.get("requires-python") == ">=3.11,<3.15"

    scripts = project.get("scripts", {})
    assert scripts.get("docuready") == "docuready.interfaces.cli:main"

    optional_deps = project.get("optional-dependencies", {})
    assert "ui" in optional_deps, "ui extra must be declared"
    assert "generator" in optional_deps, "generator extra must be declared"
    assert "dev" in optional_deps, "dev extra must be declared"
    assert "all" in optional_deps, "all extra must be declared"
    assert any(dep.lower().startswith("pyyaml") for dep in optional_deps.get("dev", [])), (
        "PyYAML must be declared directly in dev extra (Issue #38)"
    )
    assert any(dep.lower().startswith("pyyaml") for dep in optional_deps.get("all", [])), (
        "PyYAML must be declared directly in all extra (Issue #38)"
    )


def test_cli_invocation_via_module():
    """Verify CLI entry point can be invoked via python -m docuready.interfaces.cli."""
    res = subprocess.run(
        [sys.executable, "-m", "docuready.interfaces.cli", "--help"],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT)
    )
    assert res.returncode == 0, f"CLI help failed with return code {res.returncode}:\n{res.stderr}"
    assert "docuready" in res.stdout.lower() or "usage:" in res.stdout.lower()
