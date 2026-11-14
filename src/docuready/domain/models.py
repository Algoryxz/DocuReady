"""
Data Models and Enums for DocuReady MVP — Loop 3 Evidence Calibration & Safety
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


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


class EvidenceState(str, Enum):
    """
    Explicit lifecycle state of extracted document evidence.
    Note: VERIFIED_TEXT denotes native vector font extraction with direct provenance;
    it does NOT denote legal statutory authentication.
    """
    VERIFIED_TEXT = "VERIFIED_TEXT"      # Native PDF vector text with direct source provenance
    OCR_EXTRACTED = "OCR_EXTRACTED"      # Local OCR result with high calibrated confidence
    AMBIGUOUS = "AMBIGUOUS"              # Multiple candidate interpretations or date format ambiguity
    LOW_CONFIDENCE = "LOW_CONFIDENCE"    # Calibrated confidence below safety threshold (<0.65)
    NOT_FOUND = "NOT_FOUND"              # Expected field not detected in document
    UNREADABLE = "UNREADABLE"            # Document scan corrupted, blank, or illegible
    CONFLICTING = "CONFLICTING"          # Contradictory evidence detected within same document


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


class AuditResult(BaseModel):
    packet_id: str
    scheme_name: str
    readiness_score: int
    overall_status: str
    findings: List[Finding]
    summary_counts: Dict[str, int]
    execution_time_ms: float
    timestamp: str
