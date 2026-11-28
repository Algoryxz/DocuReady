"""Loop 41 — In-process OCR probe reliability, concurrency, and failure-safety tests."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image
import pytest
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
    from pathlib import Path

    probe = _InProcessScriptProbe()
    monkeypatch.setattr(
        "docuready.ingest.adaptive_ocr.find_tesseract_binary_with_source",
        lambda: (Path("/nonexistent/bin/tesseract"), "mock"),
    )
    monkeypatch.setattr(
        "docuready.ingest.adaptive_ocr.ctypes.CDLL",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("mock missing libtesseract")),
    )
    assert probe._ensure_lib() is False
    assert probe._unavailable is True
    assert probe._init_error is not None
    assert probe._init_error.startswith("libtesseract_not_found:")


def test_inprocess_probe_rejects_incomplete_traineddata(tmp_path: Path, monkeypatch):
    """Probe must refuse to operate as English-only when hin or ori models are missing."""
    import ctypes

    fake_bin = tmp_path / "bin" / "tesseract"
    fake_bin.parent.mkdir(parents=True)
    fake_bin.write_text("", encoding="utf-8")
    (fake_bin.parent / "libtesseract-5.dll").write_bytes(b"")
    (fake_bin.parent / "libtesseract.so.5").write_bytes(b"")

    class _FakeLib:
        class _Fn:
            restype = None
            argtypes = None
        TessBaseAPICreate = _Fn()
        TessBaseAPIDelete = _Fn()
        TessBaseAPIInit3 = _Fn()
        TessBaseAPISetPageSegMode = _Fn()
        TessBaseAPISetImage = _Fn()
        TessBaseAPIGetUTF8Text = _Fn()
        TessDeleteText = _Fn()

    for missing_set, expected_missing in [
        (("eng",), "hin"),
        (("eng", "hin"), "ori"),
        (("eng", "ori"), "hin"),
    ]:
        td = tmp_path / f"td_{'_'.join(missing_set)}"
        td.mkdir()
        for lang in missing_set:
            (td / f"{lang}.traineddata").write_bytes(b"fake-model-data")

        probe = _InProcessScriptProbe()
        monkeypatch.setattr(
            "docuready.ingest.adaptive_ocr.find_tesseract_binary_with_source",
            lambda: (fake_bin, "mock"),
        )
        monkeypatch.setattr(
            "docuready.ingest.adaptive_ocr.ctypes.CDLL",
            lambda *_a, **_kw: _FakeLib(),
        )
        monkeypatch.setattr(
            "docuready.ingest.adaptive_ocr.get_unified_tessdata_dir",
            lambda _p, td=td: td,
        )
        assert probe._ensure_lib() is False
        assert probe._unavailable is True
        assert probe._init_error is not None
        assert "missing_traineddata" in probe._init_error
        assert expected_missing in probe._init_error


def test_inprocess_probe_rejects_missing_secondary_loaded_language(tmp_path: Path, monkeypatch):
    """Even if TessBaseAPIInit3 returns 0, missing secondary loaded language must disable probe."""
    import ctypes

    fake_bin = tmp_path / "bin" / "tesseract"
    fake_bin.parent.mkdir(parents=True)
    fake_bin.write_text("", encoding="utf-8")
    (fake_bin.parent / "libtesseract-5.dll").write_bytes(b"")
    (fake_bin.parent / "libtesseract.so.5").write_bytes(b"")
    td = tmp_path / "tessdata"
    td.mkdir()
    for lang in ("eng", "hin", "ori"):
        (td / f"{lang}.traineddata").write_bytes(b"fake-model-data")

    deleted_apis = []

    class _FakeLib:
        class _Fn:
            restype = None
            argtypes = None
        TessBaseAPICreate = staticmethod(lambda: 12345)
        TessBaseAPIDelete = staticmethod(lambda api: deleted_apis.append(api))
        TessBaseAPIInit3 = staticmethod(lambda _api, _td, _lang: 0)
        TessBaseAPISetPageSegMode = _Fn()
        TessBaseAPISetImage = _Fn()
        TessBaseAPIGetUTF8Text = _Fn()
        TessDeleteText = _Fn()

        @staticmethod
        def TessBaseAPIGetLoadedLanguagesAsVector(_api):
            arr = (ctypes.c_char_p * 3)(b"eng", b"hin", None)
            return arr

    probe = _InProcessScriptProbe()
    monkeypatch.setattr(
        "docuready.ingest.adaptive_ocr.find_tesseract_binary_with_source",
        lambda: (fake_bin, "mock"),
    )
    monkeypatch.setattr(
        "docuready.ingest.adaptive_ocr.ctypes.CDLL",
        lambda *_a, **_kw: _FakeLib(),
    )
    monkeypatch.setattr(
        "docuready.ingest.adaptive_ocr.get_unified_tessdata_dir",
        lambda _p: td,
    )

    assert probe._get_api("eng+hin+ori", 6) is None
    assert probe._unavailable is True
    assert probe._init_error is not None
    assert "tessbaseapi_missing_loaded_langs" in probe._init_error
    assert "ori" in probe._init_error
    assert deleted_apis == [12345]


def test_inprocess_probe_handles_missing_c_api_symbol_and_surfaces_name_error(tmp_path: Path, monkeypatch):
    """Missing C API symbol marks probe unavailable; programming NameError still surfaces."""
    fake_bin = tmp_path / "bin" / "tesseract"
    fake_bin.parent.mkdir(parents=True)
    fake_bin.write_text("", encoding="utf-8")
    (fake_bin.parent / "libtesseract-5.dll").write_bytes(b"")
    (fake_bin.parent / "libtesseract.so.5").write_bytes(b"")
    td = tmp_path / "tessdata"
    td.mkdir()
    for lang in ("eng", "hin", "ori"):
        (td / f"{lang}.traineddata").write_bytes(b"fake-model-data")

    class _IncompleteLib:
        class _Fn:
            restype = None
            argtypes = None
        TessBaseAPICreate = _Fn()
        TessBaseAPIDelete = _Fn()
        TessBaseAPIInit3 = _Fn()
        TessBaseAPISetPageSegMode = _Fn()
        TessBaseAPISetImage = _Fn()
        # Missing TessBaseAPIGetUTF8Text intentionally
        TessDeleteText = _Fn()

    probe = _InProcessScriptProbe()
    monkeypatch.setattr(
        "docuready.ingest.adaptive_ocr.find_tesseract_binary_with_source",
        lambda: (fake_bin, "mock"),
    )
    monkeypatch.setattr(
        "docuready.ingest.adaptive_ocr.ctypes.CDLL",
        lambda *_a, **_kw: _IncompleteLib(),
    )
    monkeypatch.setattr(
        "docuready.ingest.adaptive_ocr.get_unified_tessdata_dir",
        lambda _p: td,
    )

    assert probe._ensure_lib() is False
    assert probe._unavailable is True
    assert probe._init_error is not None
    assert "missing_c_api_symbol" in probe._init_error
    assert "TessBaseAPIGetUTF8Text" in probe._init_error

    # Verify programming errors are not swallowed
    probe2 = _InProcessScriptProbe()
    monkeypatch.setattr(
        "docuready.ingest.adaptive_ocr.find_tesseract_binary_with_source",
        lambda: (_ for _ in ()).throw(NameError("simulated_bug")),
    )
    with pytest.raises(NameError, match="simulated_bug"):
        probe2._ensure_lib()


def test_indic_fallback_still_classifies_indic_when_inprocess_unavailable(monkeypatch):
    """When in-process probe is unavailable, _probe_band must call it, get None, and classify Indic via fallback."""
    from docuready.ingest import adaptive_ocr

    fake_probe = _InProcessScriptProbe()
    fake_probe._unavailable = True

    probe_calls = []
    probe_returns = []
    orig_recognize_gray = fake_probe.recognize_gray

    def _spy_recognize_gray(thumb):
        probe_calls.append(thumb)
        res = orig_recognize_gray(thumb)
        probe_returns.append(res)
        return res

    fake_probe.recognize_gray = _spy_recognize_gray  # type: ignore[method-assign]

    fallback_calls = []

    def _fallback_stub(*args, **kwargs):
        fallback_calls.append((args, kwargs))
        return "ପ୍ରମାଣ ପତ୍ର ଓଡ଼ିଶା ସରକାର"

    monkeypatch.setattr(adaptive_ocr, "_PROBE_ENGINE", fake_probe)
    monkeypatch.setattr(adaptive_ocr.pytesseract, "image_to_string", _fallback_stub)
    monkeypatch.setattr(adaptive_ocr, "_ORIG_PYTESSERACT_IMAGE_TO_STRING", _fallback_stub)

    img = Image.new("RGB", (600, 800), "white")
    # Draw non-blank ink so ink ratio >= 0.003
    from PIL import ImageDraw
    ImageDraw.Draw(img).rectangle((100, 200, 500, 400), fill="black")

    prof = profile_document(img)
    dec = adaptive_ocr.select_ocr_strategy(prof)
    assert len(probe_calls) >= 1
    assert all(r is None for r in probe_returns)
    assert len(fallback_calls) >= 1
    assert prof.primary_script != "LATIN"
    assert dec.selected_strategy != "FAST_PATH_ENG"
