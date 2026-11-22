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
    min_confidence: float = 5.0
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
    arr = np.array(thumb)

    # Adaptive binarization: 1 for text, 0 for background
    mean_val = float(np.mean(arr))
    thresh = mean_val * 0.90
    bin_arr = (arr < thresh).astype(np.uint8)

    # If document has almost no foreground pixels (e.g. blank scan), return 0.0
    fg_count = int(np.sum(bin_arr))
    if fg_count < 100:
        return 0.0, 0.0

    bin_pil = PIL.Image.fromarray(bin_arr * 255)

    # Coarse search: 1.5 degree increments across [-max_angle, +max_angle]
    coarse_angles = np.arange(-max_angle, max_angle + 1.5, 1.5)
    coarse_scores = []

    for a in coarse_angles:
        if abs(a) < 0.01:
            rot_arr = bin_arr
        else:
            rot_arr = np.array(bin_pil.rotate(float(a), resample=PIL.Image.Resampling.NEAREST))
        proj = np.sum(rot_arr, axis=1)
        score = float(np.sum(np.diff(proj) ** 2))
        coarse_scores.append(score)

    coarse_scores = np.array(coarse_scores)
    best_coarse_idx = int(np.argmax(coarse_scores))
    best_coarse_angle = float(coarse_angles[best_coarse_idx])
    peak_score = float(coarse_scores[best_coarse_idx])
    median_score = float(np.median(coarse_scores))

    confidence = peak_score / max(median_score, 1e-6)

    # If peak-to-median ratio is weak, no reliable horizontal line structure exists
    if confidence < min_confidence:
        return 0.0, confidence

    # Fine search: 0.2 degree increments in ±1.2 degrees around coarse peak
    fine_angles = np.arange(best_coarse_angle - 1.2, best_coarse_angle + 1.4, 0.2)
    best_fine_angle = best_coarse_angle
    best_fine_score = peak_score

    for a in fine_angles:
        rot_arr = np.array(bin_pil.rotate(float(a), resample=PIL.Image.Resampling.NEAREST))
        proj = np.sum(rot_arr, axis=1)
        score = float(np.sum(np.diff(proj) ** 2))
        if score > best_fine_score:
            best_fine_score = score
            best_fine_angle = float(a)

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

    return [
        round(min_x * scale, 1),
        round(min_y * scale, 1),
        round(max_x * scale, 1),
        round(max_y * scale, 1)
    ]
