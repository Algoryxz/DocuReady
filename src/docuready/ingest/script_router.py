"""
Script-Aware OCR Routing and Language Selection
DocuReady - Multilingual Ingestion Subsystem

Provides deterministic script identification and adaptive language configuration
for English, Hindi (Devanagari), Odia, and mixed-script Indian administrative documents.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

# Unicode codepoint ranges
RE_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
RE_ODIA = re.compile(r"[\u0B00-\u0B7F]")
RE_LATIN = re.compile(r"[A-Za-z]")


def detect_unicode_script(text: str) -> Dict[str, Any]:
    """
    Analyzes Unicode character codepoints to determine script distribution.
    Returns primary script, confidence, and character distribution counts.
    """
    if not text or not text.strip():
        return {
            "primary_script": "LATIN",
            "detected_lang": "eng",
            "counts": {"latin": 0, "devanagari": 0, "odia": 0, "total": 0},
            "is_mixed": False
        }

    dev_count = len(RE_DEVANAGARI.findall(text))
    odia_count = len(RE_ODIA.findall(text))
    latin_count = len(RE_LATIN.findall(text))
    total_indic = dev_count + odia_count
    total_alpha = latin_count + total_indic

    counts = {
        "latin": latin_count,
        "devanagari": dev_count,
        "odia": odia_count,
        "total": total_alpha
    }

    if total_alpha == 0:
        return {
            "primary_script": "LATIN",
            "detected_lang": "eng",
            "counts": counts,
            "is_mixed": False
        }

    # Ratio thresholds
    dev_ratio = dev_count / total_alpha
    odia_ratio = odia_count / total_alpha
    latin_ratio = latin_count / total_alpha

    # Mixed script detection (e.g. bilingual forms where both scripts have >= 15% presence)
    if dev_ratio >= 0.15 and latin_ratio >= 0.15:
        return {
            "primary_script": "MIXED_DEVANAGARI_LATIN",
            "detected_lang": "eng+hin",
            "counts": counts,
            "is_mixed": True
        }

    if odia_ratio >= 0.15 and latin_ratio >= 0.15:
        return {
            "primary_script": "MIXED_ODIA_LATIN",
            "detected_lang": "eng+ori",
            "counts": counts,
            "is_mixed": True
        }

    if dev_ratio > 0.40 and dev_count > odia_count:
        return {
            "primary_script": "DEVANAGARI",
            "detected_lang": "hin",
            "counts": counts,
            "is_mixed": False
        }

    if odia_ratio > 0.40 and odia_count > dev_count:
        return {
            "primary_script": "ODIA",
            "detected_lang": "ori",
            "counts": counts,
            "is_mixed": False
        }

    return {
        "primary_script": "LATIN",
        "detected_lang": "eng",
        "counts": counts,
        "is_mixed": False
    }


def detect_image_script_osd(img: Image.Image) -> Optional[Dict[str, Any]]:
    """
    Leverages Tesseract Orientation and Script Detection (OSD) to estimate image script.
    Returns script metadata if confident, or None if inconclusive.
    """
    import pytesseract

    try:
        # Resize large image to thumbnail for fast OSD estimation (300-500px)
        w, h = img.size
        scale = min(1.0, 1000.0 / max(w, h))
        if scale < 1.0:
            osd_img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
        else:
            osd_img = img

        osd_text = pytesseract.image_to_osd(osd_img, timeout=5)
        parsed = {}
        for line in osd_text.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                parsed[k.strip().lower()] = v.strip()

        script = parsed.get("script", "").capitalize()
        script_conf = float(parsed.get("script confidence", 0.0))

        if script_conf < 5.0:
            return None

        if script == "Devanagari":
            return {"primary_script": "DEVANAGARI", "detected_lang": "hin", "confidence": script_conf}
        elif script == "Latin":
            return {"primary_script": "LATIN", "detected_lang": "eng", "confidence": script_conf}

        return None
    except Exception:
        return None


def resolve_optimal_ocr_language(
    native_text: Optional[str] = None,
    img: Optional[Image.Image] = None,
    fallback_lang: str = "eng"
) -> str:
    """
    Determines the optimal Tesseract language string ('eng', 'hin', 'ori', 'eng+hin', 'eng+ori')
    using native text analysis first, then visual OSD / heuristics, and finally defaulting safely.
    """
    # 1. Native text inspection (highest precision)
    if native_text and len(native_text.strip()) >= 20:
        script_info = detect_unicode_script(native_text)
        return script_info["detected_lang"]

    # 2. Visual OSD inspection if image is available
    if img is not None:
        osd_res = detect_image_script_osd(img)
        if osd_res:
            return osd_res["detected_lang"]

    return fallback_lang
