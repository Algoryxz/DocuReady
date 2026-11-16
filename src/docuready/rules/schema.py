"""Pydantic v2 schemas for Scheme Packs and Source Registries (ARCHITECTURE_V2 §7)."""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional

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


class RemediationMetadata(BaseModel):
    """Citizen-facing remediation guidance when a rule defect is flagged."""

    model_config = ConfigDict(extra="forbid")

    authority: str
    replacement_document: Optional[str] = None
    steps: List[str] = Field(default_factory=list)


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


class PackManifest(BaseModel):
    """Declarative specification of a scheme pack (pack.yaml)."""

    model_config = ConfigDict(extra="forbid")

    pack_id: str
    version: str
    status: PackStatus
    effective: Optional[DateRange] = None
    as_of_required: bool = False
    parameters: Dict[str, Any] = Field(default_factory=dict)
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
    title: Optional[str] = None
    source_title: Optional[str] = None
    issuing_body: str
    url: Optional[str] = None
    official_url: Optional[str] = None
    retrieved_on: Optional[date] = None
    retrieval_date: Optional[date] = None
    status: SourceStatus
    reviewed_by: Optional[str] = None
    clause: Optional[str] = None
    supports_rule: Optional[bool] = None
    notes: Optional[str] = None
    original_rule_id: Optional[str] = None
    scheme_dependent_params: Optional[Dict[str, Any]] = None

    @field_validator("id")
    @classmethod
    def validate_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Source id cannot be empty")
        return v.strip()

    @model_validator(mode="after")
    def normalize_aliases(self) -> "SourceDefinition":
        if not self.title and self.source_title:
            self.title = self.source_title
        if not self.url and self.official_url:
            self.url = self.official_url
        if not self.retrieved_on and self.retrieval_date:
            self.retrieved_on = self.retrieval_date
        return self


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
