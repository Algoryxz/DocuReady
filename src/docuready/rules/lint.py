"""Scheme pack linting and integrity verification (ARCHITECTURE_V2 §7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from docuready.rules.loader import DuplicateKeyError, PackLoadError, load_pack
from docuready.rules.schema import (
    PackManifest,
    PackStatus,
    ParameterDeclaration,
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

# Supported parameter type contracts for closed primitives
PRIMITIVE_PARAMETER_CONTRACTS: Dict[str, Dict[str, str]] = {
    "require_document": {
        "min_pages": "int",
    },
    "field_present": {},
    "match_across": {
        "grade": "string",
        "threshold": "number",
    },
    "within_validity": {
        "validity_days": "int",
        "validity_months": "int",
        "validity_years": "int",
    },
    "numeric_cap": {
        "cap": "number",
        "comparator": "string",
    },
    "numeric_consistency": {
        "tolerance_pct": "number",
        "tolerance": "number",
    },
    "age_on": {
        "reference_date": "date",
        "min_age": "int",
        "max_age": "int",
    },
    "enum_in": {
        "allowed": "list[string]",
        "values": "list[string]",
    },
    "legible": {
        "min_confidence": "number",
    },
}

# Supported input field type contracts for closed primitives
PRIMITIVE_INPUT_CONTRACTS: Dict[str, Dict[str, str]] = {
    "require_document": {
        "slot": "string",
        "slots": "list[string]",
        "docs": "list[string]",
    },
    "field_present": {
        "field": "string",
        "docs": "list[string]",
        "slots": "list[string]",
    },
    "match_across": {
        "fields": "list[string]",
        "field": "string",
        "docs": "list[string]",
        "slots": "list[string]",
    },
    "within_validity": {
        "field": "string",
        "docs": "list[string]",
        "slots": "list[string]",
    },
    "numeric_cap": {
        "field": "string",
        "docs": "list[string]",
        "slots": "list[string]",
    },
    "numeric_consistency": {
        "fields": "list[string]",
        "docs": "list[string]",
        "slots": "list[string]",
    },
    "age_on": {
        "field": "string",
        "dob_field": "string",
        "docs": "list[string]",
        "slots": "list[string]",
    },
    "enum_in": {
        "field": "string",
        "docs": "list[string]",
        "slots": "list[string]",
    },
    "legible": {
        "field": "string",
        "slot": "string",
        "docs": "list[string]",
        "slots": "list[string]",
    },
}

ALLOWED_MATCH_GRADES: frozenset[str] = frozenset(
    {"name", "date", "id", "text"}
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


def _get_parameter_type(param_decl: Any) -> str:
    """Determine the canonical type of a declared parameter."""
    if isinstance(param_decl, ParameterDeclaration):
        t = param_decl.type.lower().strip()
        if t in ("string", "str"):
            return "string"
        if t in ("bool", "boolean"):
            return "bool"
        return t
    if isinstance(param_decl, dict) and "type" in param_decl:
        t = str(param_decl["type"]).lower().strip()
        if t in ("string", "str"):
            return "string"
        if t in ("bool", "boolean"):
            return "bool"
        return t
    if isinstance(param_decl, bool):
        return "bool"
    if isinstance(param_decl, int):
        return "int"
    if isinstance(param_decl, float):
        return "float"
    if isinstance(param_decl, date):
        return "date"
    if isinstance(param_decl, (list, tuple)):
        return "list"
    if isinstance(param_decl, str):
        try:
            date.fromisoformat(param_decl)
            return "date"
        except ValueError:
            return "string"
    return "unknown"


def _get_parameter_raw_value(param_decl: Any) -> Any:
    """Retrieve raw configured value from parameter declaration or literal."""
    if isinstance(param_decl, ParameterDeclaration):
        return param_decl.value
    if isinstance(param_decl, dict) and "value" in param_decl:
        return param_decl.get("value")
    return param_decl


def _is_type_compatible(actual: str, expected: str) -> bool:
    """Check if actual parameter type satisfies expected primitive parameter type."""
    if expected == "number":
        return actual in ("int", "float", "number")
    if expected == "int":
        return actual == "int"
    if expected == "float":
        return actual in ("float", "int", "number")
    if expected == "string":
        return actual == "string"
    if expected == "date":
        return actual == "date"
    if expected == "bool":
        return actual == "bool"
    if expected == "list":
        return actual == "list"
    if expected.startswith("list[") and expected.endswith("]"):
        return actual == "list"
    return False


def _is_valid_string_member(item: Any) -> bool:
    """Check whether an element is a valid non-empty string and not a boolean."""
    return isinstance(item, str) and not isinstance(item, bool) and bool(item.strip())


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
      7. Parameters: all $param references resolve in pack.yaml parameters with typed contract compatibility.
      8. Explanatory notes: unverified sources must provide notes.
      9. Exemptions: parameters referenced in exempt_when resolve and satisfy list type where required.
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
            continue

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

        # Validate primitive parameter contracts
        contract = PRIMITIVE_PARAMETER_CONTRACTS.get(rule.primitive, {})

        # Check for unsupported parameter keys
        for param_key in rule.params.keys():
            if param_key not in contract:
                result.add_error(
                    f"Rule specifies unsupported parameter '{param_key}' for primitive '{rule.primitive}'",
                    rule_id=rule.id,
                )

        # Check primitive-specific mandatory parameter requirements
        if rule.primitive == "numeric_cap" and "cap" not in rule.params:
            result.add_error(
                "Rule using primitive 'numeric_cap' missing required parameter 'cap'",
                rule_id=rule.id,
            )
        elif rule.primitive == "match_across" and "grade" not in rule.params:
            result.add_error(
                "Rule using primitive 'match_across' missing required parameter 'grade'",
                rule_id=rule.id,
            )
        elif rule.primitive == "within_validity" and not any(
            k in rule.params
            for k in ("validity_days", "validity_months", "validity_years")
        ):
            result.add_error(
                "Rule using primitive 'within_validity' must specify 'validity_days', 'validity_months', or 'validity_years'",
                rule_id=rule.id,
            )
        elif rule.primitive == "age_on":
            if "reference_date" not in rule.params:
                result.add_error(
                    "Rule using primitive 'age_on' missing required parameter 'reference_date'",
                    rule_id=rule.id,
                )
            if "min_age" not in rule.params and "max_age" not in rule.params:
                result.add_error(
                    "Rule using primitive 'age_on' must specify 'min_age' and/or 'max_age'",
                    rule_id=rule.id,
                )
        elif rule.primitive == "enum_in" and not any(
            k in rule.params for k in ("allowed", "values")
        ):
            result.add_error(
                "Rule using primitive 'enum_in' must specify 'allowed' or 'values'",
                rule_id=rule.id,
            )
        elif rule.primitive == "legible" and "min_confidence" not in rule.params:
            result.add_error(
                "Rule using primitive 'legible' missing required parameter 'min_confidence'",
                rule_id=rule.id,
            )

        # Check parameter types and $param resolution in rule.params
        for param_key, param_val in rule.params.items():
            if param_key not in contract:
                continue
            expected_type = contract[param_key]

            if isinstance(param_val, str) and param_val.startswith("$") and not param_val.startswith("$$"):
                pref = param_val[1:]
                if pref not in pack_manifest.parameters:
                    result.add_error(
                        f"Rule references undefined parameter '${pref}' in '{param_key}'",
                        rule_id=rule.id,
                    )
                else:
                    p_obj = pack_manifest.parameters[pref]
                    raw_val = _get_parameter_raw_value(p_obj)
                    if raw_val is None:
                        result.add_error(
                            f"Referenced parameter '${pref}' in '{param_key}' has no configured value; absent parameter values cannot be treated as executable configuration",
                            rule_id=rule.id,
                        )
                    actual_type = _get_parameter_type(p_obj)
                    if not _is_type_compatible(actual_type, expected_type):
                        exp_display = "list" if expected_type == "list[string]" else expected_type
                        result.add_error(
                            f"Parameter '${pref}' for {rule.primitive}.{param_key} must be {exp_display}, got {actual_type}",
                            rule_id=rule.id,
                        )
                    else:
                        if expected_type == "string":
                            if not _is_valid_string_member(raw_val):
                                result.add_error(
                                    f"Referenced parameter '${pref}' for {rule.primitive}.{param_key} must be a non-empty string, got {raw_val!r}",
                                    rule_id=rule.id,
                                )
                        elif expected_type == "list[string]":
                            if isinstance(p_obj, ParameterDeclaration) and p_obj.item_type:
                                if p_obj.item_type.lower().strip() not in ("string", "str"):
                                    result.add_error(
                                        f"Parameter '${pref}' for {rule.primitive}.{param_key} has item_type '{p_obj.item_type}', expected 'string'",
                                        rule_id=rule.id,
                                    )
                            if isinstance(raw_val, list):
                                for idx, elem in enumerate(raw_val):
                                    if not _is_valid_string_member(elem):
                                        result.add_error(
                                            f"Parameter '${pref}' for {rule.primitive}.{param_key} contains non-string element at index {idx} ({elem!r}) of type {type(elem).__name__}",
                                            rule_id=rule.id,
                                        )

                    # Check match_across grade value if constant
                    if rule.primitive == "match_across" and param_key == "grade":
                        if not isinstance(raw_val, str) or raw_val.lower().strip() not in ALLOWED_MATCH_GRADES:
                            result.add_error(
                                f"Invalid match grade '{raw_val}' in parameter '${pref}'. Allowed: {sorted(ALLOWED_MATCH_GRADES)}",
                                rule_id=rule.id,
                            )
            elif isinstance(param_val, list):
                if not (expected_type == "list" or expected_type.startswith("list[")):
                    result.add_error(
                        f"Literal parameter '{param_key}' for {rule.primitive} must be {expected_type}, got list",
                        rule_id=rule.id,
                    )
                else:
                    if expected_type == "list[string]":
                        for idx, item in enumerate(param_val):
                            if isinstance(item, str) and item.startswith("$") and not item.startswith("$$"):
                                pref = item[1:]
                                if pref not in pack_manifest.parameters:
                                    result.add_error(
                                        f"Rule references undefined parameter '${pref}' in '{param_key}'",
                                        rule_id=rule.id,
                                    )
                                else:
                                    p_obj = pack_manifest.parameters[pref]
                                    raw_val = _get_parameter_raw_value(p_obj)
                                    if raw_val is None:
                                        result.add_error(
                                            f"Referenced parameter '${pref}' in '{param_key}' list has no configured value; absent parameter values cannot be treated as executable configuration",
                                            rule_id=rule.id,
                                        )
                                    actual_type = _get_parameter_type(p_obj)
                                    if not _is_type_compatible(actual_type, "string"):
                                        result.add_error(
                                            f"Parameter '${pref}' in {rule.primitive}.{param_key} list must be string, got {actual_type}",
                                            rule_id=rule.id,
                                        )
                            elif not _is_valid_string_member(item):
                                result.add_error(
                                    f"Literal list element in parameter '{param_key}' for {rule.primitive} must be a non-empty string, got {type(item).__name__} (index {idx})",
                                    rule_id=rule.id,
                                )
            else:
                lit_type = _get_parameter_type(param_val)
                if not _is_type_compatible(lit_type, expected_type):
                    exp_display = "list" if expected_type == "list[string]" else expected_type
                    result.add_error(
                        f"Literal parameter '{param_key}' for {rule.primitive} must be {exp_display}, got {lit_type}",
                        rule_id=rule.id,
                    )
                if rule.primitive == "match_across" and param_key == "grade":
                    if not isinstance(param_val, str) or param_val.lower().strip() not in ALLOWED_MATCH_GRADES:
                        result.add_error(
                            f"Invalid match grade '{param_val}'. Allowed: {sorted(ALLOWED_MATCH_GRADES)}",
                            rule_id=rule.id,
                        )

        # Check rule.inputs contracts and $param resolution
        input_contract = PRIMITIVE_INPUT_CONTRACTS.get(rule.primitive, {})
        for in_key, in_val in rule.inputs.items():
            if in_key not in input_contract:
                refs = _extract_param_references(in_val)
                if refs:
                    for pref in sorted(refs):
                        result.add_error(
                            f"Rule references parameter '${pref}' in uncontracted input field '{in_key}' for primitive '{rule.primitive}'",
                            rule_id=rule.id,
                        )
                else:
                    result.add_error(
                        f"Rule specifies unsupported input field '{in_key}' for primitive '{rule.primitive}'",
                        rule_id=rule.id,
                    )
                continue

            expected_in_type = input_contract[in_key]

            if isinstance(in_val, str) and in_val.startswith("$") and not in_val.startswith("$$"):
                pref = in_val[1:]
                if pref not in pack_manifest.parameters:
                    result.add_error(
                        f"Rule references undefined parameter '${pref}' in 'inputs'",
                        rule_id=rule.id,
                    )
                else:
                    p_obj = pack_manifest.parameters[pref]
                    raw_val = _get_parameter_raw_value(p_obj)
                    if raw_val is None:
                        result.add_error(
                            f"Referenced parameter '${pref}' in 'inputs.{in_key}' has no configured value; absent parameter values cannot be treated as executable configuration",
                            rule_id=rule.id,
                        )
                    actual_type = _get_parameter_type(p_obj)
                    if not _is_type_compatible(actual_type, expected_in_type):
                        exp_display = "list" if expected_in_type == "list[string]" else expected_in_type
                        result.add_error(
                            f"Parameter '${pref}' for {rule.primitive}.inputs.{in_key} must be {exp_display}, got {actual_type}",
                            rule_id=rule.id,
                        )
                    else:
                        if expected_in_type == "string":
                            if not _is_valid_string_member(raw_val):
                                result.add_error(
                                    f"Referenced parameter '${pref}' for {rule.primitive}.inputs.{in_key} must be a non-empty string, got {raw_val!r}",
                                    rule_id=rule.id,
                                )
                        elif expected_in_type == "list[string]":
                            if isinstance(p_obj, ParameterDeclaration) and p_obj.item_type:
                                if p_obj.item_type.lower().strip() not in ("string", "str"):
                                    result.add_error(
                                        f"Parameter '${pref}' for {rule.primitive}.inputs.{in_key} has item_type '{p_obj.item_type}', expected 'string'",
                                        rule_id=rule.id,
                                    )
                            if isinstance(raw_val, list):
                                for idx, elem in enumerate(raw_val):
                                    if not _is_valid_string_member(elem):
                                        result.add_error(
                                            f"Parameter '${pref}' for {rule.primitive}.inputs.{in_key} contains non-string element at index {idx} ({elem!r}) of type {type(elem).__name__}",
                                            rule_id=rule.id,
                                        )
            elif isinstance(in_val, list):
                if not (expected_in_type == "list" or expected_in_type.startswith("list[")):
                    result.add_error(
                        f"Literal input '{in_key}' for {rule.primitive} must be {expected_in_type}, got list",
                        rule_id=rule.id,
                    )
                else:
                    for idx, item in enumerate(in_val):
                        if isinstance(item, str) and item.startswith("$") and not item.startswith("$$"):
                            pref = item[1:]
                            if pref not in pack_manifest.parameters:
                                result.add_error(
                                    f"Rule references undefined parameter '${pref}' in 'inputs'",
                                    rule_id=rule.id,
                                )
                            else:
                                p_obj = pack_manifest.parameters[pref]
                                raw_val = _get_parameter_raw_value(p_obj)
                                if raw_val is None:
                                    result.add_error(
                                        f"Referenced parameter '${pref}' in 'inputs.{in_key}' list has no configured value; absent parameter values cannot be treated as executable configuration",
                                        rule_id=rule.id,
                                    )
                                actual_type = _get_parameter_type(p_obj)
                                if not _is_type_compatible(actual_type, "string"):
                                    result.add_error(
                                        f"Parameter '${pref}' in {rule.primitive}.inputs.{in_key} list must be string, got {actual_type}",
                                        rule_id=rule.id,
                                    )
                        elif expected_in_type == "list[string]" and not _is_valid_string_member(item):
                            result.add_error(
                                f"Literal element in inputs.{in_key} for {rule.primitive} must be a non-empty string, got {type(item).__name__} (index {idx})",
                                rule_id=rule.id,
                            )
            else:
                lit_type = _get_parameter_type(in_val)
                if not _is_type_compatible(lit_type, expected_in_type):
                    exp_display = "list" if expected_in_type == "list[string]" else expected_in_type
                    result.add_error(
                        f"Literal input '{in_key}' for {rule.primitive} must be {exp_display}, got {lit_type}",
                        rule_id=rule.id,
                    )

        # Catch any remaining unreferenced $param in rule.inputs
        input_refs = _extract_param_references(rule.inputs)
        for pref in input_refs:
            if pref not in pack_manifest.parameters:
                if not any(f"references undefined parameter '${pref}' in 'inputs" in m.message for m in result.errors):
                    result.add_error(
                        f"Rule references undefined parameter '${pref}' in 'inputs'",
                        rule_id=rule.id,
                    )

        # Check rule.exempt_when shape and type contracts
        if rule.exempt_when is not None:
            if not isinstance(rule.exempt_when, dict) or len(rule.exempt_when) == 0:
                result.add_error(
                    f"exempt_when must be a non-empty dictionary with 'fact' and 'in', got {type(rule.exempt_when).__name__ if not isinstance(rule.exempt_when, dict) else 'empty dictionary'}",
                    rule_id=rule.id,
                )
            else:
                # 1. Validate 'fact'
                if "fact" not in rule.exempt_when:
                    result.add_error(
                        "exempt_when missing required field 'fact'",
                        rule_id=rule.id,
                    )
                else:
                    fact_val = rule.exempt_when["fact"]
                    if isinstance(fact_val, str) and fact_val.startswith("$") and not fact_val.startswith("$$"):
                        fref = fact_val[1:]
                        if fref not in pack_manifest.parameters:
                            result.add_error(
                                f"Rule references undefined parameter '${fref}' in 'exempt_when'",
                                rule_id=rule.id,
                            )
                        else:
                            fp_obj = pack_manifest.parameters[fref]
                            f_raw = _get_parameter_raw_value(fp_obj)
                            if f_raw is None:
                                result.add_error(
                                    f"Referenced parameter '${fref}' in 'exempt_when' has no configured value; absent parameter values cannot be treated as executable configuration",
                                    rule_id=rule.id,
                                )
                            f_type = _get_parameter_type(fp_obj)
                            if not _is_type_compatible(f_type, "string"):
                                result.add_error(
                                    f"Parameter '${fref}' for exempt_when 'fact' must be string, got {f_type}",
                                    rule_id=rule.id,
                                )
                    elif not _is_valid_string_member(fact_val):
                        result.add_error(
                            f"exempt_when 'fact' must be a non-empty string, got {type(fact_val).__name__}",
                            rule_id=rule.id,
                        )

                # 2. Validate 'in'
                if "in" not in rule.exempt_when:
                    result.add_error(
                        "exempt_when missing required field 'in'",
                        rule_id=rule.id,
                    )
                else:
                    in_list = rule.exempt_when["in"]
                    if isinstance(in_list, str) and in_list.startswith("$") and not in_list.startswith("$$"):
                        pref = in_list[1:]
                        if pref not in pack_manifest.parameters:
                            result.add_error(
                                f"Rule references undefined parameter '${pref}' in 'exempt_when'",
                                rule_id=rule.id,
                            )
                        else:
                            p_obj = pack_manifest.parameters[pref]
                            raw_val = _get_parameter_raw_value(p_obj)
                            if raw_val is None:
                                result.add_error(
                                    f"Referenced parameter '${pref}' in 'exempt_when' has no configured value; absent parameter values cannot be treated as executable configuration",
                                    rule_id=rule.id,
                                )
                            actual_type = _get_parameter_type(p_obj)
                            if actual_type != "list":
                                result.add_error(
                                    f"Parameter '${pref}' for exempt_when 'in' condition must be list, got {actual_type}",
                                    rule_id=rule.id,
                                )
                            else:
                                if isinstance(p_obj, ParameterDeclaration) and p_obj.item_type:
                                    if p_obj.item_type.lower().strip() not in ("string", "str"):
                                        result.add_error(
                                            f"Parameter '${pref}' for exempt_when 'in' has item_type '{p_obj.item_type}', expected 'string'",
                                            rule_id=rule.id,
                                        )
                                if isinstance(raw_val, list):
                                    for idx, elem in enumerate(raw_val):
                                        if not _is_valid_string_member(elem):
                                            result.add_error(
                                                f"Parameter '${pref}' for exempt_when 'in' contains non-string element at index {idx} ({elem!r}) of type {type(elem).__name__}",
                                                rule_id=rule.id,
                                            )
                    elif isinstance(in_list, list):
                        for idx, elem in enumerate(in_list):
                            if isinstance(elem, str) and elem.startswith("$") and not elem.startswith("$$"):
                                epref = elem[1:]
                                if epref not in pack_manifest.parameters:
                                    result.add_error(
                                        f"Rule references undefined parameter '${epref}' in 'exempt_when'",
                                        rule_id=rule.id,
                                    )
                                else:
                                    ep_obj = pack_manifest.parameters[epref]
                                    ep_raw = _get_parameter_raw_value(ep_obj)
                                    if ep_raw is None:
                                        result.add_error(
                                            f"Referenced parameter '${epref}' in 'exempt_when' list has no configured value; absent parameter values cannot be treated as executable configuration",
                                            rule_id=rule.id,
                                        )
                                    ep_type = _get_parameter_type(ep_obj)
                                    if not _is_type_compatible(ep_type, "string"):
                                        result.add_error(
                                            f"Parameter '${epref}' in exempt_when 'in' list must be string, got {ep_type}",
                                            rule_id=rule.id,
                                        )
                            elif not _is_valid_string_member(elem):
                                result.add_error(
                                    f"Literal element in exempt_when 'in' list must be a non-empty string, got {type(elem).__name__} (index {idx})",
                                    rule_id=rule.id,
                                )
                    else:
                        result.add_error(
                            f"exempt_when 'in' condition must be a list or $param referencing a list, got {type(in_list).__name__}",
                            rule_id=rule.id,
                        )

            # Catch any remaining unreferenced parameters in exempt_when
            exempt_refs = _extract_param_references(rule.exempt_when)
            for pref in exempt_refs:
                if pref not in pack_manifest.parameters:
                    if not any(f"references undefined parameter '${pref}' in exempt_when" in m.message for m in result.errors):
                        result.add_error(
                            f"Rule references undefined parameter '${pref}' in 'exempt_when'",
                            rule_id=rule.id,
                        )

    return result


def lint_all_packs(packs_root: Path | str, allow_draft: bool = False) -> List[LintResult]:
    """
    Discover and lint all scheme packs under packs_root.

    If packs_root contains pack.yaml or sources.yaml, it is linted as an explicit pack.
    Otherwise, every child directory inside packs_root is treated as an intended scheme pack.
    Any malformed child directory (missing pack.yaml, missing sources.yaml, or both) is reported
    as an error rather than being silently skipped.
    """
    root = Path(packs_root).resolve()
    if not root.exists() or not root.is_dir():
        return []

    # If root itself is a pack directory
    if (root / "pack.yaml").is_file() or (root / "sources.yaml").is_file():
        return [lint_pack(root, allow_draft=allow_draft)]

    # Scan child directories inside packs root
    results: List[LintResult] = []
    for sub in sorted(root.iterdir()):
        if sub.is_dir() and not sub.name.startswith(".") and sub.name != "__pycache__":
            results.append(lint_pack(sub, allow_draft=allow_draft))

    return results
