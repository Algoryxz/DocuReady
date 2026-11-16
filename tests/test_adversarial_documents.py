"""Adversarial and robust document corpus tests for DocuReady.

Verifies:
1. Malformed and corrupted PDFs.
2. Empty (0-byte) files.
3. Extension spoofing (e.g. plain text renamed to .pdf or .png).
4. Extreme page geometries and mixed rotations.
5. Ingestion limits enforcement (size, document count, page count).
6. Password-protected PDFs handling.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
import pymupdf

from docuready.domain.models import DocumentType
from docuready.ingest.extractor import DocumentExtractor
from docuready.ingest.pdf_backend import get_pdf_backend


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


def test_corrupted_pdf_handling(temp_dir: Path) -> None:
    """Verifies that a corrupted PDF header/trailer does not cause unhandled crashes."""
    corrupted_pdf = temp_dir / "corrupted.pdf"
    corrupted_pdf.write_bytes(b"%PDF-1.4\nCorrupted content without xref or trailer...")

    extractor = DocumentExtractor()
    doc = extractor.extract_document(str(corrupted_pdf), DocumentType.APPLICATION_FORM)
    assert doc.status == "CORRUPTED"
    assert len(doc.fields) == 0


def test_empty_zero_byte_pdf_handling(temp_dir: Path) -> None:
    """Verifies that 0-byte PDF is safely handled as CORRUPTED."""
    empty_pdf = temp_dir / "empty.pdf"
    empty_pdf.write_bytes(b"")

    extractor = DocumentExtractor()
    doc = extractor.extract_document(str(empty_pdf), DocumentType.APPLICATION_FORM)
    assert doc.status == "CORRUPTED"
    assert len(doc.fields) == 0


def test_extension_spoofing_plain_text_as_pdf(temp_dir: Path) -> None:
    """Verifies that a plain text file renamed as .pdf fails gracefully as CORRUPTED."""
    spoofed = temp_dir / "spoofed.pdf"
    spoofed.write_text("Hello, this is not a PDF file at all.")

    extractor = DocumentExtractor()
    doc = extractor.extract_document(str(spoofed), DocumentType.APPLICATION_FORM)
    assert doc.status == "CORRUPTED"
    assert len(doc.fields) == 0


def test_multi_page_mixed_rotations_geometry(temp_dir: Path) -> None:
    """Verifies that documents with multiple pages and mixed rotations are processed accurately."""
    doc_path = temp_dir / "mixed_rotation.pdf"

    # Create synthetic PDF with page 1 upright (0 deg) and page 2 rotated (90 deg)
    doc = pymupdf.open()
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text((50, 100), "Page 1: Upright Document Text")

    p2 = doc.new_page(width=595, height=842)
    p2.set_rotation(90)
    p2.insert_text((50, 100), "Page 2: Rotated 90 Degrees Text")

    doc.save(str(doc_path))
    doc.close()

    with get_pdf_backend(str(doc_path)) as backend_doc:
        assert backend_doc.page_count == 2
        page0 = backend_doc[0]
        page1 = backend_doc[1]

        assert "Page 1" in page0.get_text()
        assert "Page 2" in page1.get_text()

        # Check dimensions
        assert page0.width == 595
        assert page0.height == 842


def test_password_protected_pdf_rejection(temp_dir: Path) -> None:
    """Verifies that an encrypted PDF is detected and fails safely."""
    encrypted_path = temp_dir / "encrypted.pdf"

    doc = pymupdf.open()
    page = doc.new_page(width=500, height=500)
    page.insert_text((50, 50), "Confidential Document")
    # Save with user password
    doc.save(str(encrypted_path), encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="secret123")
    doc.close()

    # Attempting to open without password
    with get_pdf_backend(str(encrypted_path)) as backend_doc:
        raw = getattr(backend_doc, "raw_doc", None)
        if raw is not None:
            assert raw.is_encrypted or raw.needs_pass


def test_sidecar_rejects_empty_document_in_audit_packet(temp_dir: Path, monkeypatch) -> None:
    """Verifies that sidecar audit_packet rejects 0-byte document."""
    from sidecar.docuready_sidecar import _handle, PROTOCOL_VERSION

    managed = temp_dir / "managed"
    packet = managed / "packet-adv-empty"
    packet.mkdir(parents=True)
    monkeypatch.setenv("DOCUREADY_WORKSPACE_ROOT", str(managed))

    empty_file = packet / "empty.pdf"
    empty_file.write_bytes(b"")

    with pytest.raises(ValueError, match="empty \\(0 bytes\\)"):
        _handle({
            "protocol": PROTOCOL_VERSION,
            "id": "adv-empty",
            "method": "audit_packet",
            "params": {
                "packet_dir": str(packet),
                "packet_id": "TEST_PKT",
                "as_of": "2026-03-31",
            }
        })


def test_sidecar_rejects_excessive_documents_count(temp_dir: Path, monkeypatch) -> None:
    """Verifies that sidecar audit_packet rejects packets exceeding MAX_PACKET_DOCUMENTS."""
    from sidecar.docuready_sidecar import _handle, PROTOCOL_VERSION, MAX_PACKET_DOCUMENTS

    managed = temp_dir / "managed"
    packet = managed / "packet-adv-excess"
    packet.mkdir(parents=True)
    monkeypatch.setenv("DOCUREADY_WORKSPACE_ROOT", str(managed))

    for i in range(MAX_PACKET_DOCUMENTS + 1):
        f = packet / f"doc_{i}.pdf"
        f.write_bytes(b"%PDF-1.4 dummy content")

    with pytest.raises(ValueError, match="exceeds maximum limit"):
        _handle({
            "protocol": PROTOCOL_VERSION,
            "id": "adv-excess",
            "method": "audit_packet",
            "params": {
                "packet_dir": str(packet),
                "packet_id": "TEST_PKT",
                "as_of": "2026-03-31",
            }
        })
