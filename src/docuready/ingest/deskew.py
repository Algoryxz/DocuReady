"""
Deskew and Coordinate Transformation Module for DocuReady.
Provides projection-profile skew angle estimation and exact inverse affine bounding box mapping.
"""

from typing import Tuple, List, Optional
import math
import numpy as np
import PIL.Image


def estimate_skew_angle(
    img: PIL.Image.Image,
    max_angle: float = 45.0,
    thumb_height: int = 600,
    min_confidence: float = 5.0,
    hint_angle: Optional[float] = None
) -> Tuple[float, float]:
    """
    Estimates document skew angle in degrees using horizontal projection profile variance.
    Returns (correction_angle_deg, confidence).
    
    A positive correction_angle_deg means PIL.rotate(correction_angle_deg) restores horizontal text.
    If confidence < min_confidence or |correction_angle| < 1.0, returns (0.0, confidence).
    """
    if img.height <= 0 or img.width <= 0:
        return 0.0, 0.0

    # Downsample to thumbnail height for fast evaluation (~100-200ms)
    scale = float(thumb_height) / max(img.height, 1)
    new_w = max(int(img.width * scale), 1)
    thumb = img.resize((new_w, thumb_height), PIL.Image.Resampling.BILINEAR).convert("L")
    try:
        arr = np.array(thumb)
    finally:
        thumb.close()

    # Dynamic percentile thresholding:
    # Captures faint text (carbon copies) and handles shadow gradients robustly
    p_low = float(np.percentile(arr, 0.05))
    p_high = float(np.percentile(arr, 99.5))
    dynamic_range = p_high - p_low
    if dynamic_range <= 2.0:
        return 0.0, 0.0

    thresh = p_low + 0.60 * dynamic_range
    bin_arr = (arr < thresh).astype(np.uint8)

    # If document has almost no foreground pixels (e.g. blank scan), return 0.0
    fg_count = int(np.sum(bin_arr))
    if fg_count < 50:
        return 0.0, 0.0

    bin_pil = PIL.Image.fromarray(bin_arr * 255)
    try:
        # Coarse search: 1.5 degree increments across [-max_angle, +max_angle]
        coarse_angles = np.arange(-max_angle, max_angle + 1.5, 1.5)
        coarse_scores = []

        for a in coarse_angles:
            if abs(a) < 0.01:
                rot_arr = bin_arr
            else:
                with bin_pil.rotate(float(a), resample=PIL.Image.Resampling.NEAREST) as rot_pil:
                    rot_arr = np.array(rot_pil)
            proj = np.sum(rot_arr, axis=1)
            score = float(np.sum(np.diff(proj) ** 2))
            coarse_scores.append(score)

        coarse_scores = np.array(coarse_scores)
        median_score = float(np.median(coarse_scores))
        if median_score <= 0:
            median_score = 1e-6

        # Detect prominent local peaks (higher than neighbors)
        peaks = []
        for i in range(len(coarse_scores)):
            prev_s = coarse_scores[i - 1] if i > 0 else -1.0
            next_s = coarse_scores[i + 1] if i < len(coarse_scores) - 1 else -1.0
            if coarse_scores[i] >= prev_s and coarse_scores[i] >= next_s:
                peaks.append((coarse_scores[i], float(coarse_angles[i])))

        peaks.sort(key=lambda x: x[0], reverse=True)
        if not peaks:
            return 0.0, 0.0

        best_score, best_angle = peaks[0]
        peak_ratio = best_score / median_score
        selected_angle = best_angle
        confidence = peak_ratio

        # Ambiguity and multi-signal resolution
        if hint_angle is not None:
            dist_best = abs(best_angle - hint_angle)
            if dist_best <= 2.5:
                selected_angle = best_angle
                confidence = peak_ratio
            else:
                # Best peak does not match token slope (likely watermark or border).
                # Look for a candidate peak that matches the hint angle within 2.5°
                matching_peaks = [p for p in peaks if abs(p[1] - hint_angle) <= 2.5 and (p[0] / median_score) >= min_confidence]
                if matching_peaks:
                    selected_angle = matching_peaks[0][1]
                    confidence = matching_peaks[0][0] / median_score
                else:
                    confidence = peak_ratio * 0.3
        else:
            # No hint available
            if abs(best_angle) > 25.0:
                # Extreme angle typical of diagonal watermarks; check plausible physical skew range
                plausible_peaks = [p for p in peaks if abs(p[1]) <= 25.0 and (p[0] / median_score) >= min_confidence]
                if plausible_peaks:
                    selected_angle = plausible_peaks[0][1]
                    confidence = plausible_peaks[0][0] / median_score
                else:
                    confidence = peak_ratio * 0.5
            else:
                # Plausible range: check dominance ratio against competing secondary peaks
                secondary_peaks = [p for p in peaks[1:] if abs(p[1] - best_angle) >= 3.0]
                if secondary_peaks:
                    sec_score, sec_angle = secondary_peaks[0]
                    dominance_ratio = best_score / max(sec_score, 1e-6)
                    if dominance_ratio < 1.35:
                        confidence = peak_ratio * (dominance_ratio / 1.35)

        # If peak-to-median ratio is weak, no reliable horizontal line structure exists
        if confidence < min_confidence:
            return 0.0, confidence

        # Fine search: 0.1 degree increments in ±1.5 degrees around selected coarse peak
        fine_angles = np.arange(selected_angle - 1.5, selected_angle + 1.55, 0.1)
        best_fine_angle = selected_angle
        best_fine_score = -1.0

        for a in fine_angles:
            with bin_pil.rotate(float(a), resample=PIL.Image.Resampling.NEAREST) as rot_pil:
                rot_arr = np.array(rot_pil)
            proj = np.sum(rot_arr, axis=1)
            score = float(np.sum(np.diff(proj) ** 2))
            if score > best_fine_score:
                best_fine_score = score
                best_fine_angle = float(a)
    finally:
        bin_pil.close()

    best_angle = round(best_fine_angle, 2)

    # Decision Invariant: Skew < 1.0 degree is considered aligned (No-Op)
    if abs(best_angle) < 1.0:
        return 0.0, confidence

    return best_angle, confidence


def deskew_image(
    img: PIL.Image.Image,
    correction_angle: float,
    fillcolor: Tuple[int, int, int] = (255, 255, 255)
) -> Tuple[PIL.Image.Image, Tuple[int, int], Tuple[int, int]]:
    """
    Applies deskew rotation with expand=True and paper-white fillcolor.
    Returns (transformed_img, orig_size, rot_size).
    """
    orig_size = (img.width, img.height)
    if abs(correction_angle) < 1.0:
        return img, orig_size, orig_size

    # Use white background to prevent black border artifacts from disrupting Tesseract page layout analysis
    rot_img = img.rotate(
        correction_angle,
        expand=True,
        fillcolor=fillcolor,
        resample=PIL.Image.Resampling.BILINEAR
    )
    rot_size = (rot_img.width, rot_img.height)
    return rot_img, orig_size, rot_size


def transform_bbox_inverse(
    bbox: List[float],
    rotation_angle: float,
    orig_size: Tuple[int, int],
    rot_size: Tuple[int, int],
    scale: float = 1.0
) -> List[float]:
    """
    Maps bounding box [x0, y0, x1, y1] from rotated image coordinates back to original unrotated image coordinates.
    Multiplies final coordinates by scale (e.g. 72.0 / dpi for PDF points).
    """
    if abs(rotation_angle) < 1e-4 or orig_size == rot_size:
        return [
            round(bbox[0] * scale, 1),
            round(bbox[1] * scale, 1),
            round(bbox[2] * scale, 1),
            round(bbox[3] * scale, 1)
        ]

    W0, H0 = orig_size
    W1, H1 = rot_size
    cx0, cy0 = W0 / 2.0, H0 / 2.0
    cx1, cy1 = W1 / 2.0, H1 / 2.0

    rad = math.radians(rotation_angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    x0, y0, x1, y1 = bbox
    corners = [
        (x0, y0),
        (x1, y0),
        (x0, y1),
        (x1, y1),
    ]

    orig_corners = []
    for px, py in corners:
        dx1 = px - cx1
        dy1 = py - cy1
        # Inverse affine rotation for PIL counter-clockwise rotation:
        # ox = cx0 + dx1 * cos(a) - dy1 * sin(a)
        # oy = cy0 + dx1 * sin(a) + dy1 * cos(a)
        ox = cx0 + dx1 * cos_a - dy1 * sin_a
        oy = cy0 + dx1 * sin_a + dy1 * cos_a
        orig_corners.append((ox, oy))

    min_x = max(0.0, min(c[0] for c in orig_corners))
    min_y = max(0.0, min(c[1] for c in orig_corners))
    max_x = min(float(W0), max(c[0] for c in orig_corners))
    max_y = min(float(H0), max(c[1] for c in orig_corners))

    # Guard against degenerate zero-width or zero-height boxes (e.g. single-pixel punctuation or extreme clipping)
    if max_x - min_x < 1.0:
        max_x = min(float(W0), min_x + 1.0)
    if max_y - min_y < 1.0:
        max_y = min(float(H0), min_y + 1.0)

    return [
        round(min_x * scale, 1),
        round(min_y * scale, 1),
        round(max_x * scale, 1),
        round(max_y * scale, 1)
    ]
