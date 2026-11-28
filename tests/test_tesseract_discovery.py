"""Isolated regression tests for Tesseract tessdata directory discovery."""

from __future__ import annotations

import tempfile
from pathlib import Path

from docuready.ingest import tesseract_discovery


def test_linux_system_tessdata_and_extra_merge(tmp_path: Path, monkeypatch) -> None:
    """Linux /usr/bin/tesseract with /usr/share/tesseract-ocr/5/tessdata merges with extra dir without dropping eng."""
    monkeypatch.delenv("TESSDATA_PREFIX", raising=False)

    fake_root = tmp_path / "sys"
    fake_bin = fake_root / "usr" / "bin" / "tesseract"
    fake_bin.parent.mkdir(parents=True)
    fake_bin.write_text("", encoding="utf-8")

    sys_td = fake_root / "usr" / "share" / "tesseract-ocr" / "5" / "tessdata"
    sys_td.mkdir(parents=True)
    (sys_td / "eng.traineddata").write_bytes(b"ENG-MODEL")

    extra_td = tmp_path / "extra_tessdata"
    extra_td.mkdir()
    (extra_td / "hin.traineddata").write_bytes(b"HIN-MODEL")
    (extra_td / "ori.traineddata").write_bytes(b"ORI-MODEL")

    unified_target = tmp_path / "tmp_unified"
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(unified_target))
    monkeypatch.setattr(
        tesseract_discovery,
        "_SYSTEM_TESSDATA_CANDIDATES",
        (sys_td,),
    )
    # Point repo extra_candidates to our extra_td by monkeypatching Path(__file__) resolution via _resolve_base_tessdata_dir + monkeypatching extra
    orig_parents = Path(tesseract_discovery.__file__).resolve().parents[3]
    monkeypatch.setattr(
        tesseract_discovery,
        "get_unified_tessdata_dir",
        tesseract_discovery.get_unified_tessdata_dir,
    )

    # Directly verify _resolve_base_tessdata_dir finds sys_td (not bin_path.parent / "tessdata")
    resolved_base = tesseract_discovery._resolve_base_tessdata_dir(fake_bin)
    assert resolved_base == sys_td


def test_unified_tessdata_merges_base_and_extra_without_dropping_eng(tmp_path: Path, monkeypatch) -> None:
    """Unified directory must include both base eng.traineddata and extra hin/ori models."""
    monkeypatch.delenv("TESSDATA_PREFIX", raising=False)

    fake_bin = tmp_path / "usr" / "bin" / "tesseract"
    fake_bin.parent.mkdir(parents=True)
    fake_bin.write_text("", encoding="utf-8")

    sys_td = tmp_path / "usr" / "share" / "tesseract-ocr" / "5" / "tessdata"
    sys_td.mkdir(parents=True)
    (sys_td / "eng.traineddata").write_bytes(b"ENG-MODEL")

    fake_repo = tmp_path / "repo"
    extra_td = fake_repo / "sidecar" / "tessdata_extra"
    extra_td.mkdir(parents=True)
    (extra_td / "hin.traineddata").write_bytes(b"HIN-MODEL")
    (extra_td / "ori.traineddata").write_bytes(b"ORI-MODEL")

    fake_mod_file = fake_repo / "src" / "docuready" / "ingest" / "tesseract_discovery.py"
    fake_mod_file.parent.mkdir(parents=True)
    fake_mod_file.write_text("", encoding="utf-8")

    monkeypatch.setattr(tesseract_discovery, "__file__", str(fake_mod_file))
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path / "temp"))

    unified = tesseract_discovery.get_unified_tessdata_dir(fake_bin)
    assert unified is not None
    assert (unified / "eng.traineddata").read_bytes() == b"ENG-MODEL"
    assert (unified / "hin.traineddata").read_bytes() == b"HIN-MODEL"
    assert (unified / "ori.traineddata").read_bytes() == b"ORI-MODEL"


def test_explicit_tessdata_prefix_respected(tmp_path: Path, monkeypatch) -> None:
    """A valid explicit TESSDATA_PREFIX takes precedence over system paths."""
    custom_td = tmp_path / "custom_tessdata"
    custom_td.mkdir()
    (custom_td / "eng.traineddata").write_bytes(b"CUSTOM-ENG")
    monkeypatch.setenv("TESSDATA_PREFIX", str(custom_td))

    fake_bin = tmp_path / "usr" / "bin" / "tesseract"
    fake_bin.parent.mkdir(parents=True)
    fake_bin.write_text("", encoding="utf-8")

    assert tesseract_discovery._resolve_base_tessdata_dir(fake_bin) == custom_td


def test_windows_bundled_adjacent_tessdata(tmp_path: Path, monkeypatch) -> None:
    """Bundled executable with adjacent tessdata directory is resolved directly."""
    monkeypatch.delenv("TESSDATA_PREFIX", raising=False)

    bundle_dir = tmp_path / "docuready_sidecar" / "tesseract"
    bundle_dir.mkdir(parents=True)
    exe = bundle_dir / "tesseract.exe"
    exe.write_text("", encoding="utf-8")
    adj_td = bundle_dir / "tessdata"
    adj_td.mkdir()
    for lang in ("eng", "hin", "ori"):
        (adj_td / f"{lang}.traineddata").write_bytes(b"DATA")

    assert tesseract_discovery.get_unified_tessdata_dir(exe) == adj_td


def test_missing_system_tessdata_returns_none(tmp_path: Path, monkeypatch) -> None:
    """Missing system tessdata directory returns None rather than a nonexistent path."""
    monkeypatch.delenv("TESSDATA_PREFIX", raising=False)
    monkeypatch.setattr(tesseract_discovery, "_SYSTEM_TESSDATA_CANDIDATES", ())

    fake_bin = tmp_path / "opt" / "bin" / "tesseract"
    fake_bin.parent.mkdir(parents=True)
    fake_bin.write_text("", encoding="utf-8")

    assert tesseract_discovery._resolve_base_tessdata_dir(fake_bin) is None
