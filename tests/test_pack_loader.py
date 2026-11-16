"""Unit tests for Scheme Pack loader and Safe YAML parser (Task T3.1)."""

import pathlib
import pytest

from docuready.rules.loader import (
    DuplicateKeyError,
    PackLoadError,
    load_pack,
    load_yaml_with_unique_keys,
)
from docuready.rules.schema import PackManifest, SourceManifest


def test_unique_key_loader_detects_duplicate_mapping_keys():
    clean_yaml = """
    key1: value1
    key2: value2
    nested:
      a: 1
      b: 2
    """
    parsed = load_yaml_with_unique_keys(clean_yaml)
    assert parsed == {
        "key1": "value1",
        "key2": "value2",
        "nested": {"a": 1, "b": 2},
    }

    duplicate_yaml = """
    pack_id: test.pack
    version: "1.0.0"
    pack_id: duplicate.pack
    """
    with pytest.raises(DuplicateKeyError) as exc:
        load_yaml_with_unique_keys(duplicate_yaml)
    assert "Duplicate mapping key 'pack_id'" in str(exc.value)


def test_unique_key_loader_detects_duplicate_nested_keys():
    nested_dup = """
    parameters:
      income_cap: 250000
      income_cap: 300000
    """
    with pytest.raises(DuplicateKeyError) as exc:
        load_yaml_with_unique_keys(nested_dup)
    assert "Duplicate mapping key 'income_cap'" in str(exc.value)


def test_load_pack_on_generic_demo():
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    demo_pack_dir = repo_root / "packs" / "generic.demo"

    pack_manifest, source_manifest = load_pack(demo_pack_dir)
    assert isinstance(pack_manifest, PackManifest)
    assert isinstance(source_manifest, SourceManifest)
    assert pack_manifest.pack_id == "generic.demo"
    assert source_manifest.pack_id == "generic.demo"
    assert pack_manifest.version == "2.1.0"
    assert source_manifest.version == "2.1.0"


def test_load_pack_missing_directory(tmp_path):
    missing_dir = tmp_path / "does_not_exist"
    with pytest.raises(PackLoadError) as exc:
        load_pack(missing_dir)
    assert "does not exist" in str(exc.value)


def test_load_pack_missing_files(tmp_path):
    pack_dir = tmp_path / "incomplete_pack"
    pack_dir.mkdir()

    # Missing both pack.yaml and sources.yaml
    with pytest.raises(PackLoadError) as exc:
        load_pack(pack_dir)
    assert "Missing required pack manifest" in str(exc.value)

    # Missing sources.yaml
    (pack_dir / "pack.yaml").write_text("pack_id: test\nversion: '1.0'\nstatus: draft\n", encoding="utf-8")
    with pytest.raises(PackLoadError) as exc:
        load_pack(pack_dir)
    assert "Missing required sources registry" in str(exc.value)


def test_load_pack_id_mismatch(tmp_path):
    pack_dir = tmp_path / "mismatch_pack"
    pack_dir.mkdir()

    (pack_dir / "pack.yaml").write_text(
        "pack_id: pack.alpha\nversion: '1.0'\nstatus: draft\n",
        encoding="utf-8",
    )
    (pack_dir / "sources.yaml").write_text(
        "pack_id: pack.beta\nversion: '1.0'\n",
        encoding="utf-8",
    )

    with pytest.raises(PackLoadError) as exc:
        load_pack(pack_dir)
    assert "Pack ID mismatch" in str(exc.value)


def test_load_pack_syntax_error(tmp_path):
    pack_dir = tmp_path / "syntax_error_pack"
    pack_dir.mkdir()

    (pack_dir / "pack.yaml").write_text("pack_id: [unclosed list", encoding="utf-8")
    (pack_dir / "sources.yaml").write_text("pack_id: valid\nversion: '1.0'\n", encoding="utf-8")

    with pytest.raises(PackLoadError) as exc:
        load_pack(pack_dir)
    assert "YAML syntax error" in str(exc.value)
