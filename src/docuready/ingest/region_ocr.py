"""
Region-Aware Multilingual OCR & Script-Level Routing Subsystem
DocuReady - Multilingual Ingestion Subsystem

Decomposes documents into spatial layout regions (headers, columns, tables, footers, body blocks),
classifies script per region (Latin/English, Devanagari/Hindi, Odia, mixed), routes each sub-image
to its optimal Tesseract language model, and reconstructs evidence with exact global coordinates,
reading order, and confidence metrics.
"""

from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from PIL import Image

from docuready.ingest.script_router import (
    RE_DEVANAGARI,
    RE_LATIN,
    RE_ODIA,
    detect_image_script_osd,
    detect_unicode_script,
)
from docuready.ingest.tesseract_discovery import configure_pytesseract


@dataclass
class DocumentRegion:
    """Represents a discrete spatial layout region of a document page."""

    region_id: int
    bbox_px: Tuple[int, int, int, int]  # (x0, y0, x1, y1) in pixel space
    region_type: str  # HEADER, BODY, COLUMN_LEFT, COLUMN_RIGHT, TABLE, FOOTER, UNIFORM
    detected_lang: str  # eng, hin, ori, eng+hin, eng+ori
    primary_script: str  # LATIN, DEVANAGARI, ODIA, MIXED_DEVANAGARI_LATIN, MIXED_ODIA_LATIN
    confidence: float = 1.0
    text_preview: str = ""


def segment_page_into_regions(
    img: Image.Image,
    native_blocks: Optional[List[Dict[str, Any]]] = None,
    min_region_height: int = 30
) -> List[DocumentRegion]:
    """
    Partitions a page image into structural spatial regions.

    If native_blocks from a PDF layer are provided, utilizes exact text bounds and Unicode
    frequencies. Otherwise, computes horizontal and vertical projection profiles on the raster image.
    """
    w, h = img.size
    regions: List[DocumentRegion] = []

    # 1. Native PDF text block-guided segmentation (highest precision)
    if native_blocks and len(native_blocks) > 0:
        # Sort blocks top-to-bottom, left-to-right
        valid_blocks = [b for b in native_blocks if b.get("text", "").strip()]
        if valid_blocks:
            # Check script of each block
            reg_idx = 0
            for blk in valid_blocks:
                b_text = blk.get("text", "").strip()
                b_box = blk.get("bbox", [0, 0, w, h])
                # Convert PDF point coordinates to pixel space if needed
                # If bbox coordinates are in 72 DPI points:
                if b_box[2] <= 1000 and b_box[3] <= 1500 and max(w, h) > 1500:
                    scale = float(w) / max(1.0, float(b_box[2] if b_box[2] > 500 else 595.0))
                    px_box = (
                        int(b_box[0] * scale),
                        int(b_box[1] * scale),
                        int(b_box[2] * scale),
                        int(b_box[3] * scale),
                    )
                else:
                    px_box = (int(b_box[0]), int(b_box[1]), int(b_box[2]), int(b_box[3]))

                # Clamp to image dimensions
                px_box = (
                    max(0, px_box[0]),
                    max(0, px_box[1]),
                    min(w, px_box[2]),
                    min(h, px_box[3]),
                )

                if px_box[2] - px_box[0] < 10 or px_box[3] - px_box[1] < 10:
                    continue

                script_res = detect_unicode_script(b_text)
                reg_type = "BODY"
                if px_box[1] < h * 0.18:
                    reg_type = "HEADER"
                elif px_box[3] > h * 0.88:
                    reg_type = "FOOTER"

                regions.append(
                    DocumentRegion(
                        region_id=reg_idx,
                        bbox_px=px_box,
                        region_type=reg_type,
                        detected_lang=script_res["detected_lang"],
                        primary_script=script_res["primary_script"],
                        confidence=1.0,
                        text_preview=b_text[:60],
                    )
                )
                reg_idx += 1

            if regions:
                return regions

    # 2. Raster-based projection segmentation
    gray = img.convert("L")
    arr = (np.array(gray) < 210).astype(np.uint8)

    # Horizontal projection profile
    h_proj = arr.sum(axis=1)
    min_pixels_per_row = max(10, int(w * 0.01))

    # Identify horizontal bands separated by whitespace gaps
    raw_bands: List[Tuple[int, int]] = []
    in_band = False
    start_y = 0

    for y, count in enumerate(h_proj):
        if count >= min_pixels_per_row and not in_band:
            in_band = True
            start_y = y
        elif count < min_pixels_per_row and in_band:
            in_band = False
            if y - start_y >= 10:
                raw_bands.append((start_y, y))
    if in_band and len(h_proj) - start_y >= 10:
        raw_bands.append((start_y, len(h_proj)))

    if not raw_bands:
        # Uniform fallback
        return [
            DocumentRegion(
                region_id=0,
                bbox_px=(0, 0, w, h),
                region_type="UNIFORM",
                detected_lang="eng",
                primary_script="LATIN",
                confidence=1.0,
                text_preview="",
            )
        ]

    # Merge closely spaced bands (e.g. lines belonging to the same paragraph)
    merged_bands: List[Tuple[int, int]] = []
    max_line_gap = max(15, int(h * 0.035))  # lines within 3.5% page height merge into blocks

    curr_start, curr_end = raw_bands[0]
    for b_start, b_end in raw_bands[1:]:
        gap = b_start - curr_end
        if gap <= max_line_gap:
            curr_end = b_end
        else:
            merged_bands.append((curr_start, curr_end))
            curr_start, curr_end = b_start, b_end
    merged_bands.append((curr_start, curr_end))

    # For each merged horizontal band, check for multi-column splits (vertical gutters)
    reg_id = 0
    for y0, y1 in merged_bands:
        band_h = y1 - y0
        if band_h < 12:
            continue

        # Add modest padding (5-10px) to prevent clipping accents or matras
        pad_y0 = max(0, y0 - 6)
        pad_y1 = min(h, y1 + 6)

        band_arr = arr[y0:y1, :]
        v_proj = band_arr.sum(axis=0)

        # Check for wide vertical gutter (column split) in the body
        mid_start = int(w * 0.35)
        mid_end = int(w * 0.65)
        gutter_width = int(w * 0.04)

        is_split = False
        split_x = -1
        # Search for quiet zone in middle of band with ink on BOTH sides
        for x in range(mid_start, mid_end - gutter_width):
            if v_proj[x : x + gutter_width].max() == 0:
                left_ink = v_proj[:x].max() > 0
                right_ink = v_proj[x + gutter_width :].max() > 0
                if left_ink and right_ink:
                    is_split = True
                    split_x = x + gutter_width // 2
                    break

        # Determine structural role
        if pad_y0 < h * 0.18:
            role = "HEADER"
        elif pad_y1 > h * 0.88:
            role = "FOOTER"
        else:
            role = "BODY"

        if is_split and role == "BODY":
            # Left column
            regions.append(
                DocumentRegion(
                    region_id=reg_id,
                    bbox_px=(0, pad_y0, split_x, pad_y1),
                    region_type="COLUMN_LEFT",
                    detected_lang="eng",
                    primary_script="LATIN",
                )
            )
            reg_id += 1
            # Right column
            regions.append(
                DocumentRegion(
                    region_id=reg_id,
                    bbox_px=(split_x, pad_y0, w, pad_y1),
                    region_type="COLUMN_RIGHT",
                    detected_lang="eng",
                    primary_script="LATIN",
                )
            )
            reg_id += 1
        else:
            regions.append(
                DocumentRegion(
                    region_id=reg_id,
                    bbox_px=(0, pad_y0, w, pad_y1),
                    region_type=role,
                    detected_lang="eng",
                    primary_script="LATIN",
                )
            )
            reg_id += 1

    return regions


def classify_region_script(
    img_crop: Image.Image,
    native_text: Optional[str] = None,
    preferred_fallback: str = "eng"
) -> Tuple[str, str]:
    """
    Determines the optimal Tesseract language string and primary script for a cropped region.
    Returns (detected_lang, primary_script).
    """
    # 1. Native text analysis if provided
    if native_text and len(native_text.strip()) >= 10:
        res = detect_unicode_script(native_text)
        return res["detected_lang"], res["primary_script"]

    # 2. Fast sub-image script sampling
    import pytesseract

    # Run quick sample OCR using eng+hin+ori on the crop to inspect Unicode distribution
    try:
        sample_txt = pytesseract.image_to_string(
            img_crop,
            lang="eng+hin+ori",
            config="--psm 6",
            timeout=3
        )
        if sample_txt and len(sample_txt.strip()) >= 5:
            res = detect_unicode_script(sample_txt)
            if res["counts"]["total"] >= 4:
                return res["detected_lang"], res["primary_script"]
    except Exception:
        pass

    # 3. Fallback
    return preferred_fallback, "LATIN"


def ocr_page_by_regions(
    img: Image.Image,
    dpi: int = 200,
    preferred_lang: Optional[str] = None,
    native_blocks: Optional[List[Dict[str, Any]]] = None,
    enable_confidence_fallback: bool = True
) -> Dict[str, Any]:
    """
    Performs Region-Aware Multilingual OCR across the page image.

    Segments the page into regions, identifies script per region, performs targeted
    sub-image OCR, translates coordinates back to page space, and returns a unified
    Tesseract data dictionary compatible with PageOCRData.
    """
    import pytesseract

    configure_pytesseract()
    w, h = img.size

    regions = segment_page_into_regions(img, native_blocks=native_blocks)

    # Initialize accumulated token dictionary
    accum_data: Dict[str, List[Any]] = {
        "level": [],
        "page_num": [],
        "block_num": [],
        "par_num": [],
        "line_num": [],
        "word_num": [],
        "left": [],
        "top": [],
        "width": [],
        "height": [],
        "conf": [],
        "text": []
    }

    # If only 1 uniform region, run direct page pass
    if len(regions) <= 1:
        reg_lang = preferred_lang or "eng"
        try:
            return pytesseract.image_to_data(
                img,
                lang=reg_lang,
                output_type=pytesseract.Output.DICT,
                timeout=15
            )
        except Exception:
            return accum_data

    # Classify language for all regions
    for reg in regions:
        rx0, ry0, rx1, ry1 = reg.bbox_px
        crop = img.crop((rx0, ry0, rx1, ry1))
        lang_str, script_str = classify_region_script(crop, native_text=reg.text_preview)
        reg.detected_lang = lang_str
        reg.primary_script = script_str

    # Zero-Regression Fast Path:
    # If the page has no columns and every region is homogeneous English, run direct full-page pass!
    is_multi_script = any(r.detected_lang != "eng" for r in regions)
    has_columns = any(r.region_type in ("COLUMN_LEFT", "COLUMN_RIGHT") for r in regions)
    if not is_multi_script and not has_columns and (not preferred_lang or preferred_lang == "eng"):
        try:
            return pytesseract.image_to_data(
                img,
                lang="eng",
                output_type=pytesseract.Output.DICT,
                timeout=15
            )
        except Exception:
            return accum_data

    # Multi-region targeted execution
    for reg in regions:
        rx0, ry0, rx1, ry1 = reg.bbox_px
        rw = rx1 - rx0
        rh = ry1 - ry0
        if rw < 15 or rh < 10:
            continue

        crop = img.crop((rx0, ry0, rx1, ry1))

        # Determine language for this region
        if preferred_lang and preferred_lang != "auto":
            target_lang = preferred_lang
        else:
            target_lang = reg.detected_lang

        # Execute targeted OCR on sub-image
        try:
            reg_data = pytesseract.image_to_data(
                crop,
                lang=target_lang,
                output_type=pytesseract.Output.DICT,
                timeout=8
            )
        except Exception:
            reg_data = {"text": [], "conf": [], "left": [], "top": [], "width": [], "height": []}

        # Confidence fallback: if recognition yielded very poor confidence or no tokens
        if enable_confidence_fallback:
            valid_words = [
                str(t).strip() for t, c in zip(reg_data.get("text", []), reg_data.get("conf", []))
                if str(t).strip() and float(c) >= 0
            ]
            confs = [float(c) for c in reg_data.get("conf", []) if float(c) >= 0]
            mean_conf = (sum(confs) / len(confs)) if confs else 0.0

            if (len(valid_words) == 0 or mean_conf < 25.0) and target_lang != "eng":
                # Fallback to English / Compound model
                fallback_model = "eng+hin" if "hin" in target_lang else "eng"
                try:
                    alt_data = pytesseract.image_to_data(
                        crop,
                        lang=fallback_model,
                        output_type=pytesseract.Output.DICT,
                        timeout=8
                    )
                    alt_valid = [
                        str(t).strip() for t, c in zip(alt_data.get("text", []), alt_data.get("conf", []))
                        if str(t).strip() and float(c) >= 0
                    ]
                    if len(alt_valid) > len(valid_words):
                        reg_data = alt_data
                except Exception:
                    pass

        # Remap token coordinates to global page space
        n_words = len(reg_data.get("text", []))
        for i in range(n_words):
            word = str(reg_data["text"][i]).strip()
            conf = float(reg_data["conf"][i])
            if not word or conf < 0:
                continue

            local_l = float(reg_data["left"][i])
            local_t = float(reg_data["top"][i])
            local_w = float(reg_data["width"][i])
            local_h = float(reg_data["height"][i])

            global_l = rx0 + local_l
            global_t = ry0 + local_t

            accum_data["left"].append(int(global_l))
            accum_data["top"].append(int(global_t))
            accum_data["width"].append(int(local_w))
            accum_data["height"].append(int(local_h))
            accum_data["conf"].append(conf)
            accum_data["text"].append(word)

    return accum_data
