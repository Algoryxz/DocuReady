"""
Data Models and Enums for DocuReady MVP — Loop 3 Evidence Calibration & Safety
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, PrivateAttr

from docuready.domain.enums import EvidenceState, Raw, Readiness, Status


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


class ExtractionMethod(str, Enum):
    NATIVE_VECTOR = "NATIVE_VECTOR"
    LOCAL_OCR = "LOCAL_OCR"
    UNEXTRACTED = "UNEXTRACTED"




class EvidenceProvenance(BaseModel):
    document_type: str
    file_name: str
    page_number: int = 1
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


class Finding(BaseModel):
    rule_id: str
    rule_name: str
    status: FindingStatus
    severity: Severity
    penalty: int = 0
    field: str
    documents_involved: List[str]
    message: str
    evidence: List[EvidenceProvenance] = Field(default_factory=list)
    remediation: str
    statutory_reference: str

    # V2 resolution is kept outside the legacy serialized shape so the frozen
    # legacy_v0 golden snapshots remain byte-for-byte comparable.
    _resolved_status: Optional[Status] = PrivateAttr(default=None)
    _reason_code: Optional[str] = PrivateAttr(default=None)
    _raw_result: Optional[Raw] = PrivateAttr(default=None)

    def set_resolution(self, raw: Raw, status: Status, reason_code: str) -> None:
        self._raw_result = raw
        self._resolved_status = status
        self._reason_code = reason_code

    @property
    def resolved_status(self) -> Status:
        # Fail closed when a finding was constructed outside the audited
        # pipeline and has not yet been passed through the resolver.
        return self._resolved_status or Status.REVIEW

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
    overall_status: str
    findings: List[Finding]
    summary_counts: Dict[str, int]
    execution_time_ms: float
    timestamp: str

    @property
    def readiness(self) -> Readiness:
        """Canonical V2 packet readiness; legacy overall_status remains for golden tests."""
        from docuready.outcome.resolver import resolve_readiness

        return resolve_readiness(finding.resolved_status for finding in self.findings)

    @property
    def v2_summary_counts(self) -> Dict[str, int]:
        return {
            status.value: sum(
                1 for finding in self.findings if finding.resolved_status is status
            )
            for status in Status
        }

    def to_public_dict(self) -> Dict[str, Any]:
        """Return the canonical V2 report representation.

        Internal legacy fields remain available to tests and migration adapters,
        but public JSON uses only the V2 status/readiness vocabulary.
        """
        data = self.model_dump(mode="json")
        readiness = self.readiness
        data["overall_status"] = readiness.value
        data["readiness"] = readiness.value
        data["summary_counts"] = self.v2_summary_counts
        for item, finding in zip(data.get("findings", []), self.findings):
            item["status"] = finding.resolved_status.value
            item["reason_code"] = finding.reason_code
        return data
