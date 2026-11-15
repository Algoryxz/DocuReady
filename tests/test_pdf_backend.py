"""Tests for the pluggable PDF backend subsystem (Task T1.3 / ADR-001)."""

from __future__ import annotations

import pathlib
import pytest
import PIL.Image

from docuready.ingest.pdf_backend import (
    PDFDocumentBackend,
    PDFPageBackend,
    PyMuPDFDocumentBackend,
    get_pdf_backend,
)

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SAMPLE_PDF = _REPO_ROOT / "synthetic_data" / "pkt_01_clean" / "application_form.pdf"


def test_factory_returns_pymupdf_by_default():
    """Verify that get_pdf_backend defaults to PyMuPDF backend."""
    assert _SAMPLE_PDF.is_file(), f"Sample PDF missing: {_SAMPLE_PDF}"
    with get_pdf_backend(str(_SAMPLE_PDF)) as doc:
        assert isinstance(doc, PyMuPDFDocumentBackend)
        assert isinstance(doc, PDFDocumentBackend)
        assert doc.page_count >= 1
        assert len(doc) == doc.page_count


def test_pymupdf_page_backend_contract():
    """Verify that PyMuPDF page backend fulfills the PDFPageBackend interface contract."""
    with get_pdf_backend(str(_SAMPLE_PDF)) as doc:
        page = doc[0]
        assert isinstance(page, PDFPageBackend)
        assert page.page_number == 0

        # Geometry & Dimensions
        rect = page.rect
        assert len(rect) == 4
        assert rect[2] > rect[0]
        assert rect[3] > rect[1]
        assert page.width > 0
        assert page.height > 0

        # Text extraction
        text = page.get_text()
        assert isinstance(text, str)
        assert len(text) > 0

        # Word bounding boxes
        words = page.get_words()
        assert isinstance(words, list)
        assert len(words) > 0
        # Each word should be (x0, y0, x1, y1, word_str, block, line, word_idx)
        first_word = words[0]
        assert len(first_word) == 8
        assert isinstance(first_word[4], str)

        # Image rendering
        img = page.render_to_image(dpi=150)
        assert isinstance(img, PIL.Image.Image)
        assert img.width > 0
        assert img.height > 0


def test_pdf_backend_iteration_and_indexing():
    """Verify page indexing and iterator behaviors."""
    with get_pdf_backend(str(_SAMPLE_PDF)) as doc:
        pages = list(doc)
        assert len(pages) == doc.page_count

        with pytest.raises(IndexError):
            _ = doc[9999]


def test_factory_rejects_unsupported_backend():
    """Verify that requesting an unknown backend raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported PDF backend 'unsupported_engine'"):
        _ = get_pdf_backend(str(_SAMPLE_PDF), backend_name="unsupported_engine")


def test_pdfium_backend_import_handling():
    """Verify that attempting to use pdfium raises informative error or instantiates cleanly."""
    try:
        doc = get_pdf_backend(str(_SAMPLE_PDF), backend_name="pdfium")
        doc.close()
    except ImportError as e:
        assert "pypdfium2 is not installed" in str(e)


def test_pdfium_page_backend_get_words_raises_not_implemented():
    """Verify that PdfiumPageBackend.get_words explicitly raises NotImplementedError instead of returning fake coordinates."""
    from unittest.mock import MagicMock
    from docuready.ingest.pdf_backend import pdfium_backend

    # Temporarily bypass import check to test class contract
    orig_available = pdfium_backend._PYPDFIUM2_AVAILABLE
    pdfium_backend._PYPDFIUM2_AVAILABLE = True
    try:
        mock_page = MagicMock()
        mock_page.get_size.return_value = (595.0, 842.0)
        page = pdfium_backend.PdfiumPageBackend(mock_page, 0)
        with pytest.raises(NotImplementedError, match="Word-level bounding box provenance"):
            page.get_words()
    finally:
        pdfium_backend._PYPDFIUM2_AVAILABLE = orig_available
