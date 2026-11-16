"""Tests for CLI 'docuready packs lint' entry point (Task T3.1)."""

import os
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


def test_cli_packs_lint_explicit_packs_root_out_of_repo(tmp_path):
    # Simulate executing from an external directory (like /tmp)
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    packs_dir = repo_root / "packs"

    test_args = ["docuready", "packs", "lint", str(packs_dir), "--allow-draft"]
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == int(ExitCode.NO_ISSUES)
    finally:
        os.chdir(original_cwd)


def test_cli_packs_lint_root_with_invalid_pack_fails(tmp_path):
    packs_root = tmp_path / "packs"
    packs_root.mkdir()

    # Valid pack
    p1 = packs_root / "p1"
    p1.mkdir()
    (p1 / "pack.yaml").write_text("pack_id: p1\nversion: '1.0'\nstatus: draft\nrules: []\n", encoding="utf-8")
    (p1 / "sources.yaml").write_text("pack_id: p1\nversion: '1.0'\n", encoding="utf-8")

    # Malformed pack missing pack.yaml
    p2 = packs_root / "p2_broken"
    p2.mkdir()
    (p2 / "sources.yaml").write_text("pack_id: p2\nversion: '1.0'\n", encoding="utf-8")

    test_args = ["docuready", "packs", "lint", str(packs_root), "--allow-draft"]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == int(ExitCode.NEEDS_CHECKS)  # exit code 1 due to broken pack


def test_cli_packs_lint_empty_packs_root_exits_usage_error(tmp_path):
    empty_root = tmp_path / "empty_packs"
    empty_root.mkdir()

    test_args = ["docuready", "packs", "lint", str(empty_root), "--allow-draft"]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == int(ExitCode.USAGE_ERROR)  # exit code 64
