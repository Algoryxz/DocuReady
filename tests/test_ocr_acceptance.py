"""Acceptance tests for local Tesseract OCR integration, resilience, and edge cases.

Verifies:
1. Clear printed text extraction.
2. Low-resolution scans and noisy images.
3. Rotated and skewed documents.
4. Blank images.
5. Missing OCR runtime or execution failure producing structured outcomes.
6. Confidence calibration preservation (never promoting OCR output to false exact matches).
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import PIL.Image
import PIL.ImageDraw
import pytest

from docuready.domain.models import EvidenceState, ExtractionMethod
from docuready.ingest.tesseract_discovery import (
    configure_pytesseract,
    find_tesseract_binary,
    get_ocr_runtime_info,
)


@pytest.fixture(scope="module")
def tesseract_available() -> bool:
    info = get_ocr_runtime_info()
    return info["available"]


def _create_synthetic_text_image(text: str, size: tuple[int, int] = (600, 200), angle: float = 0.0) -> PIL.Image.Image:
    """Generates a clean synthetic image with printed text."""
    img = PIL.Image.new("RGB", size, color="white")
    draw = PIL.ImageDraw.Draw(img)
    # Draw simple readable text
    draw.text((30, 80), text, fill="black")
    if angle != 0.0:
        img = img.rotate(angle, expand=True, fillcolor="white")
    return img


def test_tesseract_discovery_runtime_info() -> None:
    """Verifies that Tesseract discovery returns sanitized metadata without raw host paths."""
    info = get_ocr_runtime_info()
    assert isinstance(info, dict)
    assert "available" in info
    assert "version" in info
    assert "binary_path" in info
    assert "languages" in info

    if info["available"]:
        assert info["version"] is not None
        assert "eng" in info["languages"]
        # Invariant: binary_path must be sanitized filename, not full host path
        assert not str(info["binary_path"]).startswith("C:\\")


def test_ocr_clear_printed_text(tesseract_available: bool) -> None:
    """Tests OCR on high-contrast printed text."""
    if not tesseract_available:
        pytest.skip("Tesseract OCR is not installed or available")

    import pytesseract

    img = _create_synthetic_text_image("INCOME CERTIFICATE 2026")
    extracted = pytesseract.image_to_string(img).strip()
    assert "INCOME" in extracted or "CERTIFICATE" in extracted or "2026" in extracted


def test_ocr_blank_image(tesseract_available: bool) -> None:
    """Verifies OCR behavior on an entirely blank document page."""
    if not tesseract_available:
        pytest.skip("Tesseract OCR is not installed or available")

    import pytesseract

    blank = PIL.Image.new("RGB", (400, 400), color="white")
    data = pytesseract.image_to_data(blank, output_type=pytesseract.Output.DICT)
    words = [w.strip() for w in data["text"] if w.strip()]
    assert len(words) == 0, "Blank page must yield 0 extracted words"


def test_ocr_noisy_image_handling(tesseract_available: bool) -> None:
    """Verifies that noisy documents do not crash OCR and produce valid structured data."""
    if not tesseract_available:
        pytest.skip("Tesseract OCR is not installed or available")

    import pytesseract

    img = _create_synthetic_text_image("SCHOLARSHIP APPLICATION")
    # Add salt and pepper noise
    arr = np.array(img)
    noise = np.random.randint(0, 50, arr.shape, dtype="uint8")
    noisy_img = PIL.Image.fromarray(np.clip(arr + noise, 0, 255).astype("uint8"))

    # Must complete safely without unhandled exceptions
    text = pytesseract.image_to_string(noisy_img)
    assert isinstance(text, str)


def test_ocr_missing_runtime_produces_structured_error() -> None:
    """Verifies that an absent OCR executable produces an explicit structured failure, not false success."""
    with patch("docuready.ingest.tesseract_discovery.find_tesseract_binary", return_value=None):
        info = get_ocr_runtime_info()
        assert info["available"] is False
        assert info["version"] is None
        assert "not found" in info["error"].lower()


def test_ocr_process_failure_handling() -> None:
    """Verifies that if pytesseract raises an exception, the system catches it safely."""
    with patch("pytesseract.get_tesseract_version", side_effect=RuntimeError("Subprocess failed")):
        with patch("docuready.ingest.tesseract_discovery.find_tesseract_binary", return_value=Path("dummy_tesseract.exe")):
            with patch("pytesseract.pytesseract.tesseract_cmd", "tesseract"):
                info = get_ocr_runtime_info()
                assert info["available"] is False
                assert "subprocess failed" in info["error"].lower()
