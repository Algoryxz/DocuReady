"""Tests for CLI 'docuready packs lint' entry point (Task T3.1)."""

import pathlib
import sys
from unittest.mock import patch
import pytest

from docuready.domain.enums import ExitCode
from docuready.interfaces.cli import main


def test_cli_packs_lint_generic_demo_with_allow_draft():
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    demo_pack = repo_root / "packs" / "generic.demo"

    test_args = ["docuready", "packs", "lint", str(demo_pack), "--allow-draft"]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == int(ExitCode.NO_ISSUES)


def test_cli_packs_lint_generic_demo_rejects_draft():
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    demo_pack = repo_root / "packs" / "generic.demo"

    test_args = ["docuready", "packs", "lint", str(demo_pack)]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == int(ExitCode.NEEDS_CHECKS)  # exit code 1


def test_cli_packs_lint_nonexistent_path():
    test_args = ["docuready", "packs", "lint", "nonexistent/directory/path"]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == int(ExitCode.USAGE_ERROR)  # exit code 64


def test_cli_packs_no_subcommand_exits_usage_error():
    test_args = ["docuready", "packs"]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == int(ExitCode.USAGE_ERROR)  # exit code 64


def test_cli_packs_lint_does_not_instantiate_pipeline():
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    demo_pack = repo_root / "packs" / "generic.demo"

    test_args = ["docuready", "packs", "lint", str(demo_pack), "--allow-draft"]
    with patch("docuready.pipeline.AuditPipeline") as mock_pipeline:
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == int(ExitCode.NO_ISSUES)
            mock_pipeline.assert_not_called()
