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


def test_cli_audit_without_ocr_pack_preserves_legacy_english(tmp_path):
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    pkt_dir = repo_root / "synthetic_data" / "pkt_01_clean"

    test_args = ["docuready", "audit", str(pkt_dir), "--json"]
    with patch("docuready.pipeline.AuditPipeline") as mock_pipeline_cls:
        from docuready.domain.enums import Readiness
        from docuready.domain.models import AuditResult

        mock_inst = mock_pipeline_cls.return_value
        mock_inst.load_and_audit_packet.return_value = (
            AuditResult(
                packet_id="PKT_01_CLEAN",
                scheme_name="generic.demo",
                readiness_score=100,
                overall_status=Readiness.NO_ISSUES_FOUND,
                findings=[],
                summary_counts={},
                execution_time_ms=1.0,
                timestamp="2026-11-27T00:00:00",
            ),
            {},
        )
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == int(ExitCode.NEEDS_CHECKS)
        mock_pipeline_cls.assert_called_once_with()


def test_cli_audit_with_ocr_pack_passes_manifest_to_pipeline():
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    pkt_dir = repo_root / "synthetic_data" / "pkt_01_clean"
    subhadra_pack = repo_root / "packs" / "odisha.subhadra"

    test_args = ["docuready", "audit", str(pkt_dir), "--ocr-pack", str(subhadra_pack), "--json"]
    with patch("docuready.pipeline.AuditPipeline") as mock_pipeline_cls:
        from docuready.domain.enums import Readiness
        from docuready.domain.models import AuditResult

        mock_inst = mock_pipeline_cls.return_value
        mock_inst.load_and_audit_packet.return_value = (
            AuditResult(
                packet_id="PKT_01_CLEAN",
                scheme_name="generic.demo",
                readiness_score=100,
                overall_status=Readiness.NO_ISSUES_FOUND,
                findings=[],
                summary_counts={},
                execution_time_ms=1.0,
                timestamp="2026-11-27T00:00:00",
            ),
            {},
        )
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == int(ExitCode.NEEDS_CHECKS)

        assert mock_pipeline_cls.call_count == 1
        passed_pack = mock_pipeline_cls.call_args.kwargs.get("pack")
        assert passed_pack is not None
        assert passed_pack.pack_id == "odisha.subhadra"


def test_cli_audit_with_invalid_ocr_pack_fails_clearly(tmp_path, capsys):
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    pkt_dir = repo_root / "synthetic_data" / "pkt_01_clean"

    # Nonexistent pack path
    test_args = ["docuready", "audit", str(pkt_dir), "--ocr-pack", str(tmp_path / "missing_pack")]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == int(ExitCode.USAGE_ERROR)
    assert "not found" in capsys.readouterr().err.lower()

    # Invalid pack manifest (missing pack.yaml)
    bad_pack = tmp_path / "bad_pack"
    bad_pack.mkdir()
    test_args_bad = ["docuready", "audit", str(pkt_dir), "--ocr-pack", str(bad_pack)]
    with patch.object(sys, "argv", test_args_bad):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == int(ExitCode.USAGE_ERROR)
    assert "invalid ocr pack" in capsys.readouterr().err.lower()
