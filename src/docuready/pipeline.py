"""
End-to-End Audit & Document Ingestion Pipeline for DocuReady MVP
Connects file ingestion, field extraction, validation, and document replacement.
"""

from __future__ import annotations
import os
import time
from typing import Dict, List, Optional, Tuple
from docuready.domain.models import (
    DocumentType, ExtractedDocument, AuditResult, FindingStatus
)
from docuready.ingest.extractor import DocumentExtractor, detect_document_type
from docuready.rules.validator import DocuReadyValidator, SchemeConfig

Tuple_Audit = Tuple[AuditResult, Dict[DocumentType, ExtractedDocument]]


class AuditPipeline:
    def __init__(self, scheme_config: Optional[SchemeConfig] = None):
        self.extractor = DocumentExtractor()
        self.validator = DocuReadyValidator(scheme_config=scheme_config)

    def load_and_audit_packet(self, packet_dir: str, packet_id: Optional[str] = None) -> Tuple_Audit:
        """
        Ingests all PDF documents in packet_dir, extracts fields with provenance,
        and executes the validation rules.
        """
        t0 = time.perf_counter()
        pid = packet_id or os.path.basename(packet_dir)

        # Expected filenames or auto-detect
        type_mapping = {
            "income_cert.pdf": DocumentType.INCOME_CERT,
            "caste_cert.pdf": DocumentType.CASTE_CERT,
            "residence_cert.pdf": DocumentType.RESIDENCE_CERT,
            "marksheet.pdf": DocumentType.MARKSHEET,
            "bank_passbook.pdf": DocumentType.BANK_PASSBOOK,
            "application_form.pdf": DocumentType.APPLICATION_FORM,
            "aadhaar.pdf": DocumentType.AADHAAR
        }

        extracted_docs: Dict[DocumentType, ExtractedDocument] = {}

        if os.path.exists(packet_dir):
            for file_name in os.listdir(packet_dir):
                if file_name.lower().endswith(".pdf") or file_name.lower().endswith(".png") or file_name.lower().endswith(".jpg"):
                    file_path = os.path.join(packet_dir, file_name)
                    expected_type = type_mapping.get(file_name.lower())
                    extracted = self.extractor.extract_document(file_path, expected_type=expected_type)
                    extracted_docs[extracted.doc_type] = extracted

        # Run validation
        audit_result = self.validator.validate_packet(pid, extracted_docs)
        t1 = time.perf_counter()
        audit_result.execution_time_ms = round((t1 - t0) * 1000.0, 3)

        return audit_result, extracted_docs

    def replace_document_and_reaudit(
        self,
        current_docs: Dict[DocumentType, ExtractedDocument],
        replacement_file_path: str,
        doc_type: DocumentType,
        packet_id: str = "REPLACED_PACKET"
    ) -> Tuple_Audit:
        """
        Replaces a specific document in current_docs with replacement_file_path and reruns the audit.
        """
        t0 = time.perf_counter()
        new_docs = dict(current_docs)
        new_doc = self.extractor.extract_document(replacement_file_path, expected_type=doc_type)
        new_docs[doc_type] = new_doc

        audit_result = self.validator.validate_packet(packet_id, new_docs)
        t1 = time.perf_counter()
        audit_result.execution_time_ms = round((t1 - t0) * 1000.0, 3)

        return audit_result, new_docs


Tuple_Audit = tuple[AuditResult, Dict[DocumentType, ExtractedDocument]]
