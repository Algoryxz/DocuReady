"""
Loop 39 Adversarial Tests for OCR Probe Hardening & Safe Routing.
Verifies:
1. Probe timeouts never silently classify a document as LATIN / FAST_PATH_ENG.
2. Probe exceptions remain observable via profile.probe_error and profile.probe_uncertain.
3. Empty/sparse probe text on an inked page safely falls back to eng+hin+ori.
4. Blank/unreadable pages still abstain via ABSTAIN_UNREADABLE.
"""

from PIL import Image, ImageDraw
import pytesseract

from docuready.ingest.adaptive_ocr import (
    DocumentProfile,
    profile_document,
    select_ocr_strategy,
)


def _make_inked_image() -> Image.Image:
    img = Image.new("RGB", (400, 300), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([40, 60, 360, 220], fill="black")
    return img


def test_probe_timeout_never_routes_to_english_only(monkeypatch):
    def fake_timeout(*args, **kwargs):
        raise RuntimeError("Tesseract process timeout")

    monkeypatch.setattr(pytesseract, "image_to_string", fake_timeout)
    img = _make_inked_image()
    profile = profile_document(img)

    assert profile.probe_uncertain is True
    assert profile.probe_error is not None and "RuntimeError" in profile.probe_error
    assert profile.primary_script == "UNKNOWN"

    decision = select_ocr_strategy(profile)
    assert decision.selected_strategy == "GLOBAL_MULTILINGUAL"
    assert decision.selected_lang == "eng+hin+ori"
    assert decision.selected_strategy != "FAST_PATH_ENG"


def test_sparse_probe_output_routes_to_multilingual_fallback(monkeypatch):
    monkeypatch.setattr(pytesseract, "image_to_string", lambda *a, **kw: "ab")
    img = _make_inked_image()
    profile = profile_document(img)

    assert profile.probe_uncertain is True
    decision = select_ocr_strategy(profile)
    assert decision.selected_strategy == "GLOBAL_MULTILINGUAL"
    assert decision.selected_lang == "eng+hin+ori"


def test_blank_image_still_abstains():
    blank = Image.new("RGB", (400, 300), "white")
    profile = profile_document(blank)
    assert profile.is_unreadable is True
    decision = select_ocr_strategy(profile)
    assert decision.selected_strategy == "ABSTAIN_UNREADABLE"
    assert decision.ocr_model_invocations == 0
