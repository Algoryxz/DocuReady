"""
Data Models and Enums for DocuReady MVP — Loop 3 Evidence Calibration & Safety
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, PrivateAttr, model_serializer, model_validator

from docuready.domain.enums import (
    EvidenceState,
    ExtractionMethod,
    MatchGrade,
    Raw,
    Readiness,
    Status,
    coerce_extraction_method,
)


class DocumentType(str, Enum):
    INCOME_CERT = "INCOME_CERT"
    CASTE_CERT = "CASTE_CERT"
    RESIDENCE_CERT = "RESIDENCE_CERT"
    MARKSHEET = "MARKSHEET"
    BANK_PASSBOOK = "BANK_PASSBOOK"
    APPLICATION_FORM = "APPLICATION_FORM"
    AADHAAR = "AADHAAR"


DOC_TYPE_LABELS = {
    DocumentType.INCOME_CERT: "Income Certificate",
    DocumentType.CASTE_CERT: "Caste Certificate",
    DocumentType.RESIDENCE_CERT: "Residence / Domicile Certificate",
    DocumentType.MARKSHEET: "Academic Marksheet",
    DocumentType.BANK_PASSBOOK: "Bank Passbook",
    DocumentType.APPLICATION_FORM: "Scheme Application Form",
    DocumentType.AADHAAR: "Aadhaar Card"
}


class FindingStatus(str, Enum):
    PASS = "PASS"        # Deterministic check passed
    REVIEW = "REVIEW"    # Discrepancy needs human judgment
    FAIL = "FAIL"        # Deterministic rule violated
    UNKNOWN = "UNKNOWN"  # Evidence unavailable or unreadable


class Severity(str, Enum):
    FATAL = "FATAL"        # -35 points, halts submission
    CRITICAL = "CRITICAL"  # -25 points, serious discrepancy
    REVIEW = "REVIEW"      # -10 points, variance needing human judgment
    WARNING = "WARNING"    # -5 points, advisory
    INFO = "INFO"          # 0 points, informational check


# Re-exported from docuready.domain.enums
ExtractionMethod = ExtractionMethod




class EvidenceProvenance(BaseModel):
    document_type: str
    file_name: str
    page_number: Optional[int] = 1
    bounding_box: Optional[List[float]] = None  # [x0, y0, x1, y1]
    raw_snippet: str = ""
    extracted_field: str = ""
    extraction_method: str = "NATIVE_VECTOR"
    ocr_confidence: Optional[float] = None


class ExtractedField(BaseModel):
    field_name: str
    raw_value: str
    normalized_value: Any = None
    confidence: float = 1.0
    extraction_method: str = "NATIVE_VECTOR"
    evidence_state: EvidenceState = EvidenceState.VERIFIED_TEXT
    calibrated_confidence: float = 1.0  # 0.0 to 1.0 calibrated correctness probability
    raw_ocr_token_confidence: Optional[float] = None
    supporting_tokens_count: int = 1
    label_detected: bool = True
    label_distance_pt: float = 0.0
    candidate_count: int = 1
    format_valid: bool = True
    provenance: Optional[EvidenceProvenance] = None
    is_uncertain: bool = False
    uncertainty_reason: Optional[str] = None


class ExtractedDocument(BaseModel):
    doc_type: DocumentType
    file_path: str
    status: str = "VALID"  # VALID, UNREADABLE, MISSING, CORRUPTED
    fields: Dict[str, ExtractedField] = Field(default_factory=dict)
    raw_text: str = ""
    page_count: int = 1
    extraction_method: str = "NATIVE_VECTOR"
    mean_ocr_confidence: Optional[float] = None
    expected_slot: Optional[DocumentType] = Field(default=None, exclude=True)
    detected_type: Optional[DocumentType] = Field(default=None, exclude=True)
    classification_details: Optional[Dict[str, Any]] = Field(default=None, exclude=True)


class Finding(BaseModel):
    rule_id: str
    rule_name: str
    status: Status
    severity: Severity
    penalty: int = 0
    field: str
    documents_involved: List[str]
    message: str
    evidence: List[EvidenceProvenance] = Field(default_factory=list)
    remediation: str
    statutory_reference: str
    match_grade: Optional[MatchGrade] = Field(default=None, exclude=True)

    # This excluded field preserves the legacy snapshot label strictly for
    # model_dump()/golden regression serialization. Runtime status is V2.
    legacy_status_snapshot: str = Field(default="", exclude=True, repr=False)
    _reason_code: Optional[str] = PrivateAttr(default=None)
    _raw_result: Optional[Raw] = PrivateAttr(default=None)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_status_input(cls, values):
        if not isinstance(values, dict):
            return values
        data = dict(values)
        raw_status = data.get("status")
        if raw_status is not None:
            raw_value = raw_status.value if isinstance(raw_status, Enum) else str(raw_status)
            data.setdefault("legacy_status_snapshot", raw_value)
            # No finding may expose PASS or FAIL before the safety resolver
            # has inspected its provenance and supporting evidence.
            data["status"] = Status.REVIEW
        return data

    @model_serializer(mode="wrap")
    def serialize_legacy_status_for_golden(self, handler, info):
        data = handler(self)
        if isinstance(data, dict) and self.legacy_status_snapshot:
            data["status"] = self.legacy_status_snapshot
        return data

    def set_resolution(
        self,
        raw: Raw,
        status: Status,
        reason_code: str,
        match_grade: Optional[MatchGrade] = None,
    ) -> None:
        self._raw_result = raw
        self.status = status
        self._reason_code = reason_code
        if match_grade is not None:
            self.match_grade = match_grade

    @property
    def resolved_status(self) -> Status:
        """Compatibility accessor; canonical status is stored in status."""
        return self.status

    @property
    def reason_code(self) -> str:
        return self._reason_code or "INSUFFICIENT_DATA"

    @property
    def raw_result(self) -> Optional[Raw]:
        return self._raw_result


class AuditResult(BaseModel):
    packet_id: str
    scheme_name: str
    readiness_score: int
    overall_status: Readiness
    findings: List[Finding]
    summary_counts: Dict[str, int]
    execution_time_ms: float
    timestamp: str
    as_of: Optional[str] = Field(default=None, exclude=True)

    # Excluded from normal V2 models, emitted only by the serializer so the
    # immutable legacy_v0 baseline remains comparable.
    legacy_overall_status_snapshot: str = Field(default="", exclude=True, repr=False)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_readiness_input(cls, values):
        if not isinstance(values, dict):
            return values
        data = dict(values)
        raw_status = data.get("overall_status")
        if raw_status is not None:
            raw_value = raw_status.value if isinstance(raw_status, Enum) else str(raw_status)
            data.setdefault("legacy_overall_status_snapshot", raw_value)
            legacy_mapping = {
                "READY_TO_SUBMIT": Readiness.NO_ISSUES_FOUND,
                "REVIEW_RECOMMENDED": Readiness.NEEDS_CHECKS,
                "UNREADABLE_PACKET": Readiness.NEEDS_CHECKS,
                "ACTION_REQUIRED": Readiness.NOT_READY,
                "REJECT_PRECHECK": Readiness.NOT_READY,
            }
            data["overall_status"] = legacy_mapping.get(raw_value, raw_status)
        return data

    @model_validator(mode="after")
    def derive_readiness_from_findings(self):
        from docuready.outcome.resolver import resolve_readiness

        self.overall_status = resolve_readiness(
            finding.resolved_status for finding in self.findings
        )
        return self

    @model_serializer(mode="wrap")
    def serialize_legacy_readiness_for_golden(self, handler, info):
        data = handler(self)
        if isinstance(data, dict) and self.legacy_overall_status_snapshot:
            data["overall_status"] = self.legacy_overall_status_snapshot
        return data

    @property
    def readiness(self) -> Readiness:
        """Canonical V2 readiness stored on the model."""
        return self.overall_status

    @property
    def v2_summary_counts(self) -> Dict[str, int]:
        return {
            status.value: sum(
                1 for finding in self.findings if finding.resolved_status is status
            )
            for status in Status
        }

    def to_public_dict(self, canonical: bool = False) -> Dict[str, Any]:
        """Return a public V2 projection with only canonical statuses.

        When canonical=True, volatile runtime telemetry (e.g. execution_time_ms)
        is excluded to ensure byte-for-byte deterministic reproducibility across replays.
        """
        data = self.model_dump(mode="json")
        readiness = self.readiness
        data["overall_status"] = readiness.value
        data["readiness"] = readiness.value
        data["summary_counts"] = self.v2_summary_counts
        if self.as_of is not None:
            data["as_of"] = self.as_of
        for item, finding in zip(data.get("findings", []), self.findings):
            item["status"] = finding.resolved_status.value
            item["reason_code"] = finding.reason_code
            if finding.match_grade is not None:
                item["match_grade"] = finding.match_grade.value
        if canonical:
            data.pop("execution_time_ms", None)
        return data

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Return a canonical dictionary projection for deterministic replay comparison."""
        return self.to_public_dict(canonical=True)
