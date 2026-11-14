"""Document ingestion and extraction subsystem."""

from docuready.ingest.extractor import DocumentExtractor, detect_document_type

__all__ = ["DocumentExtractor", "detect_document_type"]
