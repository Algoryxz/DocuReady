"""
tests/test_ocr_integration.py

Integration tests verifying actual OCR execution and multi-lingual language
pack availability (eng, ori, hin) using Tesseract OCR.

Contract:
- Requires real Tesseract OCR execution; skips only when executed locally without Tesseract.
- In CI (CI=true or GITHUB_ACTIONS=true), missing Tesseract, missing language packs,
  or OCR extraction failures MUST cause the test to fail.
- All documents generated for testing are 100% synthetic raster images with no native vector text.
"""

import io
import os
import shutil
from typing import List, Optional

import pytest
import pymupdf
from PIL import Image, ImageDraw, ImageFont

from docuready.domain.models import DocumentType, ExtractionMethod
from docuready.ingest.extractor import DocumentExtractor


def is_ci_environment() -> bool:
    """Returns True if running in GitHub Actions or standard CI environment."""
    return (
        os.environ.get("CI", "").lower() in ("true", "1")
        or os.environ.get("GITHUB_ACTIONS", "").lower() in ("true", "1")
    )


def get_tesseract_command() -> Optional[str]:
    """Locates the Tesseract executable on PATH or via pytesseract configuration."""
    tess = shutil.which("tesseract")
    if tess:
        return tess
    try:
        import pytesseract

        cmd = pytesseract.pytesseract.tesseract_cmd
        if cmd and shutil.which(cmd):
            return cmd
    except Exception:
        pass
    return None


def require_tesseract() -> None:
    """Ensures Tesseract is present. Skips locally if absent, fails in CI."""
    tess = get_tesseract_command()
    if not tess:
        if is_ci_environment():
            pytest.fail(
                "Tesseract executable is not installed or not in PATH in CI. "
                "CI environment requires tesseract-ocr system package."
            )
        else:
            pytest.skip(
                "Tesseract executable is not installed on local host; skipping OCR integration test."
            )


def create_synthetic_raster_pdf(
    file_path: str,
    text_lines: List[str],
    image_width: int = 1200,
    image_height: int = 600,
) -> str:
    """
    Creates a synthetic PDF containing exclusively a raster image with high-contrast text.
    PyMuPDF native text extraction from this document will yield empty string.
    """
    img = Image.new("RGB", (image_width, image_height), color="white")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.load_default(size=32)
    except TypeError:
        font = ImageFont.load_default()

    y_offset = 60
    for line in text_lines:
        draw.text((60, y_offset), line, fill="black", font=font)
        y_offset += 60

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    doc = pymupdf.open()
    page = doc.new_page(width=image_width, height=image_height)
    page.insert_image(page.rect, stream=png_bytes)
    doc.save(file_path)
    doc.close()

    return file_path


def test_tesseract_language_packs_available():
    """
    Verifies that Tesseract is installed and that the required language resources
    ('eng', 'ori', 'hin') are present.
    """
    require_tesseract()

    import pytesseract

    try:
        available_langs = pytesseract.get_languages()
    except Exception as exc:
        if is_ci_environment():
            pytest.fail(f"Failed to query Tesseract languages via pytesseract in CI: {exc}")
        else:
            pytest.skip(f"Failed to query Tesseract languages locally: {exc}")

    missing_langs = [lang for lang in ["eng", "ori", "hin"] if lang not in available_langs]

    if missing_langs:
        msg = f"Required Tesseract language pack(s) missing: {missing_langs}. Available: {available_langs}"
        if is_ci_environment():
            pytest.fail(msg)
        else:
            pytest.skip(msg)

    assert "eng" in available_langs
    assert "ori" in available_langs
    assert "hin" in available_langs


def test_ocr_integration_extracts_raster_text(tmp_path):
    """
    Validates genuine OCR execution through DocumentExtractor.extract_document:
    1. Generates an image-only PDF with zero native vector text.
    2. Exercises DocumentExtractor's fallback to real LOCAL_OCR.
    3. Confirms extraction method is LOCAL_OCR.
    4. Confirms non-empty recognized raw text and mean OCR confidence > 0.
    5. Confirms known synthetic token is present in recognized output.
    6. Confirms document status is VALID (not UNREADABLE).
    """
    require_tesseract()

    distinct_token = "VERIFY_TOKEN_98231"
    text_lines = [
        "GOVERNMENT OF ODISHA",
        "SYNTHETIC RESIDENCE CERTIFICATE",
        f"CERTIFICATE IDENTIFIER: {distinct_token}",
        "APPLICANT: SYNTHETIC CITIZEN",
        "DATE OF ISSUANCE: 14/11/2026",
    ]

    pdf_path = str(tmp_path / "synthetic_raster_doc.pdf")
    create_synthetic_raster_pdf(pdf_path, text_lines)

    # 1. Assert the PDF has strictly NO native vector text
    pre_doc = pymupdf.open(pdf_path)
    pre_text = "".join(p.get_text() for p in pre_doc)
    pre_doc.close()
    assert pre_text.strip() == "", "Precondition violated: synthetic PDF must contain no native text"

    # 2. Extract using real DocumentExtractor
    extractor = DocumentExtractor()
    extracted = extractor.extract_document(pdf_path, expected_type=DocumentType.RESIDENCE_CERT)

    # 3. Assert extraction route and results
    assert extracted.extraction_method == ExtractionMethod.LOCAL_OCR.value, (
        f"Expected LOCAL_OCR extraction method, got {extracted.extraction_method}"
    )
    assert extracted.raw_text and len(extracted.raw_text.strip()) > 0, "OCR raw_text must not be empty"
    assert extracted.status != "UNREADABLE", (
        f"Document was unexpectedly classified as UNREADABLE: raw_text='{extracted.raw_text}'"
    )
    assert extracted.status == "VALID", f"Expected VALID status, got {extracted.status}"

    # 4. Assert distinct synthetic token was recognized by OCR
    cleaned_ocr_text = extracted.raw_text.upper().replace(" ", "").replace("-", "")
    expected_token_cleaned = distinct_token.upper().replace(" ", "").replace("-", "")
    assert expected_token_cleaned in cleaned_ocr_text, (
        f"Token '{distinct_token}' was not recognized in OCR output:\n{extracted.raw_text}"
    )

    # 5. Assert OCR confidence is recorded
    assert extracted.mean_ocr_confidence is not None
    assert extracted.mean_ocr_confidence > 0.0
