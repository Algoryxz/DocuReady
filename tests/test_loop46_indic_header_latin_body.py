"""
Loop 46 — Indic Header + Latin Body Recovery & Negative-Control Tests
======================================================================
Verifies Strategy C: when central (0.25..0.45) AND lower (0.52..0.85) are
both Latin-only, upper band (0.05..0.22, max_dim=500, ink >= 0.003) is probed
with >= 6 Indic codepoint guard, recovering Indic-header + Latin-body docs
without creating false positives on English-only negative controls.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from docuready.ingest.adaptive_ocr import profile_document, select_ocr_strategy

W, H = 1200, 1600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

def _load_latin_font(size: int) -> ImageFont.ImageFont:
    for cand in (
        "arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ):
        try:
            return ImageFont.truetype(cand, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


FONT = _load_latin_font(34)


def _paste_crop(img: Image.Image, crop: Image.Image, y0_f: float, y1_f: float) -> None:
    r = crop.resize((int(W * 0.85), int(H * (y1_f - y0_f))), Image.Resampling.BILINEAR)
    img.paste(r, (int(W * 0.075), int(H * y0_f)))


class TestIndicHeaderLatinBodyRecovery:
    """Loop 46 positive recovery tests (real raster OCR, no native_text shortcut)."""

    def test_devanagari_header_full_latin_body_routes_multilingual(self):
        hin_corpus = Path(__file__).resolve().parents[1] / "research" / "loop14" / "corpus" / "DOC_HIN_01_ADMIN_CIRCULAR.png"
        if not hin_corpus.exists():
            pytest.skip("DOC_HIN_01 corpus missing")
        src = Image.open(hin_corpus).convert("RGB")
        hw, hh = src.size
        crop = src.crop((int(hw * 0.05), int(hh * 0.12), int(hw * 0.95), int(hh * 0.34)))

        page = Image.new("RGB", (W, H), WHITE)
        _paste_crop(page, crop, 0.05, 0.21)
        dr = ImageDraw.Draw(page)
        for i in range(8):
            dr.text((216, 448 + i * 70), f"Clause {i+1}: Official English administrative record text.", fill=BLACK, font=FONT)

        prof = profile_document(page)
        dec = select_ocr_strategy(prof)
        assert dec.selected_strategy == "GLOBAL_MULTILINGUAL"
        assert "hin" in dec.selected_lang

    def test_odia_header_full_latin_body_routes_multilingual(self):
        ori_corpus = Path(__file__).resolve().parents[1] / "research" / "loop18" / "corpus" / "DOC_EXT_06_ODIA_REVENUE_NOTICE.png"
        if not ori_corpus.exists():
            pytest.skip("DOC_EXT_06 corpus missing")
        src = Image.open(ori_corpus).convert("RGB")
        ow, oh = src.size
        crop = src.crop((int(ow * 0.05), int(oh * 0.10), int(ow * 0.95), int(oh * 0.35)))

        page = Image.new("RGB", (W, H), WHITE)
        _paste_crop(page, crop, 0.05, 0.21)
        dr = ImageDraw.Draw(page)
        for i in range(8):
            dr.text((216, 448 + i * 70), f"Clause {i+1}: Official English administrative record text.", fill=BLACK, font=FONT)

        prof = profile_document(page)
        dec = select_ocr_strategy(prof)
        assert dec.selected_strategy == "GLOBAL_MULTILINGUAL"
        assert "ori" in dec.selected_lang


class TestExpandedNegativeControls:
    """English-only pages with blank upper band, seals, noise, crests must stay FAST_PATH_ENG."""

    def test_blank_upper_dense_latin_body_fast_path(self):
        page = Image.new("RGB", (W, H), WHITE)
        dr = ImageDraw.Draw(page)
        for i in range(10):
            dr.text((200, 420 + i * 75), f"Section {i+1}: Dense English legal clause 2026-0{i}.", fill=BLACK, font=FONT)
        prof = profile_document(page)
        dec = select_ocr_strategy(prof)
        assert dec.selected_strategy == "FAST_PATH_ENG"

    def test_circular_seal_and_crest_negative_control(self):
        page = Image.new("RGB", (W, H), WHITE)
        dr = ImageDraw.Draw(page)
        dr.ellipse((200, 100, 360, 260), outline=BLACK, width=5)
        dr.text((400, 140), "OFFICIAL SEAL OF AUTHORITY", fill=BLACK, font=FONT)
        for i in range(6):
            dr.text((200, 450 + i * 80), f"Record line {i+1}: Verified English text.", fill=BLACK, font=FONT)
        prof = profile_document(page)
        dec = select_ocr_strategy(prof)
        assert dec.selected_strategy == "FAST_PATH_ENG"

    def test_noisy_upper_band_english_body_fast_path(self):
        page = Image.new("RGB", (W, H), WHITE)
        rng = np.random.default_rng(46)
        arr = np.array(page)
        mask = rng.random((int(H * 0.20), int(W * 0.70))) < 0.015
        arr[int(H * 0.05):int(H * 0.25), int(W * 0.15):int(W * 0.85)][mask] = 0
        page = Image.fromarray(arr)
        dr = ImageDraw.Draw(page)
        for i in range(6):
            dr.text((200, 450 + i * 80), f"Receipt item {i+1}: USD 100.00", fill=BLACK, font=FONT)
        prof = profile_document(page)
        dec = select_ocr_strategy(prof)
        assert dec.selected_strategy == "FAST_PATH_ENG"
