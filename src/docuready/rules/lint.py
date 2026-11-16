"""Scheme pack linting and integrity verification (ARCHITECTURE_V2 §7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from docuready.rules.loader import DuplicateKeyError, PackLoadError, load_pack
from docuready.rules.schema import (
    PackManifest,
    PackStatus,
    RuleDefinition,
    SourceDefinition,
    SourceManifest,
    SourceStatus,
)

CLOSED_PRIMITIVES: frozenset[str] = frozenset(
    {
        "require_document",
        "field_present",
        "match_across",
        "within_validity",
        "numeric_cap",
        "numeric_consistency",
        "age_on",
        "enum_in",
        "legible",
    }
)


@dataclass
class LintMessage:
    """Individual lint observation (ERROR or WARNING)."""

    level: str  # "ERROR" | "WARNING"
    message: str
    rule_id: Optional[str] = None
    source_id: Optional[str] = None

    def __str__(self) -> str:
        ctx = ""
        if self.rule_id:
            ctx = f"[rule: {self.rule_id}] "
        elif self.source_id:
            ctx = f"[source: {self.source_id}] "
        return f"{self.level}: {ctx}{self.message}"


@dataclass
class LintResult:
    """Result of linting a scheme pack."""

    pack_dir: Path
    pack_id: Optional[str] = None
    messages: List[LintMessage] = field(default_factory=list)

    @property
    def errors(self) -> List[LintMessage]:
        return [m for m in self.messages if m.level == "ERROR"]

    @property
    def warnings(self) -> List[LintMessage]:
        return [m for m in self.messages if m.level == "WARNING"]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(
        self,
        message: str,
        rule_id: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> None:
        self.messages.append(
            LintMessage(
                level="ERROR",
                message=message,
                rule_id=rule_id,
                source_id=source_id,
            )
        )

    def add_warning(
        self,
        message: str,
        rule_id: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> None:
        self.messages.append(
            LintMessage(
                level="WARNING",
                message=message,
                rule_id=rule_id,
                source_id=source_id,
            )
        )


def _extract_param_references(value: Any) -> Set[str]:
    """Recursively search for strings matching '$param_name'."""
    refs: Set[str] = set()
    if isinstance(value, str):
        if value.startswith("$") and len(value) > 1 and not value.startswith("$$"):
            refs.add(value[1:])
    elif isinstance(value, dict):
        for v in value.values():
            refs.update(_extract_param_references(v))
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            refs.update(_extract_param_references(item))
    return refs


def _is_valid_http_url(url: Optional[str]) -> bool:
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def lint_pack(pack_dir: Path | str, allow_draft: bool = False) -> LintResult:
    """
    Perform comprehensive lint checks on a scheme pack.

    Checks enforced:
      1. Valid directory and YAML files (no duplicate keys, schema valid).
      2. Status lifecycle: draft packs rejected unless allow_draft is True.
      3. Primitives: rule primitives must belong to CLOSED_PRIMITIVES.
      4. Remediation: every rule has authority and steps.
      5. Citation: every rule cites a valid source that resolves in sources.yaml.
      6. Source verification: verified sources must have valid URL, retrieval date, and reviewed_by.
      7. Parameters: all $param references resolve in pack.yaml parameters with type compatibility.
      8. Explanatory notes: unverified sources must provide notes.
    """
    path = Path(pack_dir).resolve()
    result = LintResult(pack_dir=path)

    try:
        pack_manifest, source_manifest = load_pack(path)
    except DuplicateKeyError as exc:
        result.add_error(f"Duplicate mapping key in pack YAML: {exc}")
        return result
    except PackLoadError as exc:
        result.add_error(f"Failed to load pack: {exc}")
        return result
    except Exception as exc:
        result.add_error(f"Unexpected error loading pack: {exc}")
        return result

    result.pack_id = pack_manifest.pack_id

    # 1. Draft lifecycle enforcement
    if pack_manifest.status == PackStatus.DRAFT and not allow_draft:
        result.add_error(
            f"Pack '{pack_manifest.pack_id}' is in 'draft' status. "
            "Draft packs are rejected unless --allow-draft is specified."
        )

    # 2. Build index of known sources from sources.yaml
    sources_by_id: Dict[str, SourceDefinition] = {
        s.id: s for s in source_manifest.sources
    }
    legacy_rules_by_id: Dict[str, Dict[str, Any]] = {}
    if source_manifest.rules:
        for r in source_manifest.rules:
            if isinstance(r, dict) and "id" in r:
                legacy_rules_by_id[r["id"]] = r

    # 3. Source definitions checks
    for src in source_manifest.sources:
        if src.status == SourceStatus.VERIFIED:
            missing_fields: List[str] = []
            if not _is_valid_http_url(src.url):
                missing_fields.append("valid official http(s) URL")
            if not src.retrieved_on:
                missing_fields.append("retrieval date (retrieved_on)")
            reviewer = src.reviewed_by or source_manifest.reviewed_by
            if not reviewer:
                missing_fields.append("reviewed_by")
            if missing_fields:
                result.add_error(
                    f"Verified source missing required metadata: {', '.join(missing_fields)}",
                    source_id=src.id,
                )
        elif src.status == SourceStatus.UNVERIFIED:
            if not src.notes or not src.notes.strip():
                result.add_error(
                    "Unverified source must provide explanatory notes",
                    source_id=src.id,
                )

    # 4. Check legacy rules entries in sources.yaml if present
    for r_id, r_data in legacy_rules_by_id.items():
        st = r_data.get("status")
        if st == "verified":
            url = r_data.get("official_url") or r_data.get("url")
            ret = r_data.get("retrieval_date") or r_data.get("retrieved_on")
            rev = r_data.get("reviewed_by") or source_manifest.reviewed_by
            missing = []
            if not _is_valid_http_url(url):
                missing.append("valid official http(s) URL")
            if not ret:
                missing.append("retrieval date")
            if not rev:
                missing.append("reviewed_by")
            if missing:
                result.add_error(
                    f"Verified rule source missing required metadata: {', '.join(missing)}",
                    source_id=r_id,
                )
        elif st == "unverified":
            if not r_data.get("notes"):
                result.add_error(
                    "Unverified rule source must provide explanatory notes",
                    source_id=r_id,
                )

    # 5. Rule definitions checks
    for rule in pack_manifest.rules:
        # Check closed primitive
        if rule.primitive not in CLOSED_PRIMITIVES:
            result.add_error(
                f"Unknown primitive '{rule.primitive}'. Must be one of: {sorted(CLOSED_PRIMITIVES)}",
                rule_id=rule.id,
            )

        # Check remediation authority
        if not rule.remediation.authority or not rule.remediation.authority.strip():
            result.add_error(
                "Rule missing required remediation authority",
                rule_id=rule.id,
            )

        # Check citation reference resolution
        cite_source_id = rule.citation.source
        matched_source: Optional[SourceDefinition] = sources_by_id.get(cite_source_id)
        matched_legacy: Optional[Dict[str, Any]] = legacy_rules_by_id.get(cite_source_id)

        if not matched_source and not matched_legacy:
            result.add_error(
                f"Citation source '{cite_source_id}' does not resolve in sources.yaml",
                rule_id=rule.id,
            )
        else:
            # Check if citing unverified source
            is_unverified = False
            if matched_source and matched_source.status in (
                SourceStatus.UNVERIFIED,
                SourceStatus.PLACEHOLDER,
            ):
                is_unverified = True
            elif matched_legacy and matched_legacy.get("status") in (
                "unverified",
                "placeholder",
            ):
                is_unverified = True

            if is_unverified:
                result.add_warning(
                    f"Cites unverified/placeholder source '{cite_source_id}' (source pending verification)",
                    rule_id=rule.id,
                )

        # Check $param resolution
        param_refs = _extract_param_references(rule.params) | _extract_param_references(
            rule.inputs
        )
        for pref in param_refs:
            if pref not in pack_manifest.parameters:
                result.add_error(
                    f"References undefined parameter '${pref}'",
                    rule_id=rule.id,
                )
            else:
                param_val = pack_manifest.parameters[pref]
                # Basic type compatibility checks for standard primitives
                if rule.primitive == "numeric_cap" and rule.params.get("cap") == f"${pref}":
                    if not isinstance(param_val, (int, float)):
                        result.add_error(
                            f"Parameter '${pref}' for numeric_cap must be numeric, got {type(param_val).__name__}",
                            rule_id=rule.id,
                        )
                elif rule.primitive == "within_validity" and rule.params.get("validity_days") == f"${pref}":
                    if not isinstance(param_val, int):
                        result.add_error(
                            f"Parameter '${pref}' for within_validity days must be int, got {type(param_val).__name__}",
                            rule_id=rule.id,
                        )

    return result


def lint_all_packs(packs_root: Path | str, allow_draft: bool = False) -> List[LintResult]:
    """
    Discover and lint all scheme packs under packs_root.

    A scheme pack is any directory containing pack.yaml or sources.yaml.
    """
    root = Path(packs_root).resolve()
    if not root.exists() or not root.is_dir():
        return []

    # If root itself is a pack directory
    if (root / "pack.yaml").is_file() or (root / "sources.yaml").is_file():
        return [lint_pack(root, allow_draft=allow_draft)]

    # Otherwise scan child directories
    results: List[LintResult] = []
    for sub in sorted(root.iterdir()):
        if sub.is_dir() and ((sub / "pack.yaml").is_file() or (sub / "sources.yaml").is_file()):
            results.append(lint_pack(sub, allow_draft=allow_draft))

    return results
