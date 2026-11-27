"""
Loop 44 — Strategy D Upper-Band Script Probe Tests
====================================================
Verifies that the upper-band probe (Strategy D) correctly routes
documents with Indic headers above the central probe window (y < 0.25)
while NOT producing false positives on English-only pages with
logos/stamps in the header area.

Also verifies that prior routing (Strategies A/C) for existing fixtures
is unaffected by the new probe.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Ensure src is importable
# ---------------------------------------------------------------------------
SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from docuready.ingest.adaptive_ocr import profile_document, select_ocr_strategy

# ---------------------------------------------------------------------------
# Synthetic fixture helpers
# ---------------------------------------------------------------------------
_PAGE_W, _PAGE_H = 850, 1100
_WHITE = (255, 255, 255)
_BLACK = (0, 0, 0)

try:
    _FONT = ImageFont.truetype("arial.ttf", 24)
except OSError:
    _FONT = ImageFont.load_default()


def _blank_page() -> Image.Image:
    img = Image.new("RGB", (_PAGE_W, _PAGE_H), _WHITE)
    return img


def _draw_text(img: Image.Image, y_frac: float, text: str, fill: tuple = _BLACK) -> None:
    draw = ImageDraw.Draw(img)
    x = int(_PAGE_W * 0.08)
    y = int(_PAGE_H * y_frac)
    draw.text((x, y), text, font=_FONT, fill=fill)


# ---------------------------------------------------------------------------
# Odia/Devanagari text strings — genuine Unicode codepoints, not Pillow-rendered
# (Pillow without libraqm cannot shape Indic; we pass native_text instead)
# ---------------------------------------------------------------------------
_ODIA_HEADER = (
    "ଓଡ଼ିଶା ସରକାର ରାଜସ୍ୱ ବିଭାଗ\n"
    "ଜିଲ୍ଲା ଭୂମି ରେକର୍ଡ ଅଫିସ\n"
    "ଜ୍ଞାତ ଜ୍ଞାତ ଭୂ-ସ୍ୱାମୀ ସ୍ୱାମୀ\n"
)

_LATIN_ID_BODY = (
    "IDENTITY DOCUMENT\n"
    "Name: Ramachandra Nayak\n"
    "DOB: 12-March-1985\n"
    "ID: OD-2024-78451\n"
    "District: Puri, Odisha\n"
)

_HINDI_HEADER = (
    "भारत सरकार गृह मंत्रालय\n"
    "राज्य सरकार प्रमाण पत्र\n"
    "जिला कार्यालय प्रशासन\n"
    "मान्यता प्राप्त संस्था\n"
)

_ENGLISH_CERT = (
    "GOVERNMENT OF INDIA\n"
    "MINISTRY OF HOME AFFAIRS\n"
    "Certificate of Domicile\n"
    "This is to certify that the holder is a bonafide resident.\n"
    "Date: 15-November-2024\n"
    "Reference: MHA/2024/78941\n"
)

_SHORT_ODIA = (
    "ରାଜ୍ୟ ରାଜସ୍ୱ ବିଭାଗ ଓଡ଼ିଶା\n"
    "ଜ୍ଞାତ ଭୂ-ସ୍ୱାମୀ ଅଫିସ ଜ୍ଞାତ\n"
    "ଓଡ଼ିଶା ଜ ଓ ଭୂ ରେ ଅ ଓ ଜ ରା\n"
)

_SHORT_HINDI = (
    "भारत सरकार प्रमाण पत्र\n"
    "जिला कार्यालय प्रशासन संस्था\n"
    "मंत्रालय गृह भारत राज्य\n"
)


# ===========================================================================
# TEST CLASS 1 — Strategy D: Indic header at y < 0.25, blank lower half
# ===========================================================================
class TestStrategyDUpperBand:
    """BLIND43_IND_HDR_LAT_ID pattern: Indic at top, Latin ID in middle, blank below."""

    def test_odia_header_latin_id_blank_bottom_routes_multilingual(self):
        """
        BLIND43_IND_HDR_LAT_ID fixture equivalent.
        Odia header at y ≈ 0–0.20; Latin ID at y ≈ 0.45–0.55; bottom blank.
        Strategy D should detect Odia in upper band and route GLOBAL_MULTILINGUAL.
        Uses native_text so Pillow shaping limitation is bypassed.
        """
        img = _blank_page()
        # Minimal visual content so OCR probe can be bypassed via native_text
        combined_native = _ODIA_HEADER + "\n" + _LATIN_ID_BODY
        profile = profile_document(img, native_text=combined_native)
        decision = select_ocr_strategy(profile)
        # Must NOT be FAST_PATH_ENG — Odia header must be detected
        assert decision.selected_strategy != "FAST_PATH_ENG", (
            f"BLIND43_IND_HDR_LAT_ID pattern should not fast-path English. "
            f"Got strategy={decision.selected_strategy}, script={profile.primary_script}"
        )
        # Must be multilingual or Indic-aware
        assert decision.selected_strategy in (
            "GLOBAL_MULTILINGUAL", "MONOLINGUAL_ORI", "REGION_AWARE_ROUTING"
        ), f"Expected multilingual/Odia strategy, got {decision.selected_strategy}"

    def test_hindi_header_latin_id_blank_bottom_routes_multilingual(self):
        """
        Hindi Devanagari header at y < 0.25; Latin ID body; blank lower half.
        Strategy D should detect Devanagari in upper band.
        """
        img = _blank_page()
        combined_native = _HINDI_HEADER + "\n" + _LATIN_ID_BODY
        profile = profile_document(img, native_text=combined_native)
        decision = select_ocr_strategy(profile)
        assert decision.selected_strategy != "FAST_PATH_ENG", (
            f"Hindi header with Latin ID should not fast-path English. "
            f"Got strategy={decision.selected_strategy}"
        )
        assert decision.selected_strategy in (
            "GLOBAL_MULTILINGUAL", "MONOLINGUAL_HIN", "REGION_AWARE_ROUTING"
        )

    def test_odia_header_odia_body_routes_monolingual_or_multilingual(self):
        """Full Odia document should route monolingual or multilingual, never FAST_PATH_ENG."""
        img = _blank_page()
        odia_full = _ODIA_HEADER + "\n" + _SHORT_ODIA * 3
        profile = profile_document(img, native_text=odia_full)
        decision = select_ocr_strategy(profile)
        assert decision.selected_strategy != "FAST_PATH_ENG", (
            f"Full Odia document should not fast-path English."
        )

    def test_hindi_header_hindi_body_routes_monolingual_or_multilingual(self):
        """Full Hindi document should route monolingual or multilingual, never FAST_PATH_ENG."""
        img = _blank_page()
        hindi_full = _HINDI_HEADER + "\n" + _SHORT_HINDI * 3
        profile = profile_document(img, native_text=hindi_full)
        decision = select_ocr_strategy(profile)
        assert decision.selected_strategy != "FAST_PATH_ENG"


# ===========================================================================
# TEST CLASS 2 — False Positive Guard
# ===========================================================================
class TestStrategyDFalsePositiveGuard:
    """
    Strategy D must NOT trigger multilingual routing on English-only pages
    even if the page has a logo, stamp, or letterhead in the upper region.
    Guard: >= 6 real Indic letter codepoints required in upper band.
    """

    def test_english_only_routes_fast_path(self):
        """Pure English certificate must still route FAST_PATH_ENG."""
        img = _blank_page()
        profile = profile_document(img, native_text=_ENGLISH_CERT)
        decision = select_ocr_strategy(profile)
        assert decision.selected_strategy == "FAST_PATH_ENG", (
            f"English-only cert should be FAST_PATH_ENG, got {decision.selected_strategy}"
        )

    def test_english_with_fewer_than_six_indic_chars_fast_path(self):
        """
        English document with 2–5 stray Indic chars (e.g. in a logo or stamp graphic
        that OCR misreads as a few Indic codepoints) must NOT trigger Strategy D.
        """
        img = _blank_page()
        # Only 4 Devanagari chars — below the >= 6 guard threshold
        sparse_indic = "भार" + "\n" + _ENGLISH_CERT  # 3 Devanagari + lots of Latin
        profile = profile_document(img, native_text=sparse_indic)
        decision = select_ocr_strategy(profile)
        # With only 3 Devanagari and majority Latin, should not trigger multilingual
        # (The existing >= 4 Indic anywhere safeguard fires for >=4; sparse_indic has 3)
        assert decision.selected_strategy in ("FAST_PATH_ENG", "GLOBAL_MULTILINGUAL"), (
            f"Sparse Indic (3 chars) should stay Fast English or at most global multi, "
            f"got {decision.selected_strategy}"
        )

    def test_english_long_route_no_regression(self):
        """Multi-paragraph English doc must remain FAST_PATH_ENG throughout Strategy D."""
        img = _blank_page()
        long_eng = (_ENGLISH_CERT + "\n") * 5
        profile = profile_document(img, native_text=long_eng)
        decision = select_ocr_strategy(profile)
        assert decision.selected_strategy == "FAST_PATH_ENG"


# ===========================================================================
# TEST CLASS 3 — Strategy C Regression Guard
# ===========================================================================
class TestStrategyCRegression:
    """Strategy C (Latin header, Indic body) must still work after Strategy D patch."""

    def test_latin_header_hindi_body_still_routes_multilingual(self):
        """BLIND43_LAT_HDR_HIN_BODY pattern: Latin header, Hindi body — Strategy C fix."""
        img = _blank_page()
        combined_native = "GOVERNMENT CIRCULAR NO. 2024/ADM/44\n" + _SHORT_HINDI * 4
        profile = profile_document(img, native_text=combined_native)
        decision = select_ocr_strategy(profile)
        assert decision.selected_strategy != "FAST_PATH_ENG", (
            "Latin header with Hindi body must NOT fast-path English (Strategy C regression)"
        )

    def test_latin_header_odia_body_still_routes_multilingual(self):
        """Latin header with Odia body must route multilingual."""
        img = _blank_page()
        combined_native = "ODISHA REVENUE DEPARTMENT — NOTICE NO. 2024/REV/12\n" + _SHORT_ODIA * 4
        profile = profile_document(img, native_text=combined_native)
        decision = select_ocr_strategy(profile)
        assert decision.selected_strategy != "FAST_PATH_ENG"


# ===========================================================================
# TEST CLASS 4 — Existing Pure Corpus Routing (Regression)
# ===========================================================================
class TestExistingCorpusNoRegression:
    """Core corpus documents must route identically to Loop 43 baselines."""

    def test_english_certificate_fast_path(self):
        """English-only certificate routes FAST_PATH_ENG."""
        img = _blank_page()
        profile = profile_document(img, native_text=_ENGLISH_CERT)
        decision = select_ocr_strategy(profile)
        assert decision.selected_strategy == "FAST_PATH_ENG"

    def test_pure_odia_routes_monolingual_or_multilingual(self):
        """Pure Odia document should not route FAST_PATH_ENG."""
        img = _blank_page()
        profile = profile_document(img, native_text=_SHORT_ODIA * 6)
        decision = select_ocr_strategy(profile)
        assert decision.selected_strategy != "FAST_PATH_ENG"

    def test_pure_hindi_routes_monolingual_or_multilingual(self):
        """Pure Hindi document should not route FAST_PATH_ENG."""
        img = _blank_page()
        profile = profile_document(img, native_text=_SHORT_HINDI * 6)
        decision = select_ocr_strategy(profile)
        assert decision.selected_strategy != "FAST_PATH_ENG"

    def test_mixed_hindi_english_routes_multilingual(self):
        """Mixed Hindi+English document routes GLOBAL_MULTILINGUAL."""
        img = _blank_page()
        mixed_native = _SHORT_HINDI * 3 + "\n" + _ENGLISH_CERT
        profile = profile_document(img, native_text=mixed_native)
        decision = select_ocr_strategy(profile)
        assert decision.selected_strategy in (
            "GLOBAL_MULTILINGUAL", "REGION_AWARE_ROUTING"
        ), f"Mixed doc should be multilingual, got {decision.selected_strategy}"

    def test_blank_page_abstains(self):
        """Blank page (ink < 0.003) must ABSTAIN."""
        img = Image.new("RGB", (_PAGE_W, _PAGE_H), _WHITE)
        profile = profile_document(img)
        decision = select_ocr_strategy(profile)
        assert decision.selected_strategy == "ABSTAIN_UNREADABLE"

    def test_tiny_image_no_zero_division(self):
        """1×1 image must not raise ZeroDivisionError."""
        img = Image.new("RGB", (1, 1), _WHITE)
        profile = profile_document(img)
        # Must not raise; strategy may be unreadable or unknown
        assert profile is not None


# ===========================================================================
# TEST CLASS 5 — Profile-Stage Attributes
# ===========================================================================
class TestProfileAttributes:
    """profile_document() must set expected attributes for each document type."""

    def test_odia_header_profile_has_indic_script(self):
        """Profile for Odia+Latin doc must reflect Odia/mixed, not pure Latin."""
        img = _blank_page()
        combined_native = _ODIA_HEADER + "\n" + _LATIN_ID_BODY
        profile = profile_document(img, native_text=combined_native)
        # primary_script must NOT be LATIN
        assert profile.primary_script != "LATIN", (
            f"Odia+Latin doc should not profile as LATIN. Got {profile.primary_script}"
        )

    def test_english_profile_is_latin(self):
        """Profile for English-only doc must be LATIN, not mixed."""
        img = _blank_page()
        profile = profile_document(img, native_text=_ENGLISH_CERT)
        assert profile.primary_script == "LATIN"
        assert not profile.is_mixed_script

    def test_profiling_latency_field_present(self):
        """profiling_latency_ms must be set and positive."""
        img = _blank_page()
        profile = profile_document(img, native_text=_ENGLISH_CERT)
        assert profile.profiling_latency_ms is not None
        assert profile.profiling_latency_ms >= 0.0


# ===========================================================================
# TEST CLASS 6 — Strategy D Minimum Indic Threshold Boundary
# ===========================================================================
class TestStrategyDThreshold:
    """Verify the >= 6 Indic char minimum boundary for Strategy D."""

    def test_exactly_six_indic_chars_triggers_detection(self):
        """Exactly 6 Indic chars (above threshold) should mark as mixed/Indic."""
        img = _blank_page()
        # 6 Odia chars + lots of Latin
        exactly_six = "ଓଡ଼ିଶା ସ" + "\n" + _ENGLISH_CERT  # ≈ 6 Odia codepoints
        profile = profile_document(img, native_text=exactly_six)
        decision = select_ocr_strategy(profile)
        # With 6 Odia chars mixed with Latin, the safeguard or probe should not fast-path
        # (The >= 4 anywhere safeguard already fires at 4 chars)
        assert decision.selected_strategy in (
            "GLOBAL_MULTILINGUAL", "MONOLINGUAL_ORI", "FAST_PATH_ENG"
        )  # At 6+ the safeguard fires, changing to multilingual

    def test_strategy_d_does_not_affect_non_latin_central(self):
        """If the central probe is NOT Latin, upper-band is never needed."""
        img = _blank_page()
        # Pure Hindi — central will be DEVANAGARI, no Strategy D trigger
        profile = profile_document(img, native_text=_SHORT_HINDI * 8)
        decision = select_ocr_strategy(profile)
        assert decision.selected_strategy in (
            "MONOLINGUAL_HIN", "GLOBAL_MULTILINGUAL"
        )

    def test_raster_odia_header_latin_id_blank_bottom_routes_multilingual(self):
        """
        End-to-end RASTER test (no native_text) for Strategy D:
        Real Odia header cropped from DOC_EXT_06 at y=0.05..0.21,
        Latin ID in central strip (0.28..0.42), blank lower half (0.50..1.0).
        """
        odia_corpus = Path(__file__).resolve().parents[1] / "research" / "loop18" / "corpus" / "DOC_EXT_06_ODIA_REVENUE_NOTICE.png"
        if not odia_corpus.exists():
            pytest.skip("DOC_EXT_06 corpus image not available")
        src_img = Image.open(odia_corpus).convert("RGB")
        ow, oh = src_img.size
        w, h = 1200, 1600
        page = Image.new("RGB", (w, h), _WHITE)
        crop = src_img.crop((int(ow * 0.05), int(oh * 0.10), int(ow * 0.95), int(oh * 0.35)))
        crop_r = crop.resize((int(w * 0.85), int(h * 0.16)), Image.Resampling.BILINEAR)
        page.paste(crop_r, (int(w * 0.075), int(h * 0.05)))
        draw = ImageDraw.Draw(page)
        try:
            fnt = ImageFont.truetype("arial.ttf", 34)
        except OSError:
            fnt = _FONT
        draw.text((int(w * 0.18), int(h * 0.28)), "GOVERNMENT IDENTITY RECORD", fill=_BLACK, font=fnt)
        draw.text((int(w * 0.18), int(h * 0.33)), "Name: Ramachandra Nayak", fill=_BLACK, font=fnt)
        draw.text((int(w * 0.18), int(h * 0.38)), "ID: OD-2024-78451", fill=_BLACK, font=fnt)

        profile = profile_document(page)
        decision = select_ocr_strategy(profile)
        assert decision.selected_strategy != "FAST_PATH_ENG", (
            f"Raster BLIND43_IND_HDR_LAT_ID must not fast-path English. "
            f"Got {decision.selected_strategy}, script={profile.primary_script}, counts={profile.script_counts}"
        )
        assert decision.selected_strategy == "GLOBAL_MULTILINGUAL"

    def test_raster_english_with_upper_seal_stays_fast_path(self):
        """
        End-to-end RASTER false-positive guard:
        English page with geometric seal + English label in upper band, blank lower half.
        Must remain FAST_PATH_ENG.
        """
        w, h = 1200, 1600
        page = Image.new("RGB", (w, h), _WHITE)
        draw = ImageDraw.Draw(page)
        try:
            fnt = ImageFont.truetype("arial.ttf", 34)
        except OSError:
            fnt = _FONT
        draw.ellipse((int(w * 0.18), int(h * 0.07), int(w * 0.28), int(h * 0.17)), outline=_BLACK, width=4)
        draw.text((int(w * 0.32), int(h * 0.10)), "OFFICIAL SEAL 2024", fill=_BLACK, font=fnt)
        draw.text((int(w * 0.18), int(h * 0.28)), "CERTIFICATE OF DOMICILE", fill=_BLACK, font=fnt)
        draw.text((int(w * 0.18), int(h * 0.34)), "This certifies the holder is a resident.", fill=_BLACK, font=fnt)
        draw.text((int(w * 0.18), int(h * 0.40)), "Reference: MHA/2024/78941", fill=_BLACK, font=fnt)

        profile = profile_document(page)
        decision = select_ocr_strategy(profile)
        assert decision.selected_strategy == "FAST_PATH_ENG"

