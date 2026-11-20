"""Safe YAML loading and schema validation for scheme packs (ARCHITECTURE_V2 §7)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Tuple

import yaml
from pydantic import ValidationError

from docuready.rules.schema import PackManifest, SourceManifest


class DuplicateKeyError(ValueError):
    """Raised when a YAML mapping contains duplicate keys."""

    pass


class PackLoadError(Exception):
    """Raised when a scheme pack cannot be found, loaded, or validated."""

    pass


class UniqueKeySafeLoader(yaml.SafeLoader):
    """PyYAML SafeLoader that raises DuplicateKeyError on duplicate mapping keys."""

    pass


def _construct_mapping_with_unique_keys(
    loader: UniqueKeySafeLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            line = getattr(key_node.start_mark, "line", 0) + 1
            col = getattr(key_node.start_mark, "column", 0) + 1
            raise DuplicateKeyError(
                f"Duplicate mapping key '{key}' found at line {line}, column {col}"
            )
        value = loader.construct_object(value_node, deep=deep)
        mapping[key] = value
    return mapping


UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_with_unique_keys,
)


def load_yaml_with_unique_keys(content: str, filename: str = "<yaml>") -> Any:
    """Parse YAML content ensuring no duplicate mapping keys exist."""
    try:
        return yaml.load(content, Loader=UniqueKeySafeLoader)
    except DuplicateKeyError:
        raise
    except yaml.YAMLError as exc:
        raise PackLoadError(f"YAML syntax error in {filename}: {exc}") from exc


def load_pack(pack_dir: Path | str) -> Tuple[PackManifest, SourceManifest]:
    """
    Load and validate pack.yaml and sources.yaml from a scheme pack directory.

    Returns:
        Tuple of (PackManifest, SourceManifest)

    Raises:
        PackLoadError if files are missing, malformed, or fail schema validation.
        DuplicateKeyError if either file contains duplicate mapping keys.
    """
    path = Path(pack_dir).resolve()
    if not path.exists():
        raise PackLoadError(f"Pack directory does not exist: {path}")
    if not path.is_dir():
        raise PackLoadError(f"Pack path is not a directory: {path}")

    pack_file = path / "pack.yaml"
    sources_file = path / "sources.yaml"

    if not pack_file.is_file():
        raise PackLoadError(f"Missing required pack manifest: {pack_file}")
    if not sources_file.is_file():
        raise PackLoadError(f"Missing required sources registry: {sources_file}")

    try:
        pack_text = pack_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise PackLoadError(f"Failed to read {pack_file}: {exc}") from exc

    try:
        sources_text = sources_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise PackLoadError(f"Failed to read {sources_file}: {exc}") from exc

    raw_pack = load_yaml_with_unique_keys(pack_text, str(pack_file))
    if not isinstance(raw_pack, dict):
        raise PackLoadError(f"Root of {pack_file} must be a YAML mapping")

    raw_sources = load_yaml_with_unique_keys(sources_text, str(sources_file))
    if not isinstance(raw_sources, dict):
        raise PackLoadError(f"Root of {sources_file} must be a YAML mapping")

    try:
        pack_manifest = PackManifest.model_validate(raw_pack)
    except ValidationError as exc:
        raise PackLoadError(f"Validation error in {pack_file}:\n{exc}") from exc

    try:
        source_manifest = SourceManifest.model_validate(raw_sources)
    except ValidationError as exc:
        raise PackLoadError(f"Validation error in {sources_file}:\n{exc}") from exc

    if pack_manifest.pack_id != source_manifest.pack_id:
        raise PackLoadError(
            f"Pack ID mismatch: {pack_file.name} declares '{pack_manifest.pack_id}', "
            f"but {sources_file.name} declares '{source_manifest.pack_id}'"
        )

    return pack_manifest, source_manifest
