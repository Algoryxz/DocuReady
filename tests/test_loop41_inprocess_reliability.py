"""Loop 41 — In-process OCR probe reliability, concurrency, and failure-safety tests."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image
import pytesseract

from docuready.ingest.adaptive_ocr import (
    _InProcessScriptProbe,
    _PROBE_ENGINE,
    profile_document,
)

DOC_ENG = Path("research/loop18/corpus/DOC_CTRL_01_ENGLISH_CERTIFICATE.png")


def test_profile_document_handles_tiny_and_blank_images_safely():
    blank = Image.new("RGB", (300, 300), "white")
    tiny = Image.new("RGB", (1, 1), "black")
    p_blank = profile_document(blank)
    p_tiny = profile_document(tiny)
    assert p_blank.is_unreadable is True
    assert p_tiny.is_unreadable is True


def test_inprocess_probe_concurrent_determinism():
    if not DOC_ENG.exists():
        return
    img = Image.open(DOC_ENG).convert("RGB")
    w, h = img.size
    strip = img.crop((int(w * 0.15), int(h * 0.25), int(w * 0.85), int(h * 0.45)))
    scale = min(1.0, 350.0 / max(strip.size))
    thumb = strip.resize((max(10, int(strip.width * scale)), max(10, int(strip.height * scale))))

    baseline = _PROBE_ENGINE.recognize_gray(thumb)
    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(lambda _: _PROBE_ENGINE.recognize_gray(thumb), range(8)))
    assert all(r == baseline for r in results)


def test_inprocess_probe_fallback_parity_and_unavailable():
    if not DOC_ENG.exists():
        return
    img = Image.open(DOC_ENG).convert("RGB")
    w, h = img.size
    strip = img.crop((int(w * 0.15), int(h * 0.25), int(w * 0.85), int(h * 0.45)))
    scale = min(1.0, 350.0 / max(strip.size))
    thumb = strip.resize((max(10, int(strip.width * scale)), max(10, int(strip.height * scale))))

    in_txt = (_PROBE_ENGINE.recognize_gray(thumb) or "").strip()
    fb_txt = (pytesseract.image_to_string(thumb, lang="eng+hin+ori", config="--psm 6", timeout=8) or "").strip()
    assert in_txt == fb_txt

    probe = _InProcessScriptProbe()
    probe._unavailable = True
    assert probe.recognize_gray(thumb) is None


def test_inprocess_probe_diagnostics_on_missing_binary(monkeypatch):
    probe = _InProcessScriptProbe()
    monkeypatch.setattr(
        "docuready.ingest.adaptive_ocr.find_tesseract_binary_with_source",
        lambda: (None, "none"),
    )
    assert probe._ensure_lib() is False
    assert probe._unavailable is True
    assert probe._init_error == "tesseract_binary_not_found"


def test_inprocess_probe_ensure_lib_does_not_raise_name_error(monkeypatch):
    probe = _InProcessScriptProbe()
    monkeypatch.setattr(
        "docuready.ingest.adaptive_ocr.find_tesseract_binary_with_source",
        lambda: ("/nonexistent/bin/tesseract", "mock"),
    )
    assert probe._ensure_lib() is False
    assert probe._unavailable is True
    assert probe._init_error is not None
    assert probe._init_error.startswith("libtesseract_not_found:")
