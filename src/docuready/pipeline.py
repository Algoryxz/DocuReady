"""
End-to-End Audit & Document Ingestion Pipeline for DocuReady MVP
Connects file ingestion, field extraction, validation, and document replacement.
"""

from __future__ import annotations
import os
import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
from docuready.domain.models import (
    DocumentType, ExtractedDocument, AuditResult, FindingStatus
)
from docuready.ingest.extractor import DocumentExtractor, detect_document_type, get_slot_ocr_langs
from docuready.rules.validator import DocuReadyValidator, SchemeConfig
from docuready.report.redact import get_safe_logger

Tuple_Audit = Tuple[AuditResult, Dict[DocumentType, ExtractedDocument]]
logger = get_safe_logger("docuready.pipeline")


class AuditPipeline:
    def __init__(
        self,
        scheme_config: Optional[SchemeConfig] = None,
        audit_date: Optional[date] = None,
        as_of: Optional[date] = None,
        pack: Optional[Any] = None,
    ):
        if as_of is not None and audit_date is not None and as_of != audit_date:
            raise ValueError(
                f"Conflicting as_of ({as_of}) and audit_date ({audit_date}) provided"
            )
        env_as_of = os.environ.get("DOCUREADY_AS_OF")
        if as_of is not None or audit_date is not None:
            effective_as_of = as_of or audit_date
        elif env_as_of:
            effective_as_of = date.fromisoformat(env_as_of)
        else:
            effective_as_of = date.today()

        self.as_of = effective_as_of
        self.audit_date = effective_as_of
        self.pack = pack
        self.extractor = DocumentExtractor()
        self.validator = DocuReadyValidator(
            scheme_config=scheme_config,
            as_of=self.as_of,
        )

    def load_and_audit_packet(
        self,
        packet_dir: str,
        packet_id: Optional[str] = None,
        as_of: Optional[date] = None,
        audit_date: Optional[date] = None,
    ) -> Tuple_Audit:
        """
        Ingests all PDF documents in packet_dir, extracts fields with provenance,
        and executes the validation rules.
        """
        if as_of is not None and audit_date is not None and as_of != audit_date:
            raise ValueError(
                f"Conflicting as_of ({as_of}) and audit_date ({audit_date}) provided"
            )
        effective_as_of = as_of or audit_date or self.as_of
        t0 = time.perf_counter()
        pid = packet_id or os.path.basename(packet_dir)
        logger.info("Starting audit for packet_id=%s in directory=%s", pid, os.path.basename(packet_dir))

        # Expected canonical filename stems or auto-detect
        stem_mapping = {
            "income_cert": DocumentType.INCOME_CERT,
            "caste_cert": DocumentType.CASTE_CERT,
            "residence_cert": DocumentType.RESIDENCE_CERT,
            "marksheet": DocumentType.MARKSHEET,
            "bank_passbook": DocumentType.BANK_PASSBOOK,
            "application_form": DocumentType.APPLICATION_FORM,
            "aadhaar": DocumentType.AADHAAR,
        }

        extracted_docs: Dict[DocumentType, ExtractedDocument] = {}

        if os.path.exists(packet_dir):
            for file_name in os.listdir(packet_dir):
                stem, ext = os.path.splitext(file_name.lower())
                if ext in (".pdf", ".png", ".jpg"):
                    file_path = os.path.join(packet_dir, file_name)
                    expected_type = stem_mapping.get(stem)
                    slot_langs = get_slot_ocr_langs(self.pack, expected_type)
                    extracted = self.extractor.extract_document(
                        file_path, expected_type=expected_type, ocr_langs=slot_langs
                    )
                    target_slot = expected_type or extracted.doc_type
                    extracted_docs[target_slot] = extracted

        # Run validation
        logger.info("Extracted %d documents for packet %s", len(extracted_docs), pid)
        generation_ts = datetime.now().isoformat()
        audit_result = self.validator.validate_packet(
            pid, extracted_docs, as_of=effective_as_of, timestamp=generation_ts
        )
        t1 = time.perf_counter()
        audit_result.execution_time_ms = round((t1 - t0) * 1000.0, 3)
        logger.info(
            "Audit completed for packet %s: status=%s score=%s",
            pid,
            audit_result.overall_status,
            audit_result.readiness_score,
        )

        return audit_result, extracted_docs

    def replace_document_and_reaudit(
        self,
        current_docs: Dict[DocumentType, ExtractedDocument],
        replacement_file_path: str,
        doc_type: DocumentType,
        packet_id: str = "REPLACED_PACKET",
        as_of: Optional[date] = None,
        audit_date: Optional[date] = None,
    ) -> Tuple_Audit:
        """
        Replaces a specific document in current_docs with replacement_file_path and reruns the audit.
        """
        if as_of is not None and audit_date is not None and as_of != audit_date:
            raise ValueError(
                f"Conflicting as_of ({as_of}) and audit_date ({audit_date}) provided"
            )
        effective_as_of = as_of or audit_date or self.as_of
        t0 = time.perf_counter()
        new_docs = dict(current_docs)
        slot_langs = get_slot_ocr_langs(self.pack, doc_type)
        new_doc = self.extractor.extract_document(
            replacement_file_path, expected_type=doc_type, ocr_langs=slot_langs
        )
        new_docs[doc_type] = new_doc

        generation_ts = datetime.now().isoformat()
        audit_result = self.validator.validate_packet(
            packet_id, new_docs, as_of=effective_as_of, timestamp=generation_ts
        )
        t1 = time.perf_counter()
        audit_result.execution_time_ms = round((t1 - t0) * 1000.0, 3)

        return audit_result, new_docs


Tuple_Audit = tuple[AuditResult, Dict[DocumentType, ExtractedDocument]]
