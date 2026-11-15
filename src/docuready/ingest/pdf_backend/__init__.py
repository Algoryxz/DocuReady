"""Pluggable PDF backend abstraction subsystem for DocuReady."""

from __future__ import annotations

import os
from typing import Optional

from docuready.ingest.pdf_backend.base import PDFDocumentBackend, PDFPageBackend
from docuready.ingest.pdf_backend.pymupdf_backend import (
    PyMuPDFDocumentBackend,
    PyMuPDFPageBackend,
)


def get_pdf_backend(file_path: str, backend_name: Optional[str] = None) -> PDFDocumentBackend:
    """Factory function to instantiate the configured PDF backend.

    Defaults to 'pymupdf' unless overridden via DOCUREADY_PDF_BACKEND environment variable
    or the backend_name parameter.
    """
    selected = (backend_name or os.environ.get("DOCUREADY_PDF_BACKEND", "pymupdf")).lower()

    if selected in ("pymupdf", "fitz", "default"):
        return PyMuPDFDocumentBackend(file_path)
    elif selected in ("pdfium", "pypdfium2"):
        from docuready.ingest.pdf_backend.pdfium_backend import PdfiumDocumentBackend

        return PdfiumDocumentBackend(file_path)
    else:
        raise ValueError(
            f"Unsupported PDF backend '{selected}'. Supported backends: 'pymupdf', 'pdfium'"
        )


__all__ = [
    "PDFDocumentBackend",
    "PDFPageBackend",
    "PyMuPDFDocumentBackend",
    "PyMuPDFPageBackend",
    "get_pdf_backend",
]
