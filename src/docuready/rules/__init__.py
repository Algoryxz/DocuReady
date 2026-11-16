"""Deterministic validation rules, scheme packs, and citation registries."""

from docuready.rules.lint import (
    ALLOWED_MATCH_GRADES,
    CLOSED_PRIMITIVES,
    PRIMITIVE_PARAMETER_CONTRACTS,
    LintMessage,
    LintResult,
    lint_all_packs,
    lint_pack,
)
from docuready.rules.loader import (
    DuplicateKeyError,
    PackLoadError,
    UniqueKeySafeLoader,
    load_pack,
    load_yaml_with_unique_keys,
)
from docuready.rules.schema import (
    CitationReference,
    DateRange,
    DocSlotDefinition,
    PackManifest,
    PackStatus,
    ParameterDeclaration,
    RemediationMetadata,
    RuleDefinition,
    SourceDefinition,
    SourceManifest,
    SourceStatus,
)
from docuready.rules.slot_validator import validate_packet_slots, validate_slot
from docuready.rules.validator import DocuReadyValidator, SchemeConfig

__all__ = [
    "DocuReadyValidator",
    "SchemeConfig",
    "validate_slot",
    "validate_packet_slots",
    # T3.1 exports
    "PackStatus",
    "SourceStatus",
    "DateRange",
    "DocSlotDefinition",
    "CitationReference",
    "RemediationMetadata",
    "RuleDefinition",
    "ParameterDeclaration",
    "PackManifest",
    "SourceDefinition",
    "SourceManifest",
    "DuplicateKeyError",
    "PackLoadError",
    "UniqueKeySafeLoader",
    "load_pack",
    "load_yaml_with_unique_keys",
    "CLOSED_PRIMITIVES",
    "PRIMITIVE_PARAMETER_CONTRACTS",
    "ALLOWED_MATCH_GRADES",
    "LintMessage",
    "LintResult",
    "lint_pack",
    "lint_all_packs",
]
