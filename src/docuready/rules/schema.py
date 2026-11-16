"""Pydantic v2 schemas for Scheme Packs and Source Registries (ARCHITECTURE_V2 §7)."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from docuready.domain.enums import MaxSeverity


class PackStatus(str, Enum):
    """Lifecycle status of a scheme pack."""

    DRAFT = "draft"
    DEMO_SNAPSHOT = "demo_snapshot"
    VERIFIED = "verified"


class SourceStatus(str, Enum):
    """Verification status of a statutory or regulatory citation source."""

    VERIFIED = "verified"
    PLACEHOLDER = "placeholder"
    UNVERIFIED = "unverified"


class DateRange(BaseModel):
    """Effective window for a scheme or policy pack."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    from_date: Optional[date] = Field(default=None, alias="from")
    to_date: Optional[date] = Field(default=None, alias="to")

    @model_validator(mode="after")
    def validate_range(self) -> "DateRange":
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError(
                f"Effective date range invalid: from ({self.from_date}) is after to ({self.to_date})"
            )
        return self


class DocSlotDefinition(BaseModel):
    """Document slot definition required by a pack."""

    model_config = ConfigDict(extra="forbid")

    ocr_langs: List[str] = Field(default_factory=lambda: ["eng"])
    required: bool = True


class CitationReference(BaseModel):
    """Citation linking a rule definition to an authoritative source."""

    model_config = ConfigDict(extra="forbid")

    source: str
    clause: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("source")
    @classmethod
    def validate_source_not_empty(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Citation source cannot be empty")
        return v.strip()


class RemediationMetadata(BaseModel):
    """Citizen-facing remediation guidance when a rule defect is flagged."""

    model_config = ConfigDict(extra="forbid")

    authority: str
    replacement_document: Optional[str] = None
    steps: List[str] = Field(default_factory=list)

    @field_validator("authority")
    @classmethod
    def validate_authority_not_empty(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Remediation authority cannot be empty")
        return v.strip()


class RuleDefinition(BaseModel):
    """Declarative rule specification grounded in a closed engine primitive."""

    model_config = ConfigDict(extra="forbid")

    id: str
    primitive: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)
    max_severity: MaxSeverity
    exempt_when: Optional[Dict[str, Any]] = None
    citation: CitationReference
    remediation: RemediationMetadata

    @field_validator("id")
    @classmethod
    def validate_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Rule id cannot be empty")
        return v.strip()

    @field_validator("primitive")
    @classmethod
    def validate_primitive_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Rule primitive cannot be empty")
        return v.strip()


class ParameterDeclaration(BaseModel):
    """Explicit typed declaration for a scheme pack parameter."""

    model_config = ConfigDict(extra="forbid")

    type: str
    value: Optional[Any] = None
    description: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = {
            "int",
            "float",
            "number",
            "string",
            "str",
            "bool",
            "boolean",
            "date",
            "list",
        }
        if not isinstance(v, str) or v.lower().strip() not in valid_types:
            raise ValueError(
                f"Invalid parameter type '{v}'. Allowed types: {sorted(valid_types)}"
            )
        return v.lower().strip()

    @model_validator(mode="after")
    def validate_value_type_consistency(self) -> "ParameterDeclaration":
        """
        Validate consistency between declared type and configured value.

        Omitted values (value is None) are permitted at schema level to allow
        abstract or runtime parameter declarations. When a non-null value is provided,
        it must strictly conform to the declared type without silent coercion.
        """
        if self.value is None:
            return self

        t = self.type.lower().strip()
        val = self.value

        if t == "int":
            if isinstance(val, bool) or not isinstance(val, int):
                raise ValueError(
                    f"Parameter of type 'int' must contain an integer (not a boolean or string), got {type(val).__name__} (value: {val!r})"
                )
        elif t == "float":
            if isinstance(val, bool) or not isinstance(val, (float, int)):
                raise ValueError(
                    f"Parameter of type 'float' must contain a valid numeric value, got {type(val).__name__} (value: {val!r})"
                )
        elif t == "number":
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                raise ValueError(
                    f"Parameter of type 'number' must contain an integer or float (not a boolean), got {type(val).__name__} (value: {val!r})"
                )
        elif t in ("string", "str"):
            if not isinstance(val, str):
                raise ValueError(
                    f"Parameter of type '{t}' must contain a string, got {type(val).__name__} (value: {val!r})"
                )
        elif t in ("bool", "boolean"):
            if not isinstance(val, bool):
                raise ValueError(
                    f"Parameter of type '{t}' must contain a boolean, got {type(val).__name__} (value: {val!r})"
                )
        elif t == "date":
            if isinstance(val, bool):
                raise ValueError("Parameter of type 'date' cannot be a boolean")
            if isinstance(val, (date, datetime)):
                pass
            elif isinstance(val, str):
                try:
                    date.fromisoformat(val)
                except (ValueError, TypeError) as exc:
                    raise ValueError(
                        f"Parameter of type 'date' contains invalid date string '{val}': {exc}"
                    )
            else:
                raise ValueError(
                    f"Parameter of type 'date' must contain a valid date representation, got {type(val).__name__} (value: {val!r})"
                )
        elif t == "list":
            if not isinstance(val, list):
                raise ValueError(
                    f"Parameter of type 'list' must contain a list, got {type(val).__name__} (value: {val!r})"
                )

        return self


class PackManifest(BaseModel):
    """Declarative specification of a scheme pack (pack.yaml)."""

    model_config = ConfigDict(extra="forbid")

    pack_id: str
    version: str
    status: PackStatus
    effective: Optional[DateRange] = None
    as_of_required: bool = False
    parameters: Dict[
        str,
        Union[ParameterDeclaration, int, float, str, bool, date, list],
    ] = Field(default_factory=dict)
    doc_slots: Dict[str, DocSlotDefinition] = Field(default_factory=dict)
    rules: List[RuleDefinition] = Field(default_factory=list)

    @field_validator("pack_id")
    @classmethod
    def validate_pack_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("pack_id cannot be empty")
        return v.strip()

    @model_validator(mode="after")
    def validate_unique_rule_ids(self) -> "PackManifest":
        seen_ids = set()
        for rule in self.rules:
            if rule.id in seen_ids:
                raise ValueError(f"Duplicate rule id '{rule.id}' in pack manifest")
            seen_ids.add(rule.id)
        return self


class SourceDefinition(BaseModel):
    """Individual citation source record in sources.yaml."""

    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    issuing_body: str
    status: SourceStatus
    url: Optional[str] = None
    retrieved_on: Optional[date] = None
    reviewed_by: Optional[str] = None
    clause: Optional[str] = None
    supports_rule: Optional[bool] = None
    notes: Optional[str] = None
    original_rule_id: Optional[str] = None
    scheme_dependent_params: Optional[Dict[str, Any]] = None

    # Optional alias fields to accommodate legacy input structures
    source_title: Optional[str] = None
    official_url: Optional[str] = None
    retrieval_date: Optional[date] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_and_validate_aliases(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        d = dict(data)

        # 1. title vs source_title
        has_title = "title" in d and d["title"] is not None
        has_legacy_title = "source_title" in d and d["source_title"] is not None
        if has_title and has_legacy_title:
            if str(d["title"]).strip() != str(d["source_title"]).strip():
                raise ValueError(
                    f"Conflicting aliases for title: 'title'='{d['title']}' but 'source_title'='{d['source_title']}'"
                )
        elif has_legacy_title and not has_title:
            d["title"] = d["source_title"]

        # 2. url vs official_url
        has_url = "url" in d and d["url"] is not None
        has_legacy_url = "official_url" in d and d["official_url"] is not None
        if has_url and has_legacy_url:
            if str(d["url"]).strip() != str(d["official_url"]).strip():
                raise ValueError(
                    f"Conflicting aliases for url: 'url'='{d['url']}' but 'official_url'='{d['official_url']}'"
                )
        elif has_legacy_url and not has_url:
            d["url"] = d["official_url"]

        # 3. retrieved_on vs retrieval_date
        has_retrieved_on = "retrieved_on" in d and d["retrieved_on"] is not None
        has_legacy_retrieval_date = (
            "retrieval_date" in d and d["retrieval_date"] is not None
        )
        if has_retrieved_on and has_legacy_retrieval_date:
            if str(d["retrieved_on"]).strip() != str(d["retrieval_date"]).strip():
                raise ValueError(
                    f"Conflicting aliases for retrieved_on: 'retrieved_on'='{d['retrieved_on']}' but 'retrieval_date'='{d['retrieval_date']}'"
                )
        elif has_legacy_retrieval_date and not has_retrieved_on:
            d["retrieved_on"] = d["retrieval_date"]

        return d

    @field_validator("id")
    @classmethod
    def validate_id_not_empty(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Source id must be a non-empty string")
        return v.strip()

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Source title must be a non-empty string")
        return v.strip()

    @field_validator("issuing_body")
    @classmethod
    def validate_issuing_body_not_empty(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Source issuing_body must be a non-empty string")
        return v.strip()


class SourceManifest(BaseModel):
    """Registry of authoritative statutory and regulatory sources (sources.yaml)."""

    model_config = ConfigDict(extra="forbid")

    pack_id: str
    version: str
    description: Optional[str] = None
    last_audited: Optional[date] = None
    audited_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    sources: List[SourceDefinition] = Field(default_factory=list)
    rules: Optional[List[Dict[str, Any]]] = None

    @field_validator("pack_id")
    @classmethod
    def validate_pack_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("pack_id cannot be empty")
        return v.strip()

    @model_validator(mode="after")
    def validate_unique_source_ids(self) -> "SourceManifest":
        seen_source_ids = set()
        for src in self.sources:
            if src.id in seen_source_ids:
                raise ValueError(f"Duplicate source id '{src.id}' in sources manifest")
            seen_source_ids.add(src.id)
        return self
