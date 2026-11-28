"""
Document Extraction Pipeline for DocuReady MVP
Extracts structured fields, bounding boxes, and provenance from PDFs and image scans using PyMuPDF and Local Tesseract OCR.
"""

import os
import re
import io
import math
from typing import Dict, Optional, Tuple, List, Any, Union
import pymupdf
import PIL.Image
import pytesseract

from docuready.ingest.pdf_backend import get_pdf_backend, PDFDocumentBackend, PDFPageBackend
from docuready.ingest.slot_classifier import classify_document_content, SlotClassification

from docuready.domain.models import (
    DocumentType, ExtractedDocument, ExtractedField, EvidenceProvenance,
    ExtractionMethod, EvidenceState
)
from docuready.normalize.normalizer import (
    normalize_name, parse_and_normalize_date, normalize_income,
    validate_ifsc_code, normalize_cert_number, normalize_indic_digits,
)
from docuready.evidence.calibrator import ConfidenceCalibrator, validate_field_syntax
from docuready.ingest.tesseract_discovery import (
    check_ocr_language_availability,
    configure_pytesseract,
    normalize_ocr_langs,
)
from docuready.ingest.deskew import estimate_skew_angle, deskew_image, transform_bbox_inverse

# Configure local Tesseract binary path dynamically
configure_pytesseract()


def detect_document_type(text: str) -> Optional[DocumentType]:
    """Infers document type from raw extracted text headers using anchor verification."""
    classification = classify_document_content(text)
    return classification.candidate_type


def _clean_field_value(v: Optional[str]) -> Optional[str]:
    """Strips table borders (|) and extraneous outer whitespace from captured field values."""
    if not v:
        return v
    s = str(v).strip()
    if "|" in s:
        s = s.strip(" |")
    return s.strip()


def _find_field_in_page_vector(page: pymupdf.Page, patterns: List[str]) -> Tuple[Optional[str], Optional[List[float]], str]:
    """
    Searches a PDF page with native vector text:
    Returns (value, bounding_box [x0, y0, x1, y1], snippet)
    """
    text = page.get_text()
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for pattern in patterns:
        for idx, line in enumerate(lines):
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                if match.groups() and match.group(1) is not None:
                    captured = _clean_field_value(match.group(1))
                    if captured and captured not in [":", "-", "=", "|", ""]:
                        val = captured
                    elif idx + 1 < len(lines):
                        val = _clean_field_value(lines[idx + 1])
                    else:
                        val = _clean_field_value(line)
                else:
                    if line.rstrip().endswith(":") or "IN FIGURES" in line.upper():
                        val = _clean_field_value(lines[idx + 1]) if idx + 1 < len(lines) else _clean_field_value(line)
                    else:
                        val = _clean_field_value(line)

                if not val or val.upper() in [":", "-", "=", "|", "IN FIGURES", "RS.", "RUPEES", ""]:
                    continue

                rects = page.search_for(val) if val else page.search_for(line)
                bbox = None
                if rects:
                    r = rects[0]
                    if hasattr(r, "x0"):
                        bbox = [round(r.x0, 1), round(r.y0, 1), round(r.x1, 1), round(r.y1, 1)]
                    else:
                        bbox = [round(r[0], 1), round(r[1], 1), round(r[2], 1), round(r[3], 1)]
                snippet = f"{line}" + (f" -> {lines[idx+1]}" if idx + 1 < len(lines) and val != line else "")
                return val, bbox, snippet

    return None, None, ""


class PageOCRData:
    """Holds OCR results, token bounding boxes and line structures for an image page."""
    def __init__(
        self,
        raw_data: Dict[str, List[Any]],
        dpi: int = 200,
        rotation_applied: int = 0,
        ocr_lang: Optional[str] = None,
        ocr_error: Optional[str] = None,
        skew_angle: float = 0.0,
        orig_size: Optional[Tuple[int, int]] = None,
        rot_size: Optional[Tuple[int, int]] = None
    ):
        self.dpi = dpi
        self.rotation_applied = rotation_applied
        self.ocr_lang = ocr_lang
        self.ocr_error = ocr_error
        self.skew_angle = skew_angle
        self.orig_size = orig_size
        self.rot_size = rot_size
        self.scale = 72.0 / float(dpi)
        self.lines: List[Dict[str, Any]] = []
        self._build_lines(raw_data)

    def _build_lines(self, data: Dict[str, List[Any]]):
        words_meta = []
        n_boxes = len(data.get("text", []))
        transform_angle = self.skew_angle
        has_transform = abs(transform_angle) > 1e-4 and self.orig_size is not None and self.rot_size is not None

        for i in range(n_boxes):
            word = str(data["text"][i]).strip()
            conf = float(data["conf"][i])
            if not word or conf < 0:
                continue

            left_px = float(data["left"][i])
            top_px = float(data["top"][i])
            right_px = left_px + float(data["width"][i])
            bottom_px = top_px + float(data["height"][i])

            if has_transform:
                orig_box = transform_bbox_inverse(
                    [left_px, top_px, right_px, bottom_px],
                    transform_angle,
                    self.orig_size,
                    self.rot_size,
                    scale=self.scale
                )
            else:
                orig_box = [
                    round(left_px * self.scale, 1),
                    round(top_px * self.scale, 1),
                    round(right_px * self.scale, 1),
                    round(bottom_px * self.scale, 1)
                ]

            words_meta.append({
                "word": word,
                "box": orig_box,
                "conf": conf,
                # Cluster in the horizontal deskewed coordinate frame
                "x0": left_px * self.scale,
                "y0": top_px * self.scale
            })

        if not words_meta:
            return

        # Column-aware spatial reconstruction
        from docuready.ingest.spatial_layout import cluster_and_order_words
        column_groups = cluster_and_order_words(words_meta)
        if column_groups is not None:
            for group in column_groups:
                words = [wm["word"] for wm in group]
                boxes = [wm["box"] for wm in group]
                confs = [wm["conf"] for wm in group]
                self._commit_line(words, boxes, confs)
            return

        from itertools import groupby
        words_meta.sort(key=lambda w: (round(w["y0"] / 12.0) * 12.0, w["x0"]))
        for _, group in groupby(words_meta, key=lambda w: round(w["y0"] / 12.0) * 12.0):
            line_words_meta = list(group)
            line_words_meta.sort(key=lambda w: w["x0"])
            words = [wm["word"] for wm in line_words_meta]
            boxes = [wm["box"] for wm in line_words_meta]
            confs = [wm["conf"] for wm in line_words_meta]
            self._commit_line(words, boxes, confs)

    def _commit_line(self, words: List[str], boxes: List[List[float]], confs: List[float]):
        text = " ".join(words)
        x0 = round(min(b[0] for b in boxes), 1)
        y0 = round(min(b[1] for b in boxes), 1)
        x1 = round(max(b[2] for b in boxes), 1)
        y1 = round(max(b[3] for b in boxes), 1)
        mean_conf = round(sum(confs) / (len(confs) * 100.0), 3)  # Scale to 0.0 - 1.0
        self.lines.append({
            "text": text,
            "bbox": [x0, y0, x1, y1],
            "confidence": mean_conf,
            "words": words,
            "word_boxes": boxes,
            "word_confs": confs
        })


MAX_PDF_PAGES = 50
MAX_PIXEL_DIMENSION = 5000
OCR_TIMEOUT_SECONDS = 15
OSD_TIMEOUT_SECONDS = 4

# Fast-path verification gate thresholds
OSD_FAST_PATH_MIN_TOKENS = 15
OSD_FAST_PATH_MIN_CHARS = 40
OSD_FAST_PATH_MIN_MEAN_CONF = 70.0
OSD_FAST_PATH_MIN_HIGH_CONF_RATIO = 0.60
OSD_FAST_PATH_MIN_HORIZ_RATIO = 0.70
OSD_FAST_PATH_HIGH_CONF_THRESH = 60.0


def _is_demonstrably_upright(data: Dict[str, List[Any]]) -> bool:
    """
    Evaluates whether token OCR results from an unrotated page demonstrably confirm upright orientation.
    Requires substantive alphanumeric tokens, high mean confidence, horizontal aspect ratio,
    and a strictly horizontal baseline slope (|median_slope| < 1.5°).
    """
    texts = data.get("text", [])
    confs = data.get("conf", [])
    lefts = data.get("left", [])
    tops = data.get("top", [])
    widths = data.get("width", [])
    heights = data.get("height", [])
    line_nums = data.get("line_num", [])
    block_nums = data.get("block_num", [])

    valid_tokens = []
    total_chars = 0
    token_positions = []

    for i in range(len(texts)):
        word = str(texts[i]).strip()
        c = float(confs[i])
        # Require non-empty token, valid confidence, and at least one alphanumeric character
        if word and c >= 0 and any(ch.isalnum() for ch in word):
            w = float(widths[i])
            h = float(heights[i])
            valid_tokens.append((word, c, w, h))
            total_chars += len(word)
            b = block_nums[i] if i < len(block_nums) else 0
            l = line_nums[i] if i < len(line_nums) else 0
            x = float(lefts[i]) if i < len(lefts) else 0.0
            y = float(tops[i]) if i < len(tops) else 0.0
            token_positions.append((b, l, x, y, w, h))

    total_tokens = len(valid_tokens)
    if total_tokens < OSD_FAST_PATH_MIN_TOKENS or total_chars < OSD_FAST_PATH_MIN_CHARS:
        return False

    mean_conf = sum(t[1] for t in valid_tokens) / total_tokens
    if mean_conf < OSD_FAST_PATH_MIN_MEAN_CONF:
        return False

    high_conf_count = sum(1 for t in valid_tokens if t[1] >= OSD_FAST_PATH_HIGH_CONF_THRESH)
    if (high_conf_count / total_tokens) < OSD_FAST_PATH_MIN_HIGH_CONF_RATIO:
        return False

    # Check horizontal aspect ratio: upright text lines in Latin/Devanagari/Odia have width >= height
    horizontal_count = sum(1 for t in valid_tokens if t[2] >= t[3])
    if (horizontal_count / total_tokens) < OSD_FAST_PATH_MIN_HORIZ_RATIO:
        return False

    # Baseline slope invariant: on an upright page, adjacent words on a line must be horizontal
    slopes = []
    for i in range(len(token_positions) - 1):
        b1, l1, x1, y1, w1, h1 = token_positions[i]
        b2, l2, x2, y2, w2, h2 = token_positions[i + 1]
        if b1 == b2 and l1 == l2 and x2 > x1 + (w1 * 0.3):
            dx = x2 - x1
            dy = y2 - y1
            angle_deg = math.degrees(math.atan2(dy, dx))
            slopes.append(angle_deg)

    if len(slopes) >= 5:
        slopes.sort()
        med_slope = slopes[len(slopes) // 2]
        if abs(med_slope) >= 1.5:
            return False

    return True


def extract_token_baseline_slope(data: dict, min_pairs: int = 3) -> Optional[float]:
    """
    Computes the median baseline slope in degrees from adjacent words in pytesseract image_to_data dict.
    Returns None if fewer than min_pairs adjacent horizontal tokens exist.
    """
    texts = data.get("text", [])
    confs = data.get("conf", [])
    lefts = data.get("left", [])
    tops = data.get("top", [])
    widths = data.get("width", [])
    heights = data.get("height", [])
    line_nums = data.get("line_num", [])
    block_nums = data.get("block_num", [])

    token_positions = []
    for i in range(len(texts)):
        word = str(texts[i]).strip()
        c = float(confs[i]) if i < len(confs) else -1.0
        if word and c >= 25.0 and any(ch.isalnum() for ch in word):
            b = block_nums[i] if i < len(block_nums) else 0
            l = line_nums[i] if i < len(line_nums) else 0
            x = float(lefts[i]) if i < len(lefts) else 0.0
            y = float(tops[i]) if i < len(tops) else 0.0
            w = float(widths[i]) if i < len(widths) else 0.0
            h = float(heights[i]) if i < len(heights) else 0.0
            token_positions.append((b, l, x, y, w, h))

    slopes = []
    for i in range(len(token_positions) - 1):
        b1, l1, x1, y1, w1, h1 = token_positions[i]
        b2, l2, x2, y2, w2, h2 = token_positions[i + 1]
        if b1 == b2 and l1 == l2 and x2 > x1 + (w1 * 0.3):
            dx = x2 - x1
            dy = y2 - y1
            angle_deg = math.degrees(math.atan2(dy, dx))
            if -45.0 <= angle_deg <= 45.0:
                slopes.append(angle_deg)

    if len(slopes) >= min_pairs:
        slopes.sort()
        med = slopes[len(slopes) // 2]
        return round(med, 2)
    return None


def _ocr_page(page: pymupdf.Page, dpi: int = 200, preferred_lang: Optional[str] = None, lang: Optional[str] = None) -> PageOCRData:
    """Renders page to image with direct buffer decoding, fast-path upright verification, deskew recovery, auto-orientation fallback, and timeouts."""
    effective_lang = lang or preferred_lang or "eng"
    lang_to_use = normalize_ocr_langs(effective_lang)
    rect = page.rect
    # Security check: Page bomb protection against excessive dimensions
    if rect.width > MAX_PIXEL_DIMENSION or rect.height > MAX_PIXEL_DIMENSION:
        # Fallback to standard 72 DPI to avoid memory explosion
        pix = page.get_pixmap(dpi=72)
    else:
        pix = page.get_pixmap(dpi=dpi)

    try:
        # Direct buffer access: eliminates BytesIO + PNG encode/decode overhead (~25-30ms)
        img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    except Exception:
        img = PIL.Image.open(io.BytesIO(pix.tobytes()))
    finally:
        pix = None  # Free native C pixmap memory immediately

    rot_applied = 0
    orig_size = (img.width, img.height)
    rot_size = (img.width, img.height)

    ocr_error: Optional[str] = None
    # Step 1: Speculative token OCR on initial 0° image
    try:
        data = pytesseract.image_to_data(img, lang=lang_to_use, output_type=pytesseract.Output.DICT, timeout=OCR_TIMEOUT_SECONDS)
    except Exception as exc:
        data = {"text": [], "conf": [], "left": [], "top": [], "width": [], "height": []}
        ocr_error = f"Local OCR execution failed for language '{lang_to_use}': {type(exc).__name__}"

    # Step 2: Conservative Fast-Path check
    # If the page is demonstrably upright with high token confidence and horizontal geometry, skip OSD and deskew!
    if _is_demonstrably_upright(data):
        return PageOCRData(data, dpi=dpi, rotation_applied=0, ocr_lang=lang_to_use, ocr_error=ocr_error)

    # Step 3: Skew Analysis & Recovery for non-orthogonal rotations
    try:
        hint_angle = extract_token_baseline_slope(data)
        corr_angle, skew_conf = estimate_skew_angle(img, max_angle=45.0, hint_angle=hint_angle)
        if abs(corr_angle) >= 1.0 and skew_conf >= 5.0:
            deskewed_img, o_sz, r_sz = deskew_image(img, corr_angle)
            deskew_data = pytesseract.image_to_data(
                deskewed_img,
                lang=lang_to_use,
                output_type=pytesseract.Output.DICT,
                timeout=OCR_TIMEOUT_SECONDS
            )
            deskew_valid_count = sum(1 for w, c in zip(deskew_data.get("text", []), deskew_data.get("conf", [])) if str(w).strip() and float(c) >= 0)
            initial_valid_count = sum(1 for w, c in zip(data.get("text", []), data.get("conf", [])) if str(w).strip() and float(c) >= 0)
            if _is_demonstrably_upright(deskew_data) or deskew_valid_count > initial_valid_count:
                return PageOCRData(
                    deskew_data,
                    dpi=dpi,
                    rotation_applied=0,
                    ocr_lang=lang_to_use,
                    ocr_error=ocr_error,
                    skew_angle=corr_angle,
                    orig_size=o_sz,
                    rot_size=r_sz
                )
    except Exception:
        pass

    # Step 4: If not deskewed, check if there are 0 valid tokens (e.g. blank scan), skip OSD to avoid 'Too few characters' error.
    valid_token_count = sum(1 for w, c in zip(data.get("text", []), data.get("conf", [])) if str(w).strip() and float(c) >= 0)
    if valid_token_count == 0:
        return PageOCRData(data, dpi=dpi, rotation_applied=0, ocr_lang=lang_to_use, ocr_error=ocr_error)

    # Step 5: Fallback to OSD for orthogonal orientation recovery on 90°, 180°, 270° pages
    try:
        rot = None
        # Tier A: Fast downsampled OSD (0.60x) saves ~25-30% compute time on rotated scans
        try:
            target_size = (int(img.width * 0.60), int(img.height * 0.60))
            small_img = img.resize(target_size, PIL.Image.Resampling.BILINEAR)
            osd = pytesseract.image_to_osd(small_img, timeout=OSD_TIMEOUT_SECONDS)
            rot_match = [line for line in osd.split("\n") if "Rotate:" in line]
            if rot_match:
                r = int(rot_match[0].split(":")[1].strip())
                if r in [90, 180, 270]:
                    rot = r
        except Exception:
            pass

        # Tier B: Full-resolution OSD fallback if Tier A did not detect an orthogonal rotation
        if rot is None:
            osd = pytesseract.image_to_osd(img, timeout=OSD_TIMEOUT_SECONDS)
            rot_match = [line for line in osd.split("\n") if "Rotate:" in line]
            if rot_match:
                r = int(rot_match[0].split(":")[1].strip())
                if r in [90, 180, 270]:
                    rot = r

        if rot in [90, 180, 270]:
            rotated_img = img.rotate(360 - rot, expand=True, fillcolor=(255, 255, 255))
            rot_applied = rot
            orig_size = (img.width, img.height)
            rot_size = (rotated_img.width, rotated_img.height)
            # Re-run token OCR on the rotated upright image
            try:
                data = pytesseract.image_to_data(rotated_img, lang=lang_to_use, output_type=pytesseract.Output.DICT, timeout=OCR_TIMEOUT_SECONDS)
            except Exception:
                pass  # Keep initial data on secondary failure
    except Exception:
        pass  # Graceful fallback: retain initial token data if OSD fails or times out

    return PageOCRData(
        data,
        dpi=dpi,
        rotation_applied=rot_applied,
        ocr_lang=lang_to_use,
        ocr_error=ocr_error,
        skew_angle=0.0
    )


def _find_field_in_ocr_page(ocr_data: PageOCRData, patterns: List[str]) -> Tuple[Optional[str], Optional[List[float]], str, float, bool, float, int]:
    """
    Searches an OCR page for matching patterns.
    Returns (value, bounding_box, snippet, confidence, label_detected, label_distance_pt, candidate_count)
    """
    line_best_matches = {}  # idx -> (score, (val, bbox, snippet, conf, lbl_det, lbl_dist))
    seen_canonical_values = set()

    for pattern in patterns:
        for idx, line_obj in enumerate(ocr_data.lines):
            line = line_obj["text"]
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                label_detected = True
                label_dist_pt = 0.0

                if match.groups() and match.group(1) is not None:
                    captured = _clean_field_value(match.group(1))
                    if captured and captured not in [":", "-", "=", "|", ""]:
                        val = captured
                    elif idx + 1 < len(ocr_data.lines):
                        val = _clean_field_value(ocr_data.lines[idx + 1]["text"])
                        label_dist_pt = abs(ocr_data.lines[idx + 1]["bbox"][1] - line_obj["bbox"][1])
                    else:
                        val = _clean_field_value(line)
                else:
                    if line.rstrip().endswith(":") or "IN FIGURES" in line.upper():
                        if idx + 1 < len(ocr_data.lines):
                            val = _clean_field_value(ocr_data.lines[idx + 1]["text"])
                            label_dist_pt = abs(ocr_data.lines[idx + 1]["bbox"][1] - line_obj["bbox"][1])
                        else:
                            val = _clean_field_value(line)
                    else:
                        val = _clean_field_value(line)

                # Reject bare label matches
                if not val or val.upper() in [":", "-", "=", "|", "IN FIGURES", "RS.", "RUPEES", ""]:
                    continue

                bbox = line_obj["bbox"]
                next_text = ocr_data.lines[idx + 1]["text"] if idx + 1 < len(ocr_data.lines) else ""
                snippet = f"{line}" + (f" -> {next_text}" if idx + 1 < len(ocr_data.lines) and val != line else "")
                conf = line_obj["confidence"]
                score = conf - (0.001 * label_dist_pt)

                # Canonical representation for equivalence check
                canon_val = re.sub(r'[\s\|\:\-\=/,.]', '', normalize_indic_digits(val).upper())
                if canon_val:
                    seen_canonical_values.add(canon_val)

                # Keep best matching extraction on this line
                if idx not in line_best_matches or score > line_best_matches[idx][0]:
                    line_best_matches[idx] = (score, (val, bbox, snippet, conf, label_detected, label_dist_pt))

    if not line_best_matches:
        return None, None, "", 0.0, False, 999.0, 0

    candidate_count = len(seen_canonical_values)
    best_match = max(line_best_matches.values(), key=lambda item: item[0])[1]
    val, bbox, snippet, conf, lbl_det, lbl_dist = best_match
    return val, bbox, snippet, conf, lbl_det, lbl_dist, candidate_count


def get_slot_ocr_langs(
    pack: Any,
    expected_type: Optional[DocumentType],
) -> Optional[List[str]]:
    """Resolve configured ocr_langs for a document type from a loaded PackManifest."""
    if pack is None or expected_type is None or not getattr(pack, "doc_slots", None):
        return None
    from docuready.rules.primitives import resolve_doc_type

    for slot_name, slot_def in pack.doc_slots.items():
        if resolve_doc_type(slot_name) == expected_type:
            langs = getattr(slot_def, "ocr_langs", None)
            return list(langs) if langs else None
    return None

class DocumentExtractor:
    """Extracts typed fields and provenance from supported document formats using native text and local OCR."""

    def __init__(
        self,
        dpi: int = 200,
        low_conf_threshold: float = 0.70,
        tau_abstain: float = 0.45,
        operating_mode: str = "CALIBRATED_LABEL_AWARE"
    ):
        self.dpi = dpi
        self.low_conf_threshold = low_conf_threshold
        self.tau_abstain = tau_abstain
        self.operating_mode = operating_mode
        self.calibrator = ConfidenceCalibrator(tau_high=low_conf_threshold, tau_abstain=tau_abstain)

    def extract_document(
        self,
        file_path: str,
        expected_type: Optional[DocumentType] = None,
        ocr_langs: Optional[Union[str, List[str]]] = None,
    ) -> ExtractedDocument:
        file_name = os.path.basename(file_path)
        if not os.path.exists(file_path):
            return ExtractedDocument(
                doc_type=expected_type or DocumentType.APPLICATION_FORM,
                file_path=file_path,
                status="MISSING",
                extraction_method=ExtractionMethod.UNEXTRACTED.value,
                expected_slot=expected_type,
            )

        # Security check: verify PDF header
        try:
            with open(file_path, "rb") as f_check:
                header = f_check.read(10)
                if file_name.lower().endswith(".pdf") and not header.startswith(b"%PDF-"):
                    return ExtractedDocument(
                        doc_type=expected_type or DocumentType.APPLICATION_FORM,
                        file_path=file_path,
                        status="CORRUPTED",
                        extraction_method=ExtractionMethod.UNEXTRACTED.value,
                        expected_slot=expected_type,
                    )
        except Exception:
            return ExtractedDocument(
                doc_type=expected_type or DocumentType.APPLICATION_FORM,
                file_path=file_path,
                status="CORRUPTED",
                extraction_method=ExtractionMethod.UNEXTRACTED.value,
                expected_slot=expected_type,
            )

        backend_doc = None
        doc = None
        try:
            try:
                backend_doc = get_pdf_backend(file_path)
                doc = getattr(backend_doc, "raw_doc", backend_doc)
                if getattr(doc, "needs_pass", False) or getattr(doc, "is_encrypted", False):
                    return ExtractedDocument(
                        doc_type=expected_type or DocumentType.APPLICATION_FORM,
                        file_path=file_path,
                        status="UNREADABLE",
                        extraction_method=ExtractionMethod.UNEXTRACTED.value,
                        expected_slot=expected_type,
                    )
            except Exception:
                return ExtractedDocument(
                    doc_type=expected_type or DocumentType.APPLICATION_FORM,
                    file_path=file_path,
                    status="CORRUPTED",
                    extraction_method=ExtractionMethod.UNEXTRACTED.value,
                    expected_slot=expected_type,
                )

            try:
                page_count = len(doc)
            except Exception:
                return ExtractedDocument(
                    doc_type=expected_type or DocumentType.APPLICATION_FORM,
                    file_path=file_path,
                    status="CORRUPTED",
                    extraction_method=ExtractionMethod.UNEXTRACTED.value,
                    expected_slot=expected_type,
                )

            if page_count == 0 or page_count > MAX_PDF_PAGES:
                return ExtractedDocument(
                    doc_type=expected_type or DocumentType.APPLICATION_FORM,
                    file_path=file_path,
                    status="UNREADABLE",
                    extraction_method=ExtractionMethod.UNEXTRACTED.value,
                    expected_slot=expected_type,
                )

            # 1. Inspect native text across all pages
            native_text = ""
            try:
                for p in doc:
                    native_text += p.get_text() + "\n"
            except Exception:
                return ExtractedDocument(
                    doc_type=expected_type or DocumentType.APPLICATION_FORM,
                    file_path=file_path,
                    status="UNREADABLE",
                    extraction_method=ExtractionMethod.UNEXTRACTED.value,
                    expected_slot=expected_type,
                )

            # Check if native text is sufficiently dense and readable
            has_native_text = len(native_text.strip()) >= 30 and "ILLEGIBLE" not in native_text.upper()

            if has_native_text:
                extraction_method = ExtractionMethod.NATIVE_VECTOR
                raw_text = native_text
                mean_ocr_conf = None
                classification = classify_document_content(raw_text)
                detected_type = classification.candidate_type
                doc_type = detected_type or expected_type or self._fallback_type(file_name)
                fields = self._parse_fields_vector(doc, doc_type, file_name)
            else:
                # 2. Trigger Local OCR fallback
                extraction_method = ExtractionMethod.LOCAL_OCR
                if ocr_langs is not None:
                    doc_ocr_lang = normalize_ocr_langs(ocr_langs)
                elif native_text and len(native_text.strip()) >= 15:
                    from docuready.ingest.script_router import detect_unicode_script
                    doc_ocr_lang = detect_unicode_script(native_text)["detected_lang"]
                else:
                    doc_ocr_lang = "eng"

                # Verify requested language pack availability when Tesseract binary is present
                if ocr_langs is not None:
                    avail = check_ocr_language_availability(doc_ocr_lang)
                    if avail["binary_available"] and avail["missing_langs"]:
                        return ExtractedDocument(
                            doc_type=expected_type or self._fallback_type(file_name),
                            file_path=file_path,
                            status="UNREADABLE",
                            raw_text="",
                            page_count=page_count,
                            extraction_method=extraction_method.value,
                            mean_ocr_confidence=0.0,
                            expected_slot=expected_type,
                            ocr_lang=doc_ocr_lang,
                            classification_details={
                                "ocr_error": avail["error"],
                                "missing_ocr_langs": avail["missing_langs"],
                            },
                        )

                ocr_pages: List[PageOCRData] = []
                ocr_text_accum = []
                all_confs = []

                for p in doc:
                    p_ocr = _ocr_page(p, dpi=self.dpi, preferred_lang=doc_ocr_lang)
                    ocr_pages.append(p_ocr)
                    for l in p_ocr.lines:
                        ocr_text_accum.append(l["text"])
                        all_confs.append(l["confidence"])

                ocr_errors = [p_ocr.ocr_error for p_ocr in ocr_pages if p_ocr.ocr_error]
                raw_text = "\n".join(ocr_text_accum)
                mean_ocr_conf = round(sum(all_confs) / len(all_confs), 3) if all_confs else 0.0

                classification = classify_document_content(raw_text)
                detected_type = classification.candidate_type

                if ocr_errors or "ILLEGIBLE" in raw_text.upper() or "ILLEGIBLE" in native_text.upper() or len(raw_text.strip()) < 20 or not all_confs:
                    # Blank scan, unextractable raster, missing traineddata, or explicit illegible marker
                    cls_details = {
                        "is_confident": classification.is_confident,
                        "is_uncertain": classification.is_uncertain,
                        "uncertainty_reason": classification.uncertainty_reason,
                        "primary_anchors": classification.primary_anchors,
                        "corroborating_terms": classification.corroborating_terms,
                        "conflicting_types": [dt.value for dt in classification.conflicting_types],
                        "source_lines": classification.source_lines,
                    }
                    if ocr_errors:
                        cls_details["ocr_error"] = ocr_errors[0]
                    return ExtractedDocument(
                        doc_type=detected_type or expected_type or self._fallback_type(file_name),
                        file_path=file_path,
                        status="UNREADABLE",
                        raw_text=raw_text,
                        page_count=page_count,
                        extraction_method=extraction_method.value,
                        mean_ocr_confidence=mean_ocr_conf,
                        expected_slot=expected_type,
                        detected_type=detected_type,
                        ocr_lang=doc_ocr_lang,
                        classification_details=cls_details,
                    )

                doc_type = detected_type or expected_type or self._fallback_type(file_name)
                fields = self._parse_fields_ocr(ocr_pages, doc_type, file_name, ocr_lang=doc_ocr_lang)

            return ExtractedDocument(
                doc_type=doc_type,
                file_path=file_path,
                status="VALID",
                fields=fields,
                raw_text=raw_text,
                page_count=page_count,
                extraction_method=extraction_method.value,
                mean_ocr_confidence=mean_ocr_conf,
                expected_slot=expected_type,
                detected_type=detected_type,
                ocr_lang=doc_ocr_lang if extraction_method == ExtractionMethod.LOCAL_OCR else None,
                classification_details={
                    "is_confident": classification.is_confident,
                    "is_uncertain": classification.is_uncertain,
                    "uncertainty_reason": classification.uncertainty_reason,
                    "primary_anchors": classification.primary_anchors,
                    "corroborating_terms": classification.corroborating_terms,
                    "conflicting_types": [dt.value for dt in classification.conflicting_types],
                    "source_lines": classification.source_lines,
                },
            )
        finally:
            if doc is not None and hasattr(doc, "close"):
                try:
                    doc.close()
                except Exception:
                    pass
            if backend_doc is not None and hasattr(backend_doc, "close") and backend_doc is not doc:
                try:
                    backend_doc.close()
                except Exception:
                    pass
            try:
                pymupdf.TOOLS.store_shrink(100)
            except Exception:
                pass

    def _fallback_type(self, file_name: str) -> DocumentType:
        fn_upper = file_name.upper()
        if "INCOME" in fn_upper:
            return DocumentType.INCOME_CERT
        elif "CASTE" in fn_upper:
            return DocumentType.CASTE_CERT
        elif "RESIDENCE" in fn_upper:
            return DocumentType.RESIDENCE_CERT
        elif "MARKSHEET" in fn_upper:
            return DocumentType.MARKSHEET
        elif "PASSBOOK" in fn_upper:
            return DocumentType.BANK_PASSBOOK
        elif "APPLICATION" in fn_upper:
            return DocumentType.APPLICATION_FORM
        elif "AADHAAR" in fn_upper:
            return DocumentType.AADHAAR
        return DocumentType.APPLICATION_FORM

    def _parse_fields_vector(self, doc: pymupdf.Document, doc_type: DocumentType, file_name: str) -> Dict[str, ExtractedField]:
        fields: Dict[str, ExtractedField] = {}

        def search_all_pages(patterns: List[str]):
            for p_idx, page in enumerate(doc):
                val, bbox, snip = _find_field_in_page_vector(page, patterns)
                if val:
                    return val, bbox, snip, p_idx + 1
            return None, None, "", 1

        def add_f(field_name: str, patterns: List[str], norm_func=None):
            val, bbox, snip, p_num = search_all_pages(patterns)
            if val:
                norm_val = norm_func(val) if norm_func else val
                is_ambig = False
                if "date" in field_name or field_name == "dob":
                    _, _, is_ambig = parse_and_normalize_date(val)

                cal_res = self.calibrator.calibrate(
                    field_name=field_name,
                    raw_value=val,
                    extraction_method=ExtractionMethod.NATIVE_VECTOR,
                    page_has_date_ambiguity=is_ambig
                )

                prov = EvidenceProvenance(
                    document_type=doc_type.value,
                    file_name=file_name,
                    page_number=p_num,
                    bounding_box=bbox,
                    raw_snippet=snip,
                    extracted_field=field_name,
                    extraction_method=ExtractionMethod.NATIVE_VECTOR.value,
                    ocr_confidence=None  # Do not invent confidence for native vector
                )
                fields[field_name] = ExtractedField(
                    field_name=field_name,
                    raw_value=val,
                    normalized_value=norm_val,
                    confidence=1.0,
                    extraction_method=ExtractionMethod.NATIVE_VECTOR.value,
                    evidence_state=cal_res["evidence_state"],
                    calibrated_confidence=cal_res["calibrated_confidence"],
                    raw_ocr_token_confidence=None,
                    supporting_tokens_count=len(val.split()),
                    label_detected=True,
                    label_distance_pt=0.0,
                    candidate_count=1,
                    format_valid=cal_res["format_valid"],
                    provenance=prov,
                    is_uncertain=cal_res["is_uncertain"],
                    uncertainty_reason=cal_res["uncertainty_reason"]
                )

        self._dispatch_type_patterns(doc_type, add_f)
        return fields

    def _parse_fields_ocr(
        self,
        ocr_pages: List[PageOCRData],
        doc_type: DocumentType,
        file_name: str,
        ocr_lang: str = "eng",
    ) -> Dict[str, ExtractedField]:
        fields: Dict[str, ExtractedField] = {}

        def search_all_ocr_pages(patterns: List[str]):
            for p_idx, p_data in enumerate(ocr_pages):
                val, bbox, snip, conf, lbl_det, lbl_dist, cand_count = _find_field_in_ocr_page(p_data, patterns)
                if val:
                    return val, bbox, snip, conf, lbl_det, lbl_dist, cand_count, p_idx + 1
            return None, None, "", 0.0, False, 999.0, 0, 1

        def add_f(field_name: str, patterns: List[str], norm_func=None):
            val, bbox, snip, conf, lbl_det, lbl_dist, cand_count, p_num = search_all_ocr_pages(patterns)
            if val:
                norm_val = norm_func(val) if norm_func else val
                is_ambig = False
                if "date" in field_name or field_name == "dob":
                    _, _, is_ambig = parse_and_normalize_date(val)

                supporting_toks = len(val.split())
                cal_res = self.calibrator.calibrate(
                    field_name=field_name,
                    raw_value=val,
                    extraction_method=ExtractionMethod.LOCAL_OCR,
                    token_confidence=conf,
                    label_detected=lbl_det,
                    label_distance_pt=lbl_dist,
                    candidate_count=cand_count,
                    supporting_tokens_count=supporting_toks,
                    page_has_date_ambiguity=is_ambig
                )

                # Operating mode check
                if self.operating_mode == "CONSERVATIVE_ABSTAIN":
                    if cal_res["calibrated_confidence"] < 0.85:
                        # Abstain from emitting uncertain value
                        return
                elif self.operating_mode == "CALIBRATED_LABEL_AWARE":
                    if cal_res["calibrated_confidence"] < self.tau_abstain or not cal_res["format_valid"]:
                        # Abstain from noisy/invalid values
                        return

                prov = EvidenceProvenance(
                    document_type=doc_type.value,
                    file_name=file_name,
                    page_number=p_num,
                    bounding_box=bbox,
                    raw_snippet=snip,
                    extracted_field=field_name,
                    extraction_method=ExtractionMethod.LOCAL_OCR.value,
                    ocr_confidence=conf,
                    ocr_lang=ocr_lang,
                )
                fields[field_name] = ExtractedField(
                    field_name=field_name,
                    raw_value=val,
                    normalized_value=norm_val,
                    confidence=conf,
                    extraction_method=ExtractionMethod.LOCAL_OCR.value,
                    evidence_state=cal_res["evidence_state"],
                    calibrated_confidence=cal_res["calibrated_confidence"],
                    raw_ocr_token_confidence=conf,
                    supporting_tokens_count=supporting_toks,
                    label_detected=lbl_det,
                    label_distance_pt=lbl_dist,
                    candidate_count=cand_count,
                    format_valid=cal_res["format_valid"],
                    provenance=prov,
                    is_uncertain=cal_res["is_uncertain"],
                    uncertainty_reason=cal_res["uncertainty_reason"]
                )

        self._dispatch_type_patterns(doc_type, add_f)
        return fields

    def _dispatch_type_patterns(self, doc_type: DocumentType, add_field_func):
        """Maps canonical document types to regex extractors and normalization routines."""
        def parse_dt(v):
            dt, st, amb = parse_and_normalize_date(v)
            return str(dt) if dt else v

        def parse_pct(v):
            try:
                return float(re.search(r"[\d.]+", v).group(0)) if v else None
            except Exception:
                return None

        def norm_ident(v):
            return normalize_indic_digits(v).strip() if v else None

        def norm_ifsc(v):
            return normalize_indic_digits(v).strip().upper() if v else None

        cert_chars = r"A-Za-z0-9\u0B66-\u0B6F\u0966-\u096F/\-"

        if doc_type == DocumentType.INCOME_CERT:
            add_field_func("applicant_name", [r"certify\s+that\s+([^,]+),", r"Applicant\s*Name\s*[:\|\-]?(.*)", r"certify\s+that\s+([A-Za-z\s]+?)(?:,|\s+(?:Son|Daughter|Son/Daughter|S/o|D/o|W/o)\b|\s+resident|\s+residing|\s+R/o|$)", r"Name\s*[:\|\-]?(.*)"], normalize_name)
            add_field_func("father_name", [r"Son/Daughter\s+of\s+([^,]+),", r"(?:Son/Daughter|Son|Daughter)\s+of\s+([A-Za-z\s]+?)(?:,|\s+resident|\s+residing|\s+R/o|$)", r"(?:S/o|D/o|W/o)\s*(?:of|/o)?\s*[:\|\-]?\s*([A-Za-z\s]+?)(?:,|\s+resident|\s+residing|\s+R/o|$)", r"Father['\s]*s?\s*Name\s*[:\|\-]?(.*)"], normalize_name)
            add_field_func("annual_income", [r"(?:Annual\s+)?(?:Family\s+)?Income\s*\(in\s+figures\)\s*[:\-]?(.*)", r"Annual\s+Family\s+Income\s*\(in\s+figures\)\s*[:\-]?(.*)", r"(?:Total\s+Annual|Annual\s+Family|Total\s+Family|Total|Annual)\s+(?:Family\s+)?Income[^\n:|]*[:\|\-]\s*(.*)", r"Annual\s+Family\s+Income[^\n:]*[:\-]?(.*)", r"(?:Total|Annual)\s+Income\s*[:\|\-]\s*(.*)"], normalize_income)
            add_field_func("issue_date", [r"Issue\s+Date\s*[:\-]?\s*(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})", r"Date\s+of\s+Issue\s*[:\-]?\s*(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})", r"(?:Issue\s+Date|Date\s+of\s+Issue|Date)\s*[:\|\-]?\s*([0-9]{1,4}[/\.\-\s]+[A-Za-z0-9]{1,9}[/\.\-\s]+[0-9]{2,4})"], parse_dt)
            add_field_func("certificate_no", [rf"Certificate\s+No\s*[:\-]?\s*([{cert_chars}]+)", rf"Cert\s+No\s*[:\-]?\s*([{cert_chars}]+)", rf"Certificate\s+(?:No|Number)\s*[:\|\-]?\s*([{cert_chars}]+)"], normalize_cert_number)
            add_field_func("state", [r"GOVERNMENT\s+OF\s+([^\n]+)", r"State\s+of\s+([^,\n]+)"], lambda s: s.strip().upper() if s else None)

        elif doc_type == DocumentType.CASTE_CERT:
            add_field_func("applicant_name", [r"Applicant\s*Name\s*[:\|\-]?(.*)", r"certify\s+that\s+([^,]+),", r"certify\s+that\s+([A-Za-z\s]+?)(?:,|\s+(?:Son|Daughter|Son/Daughter|S/o|D/o|W/o)\b|\s+resident|\s+residing|\s+R/o|$)", r"Name\s*[:\|\-]?(.*)"], normalize_name)
            add_field_func("father_name", [r"Son/Daughter\s+of\s+([^,]+),", r"(?:Son/Daughter|Son|Daughter)\s+of\s+([A-Za-z\s]+?)(?:,|\s+resident|\s+residing|\s+R/o|$)", r"(?:S/o|D/o|W/o)\s*(?:of|/o)?\s*[:\|\-]?\s*([A-Za-z\s]+?)(?:,|\s+resident|\s+residing|\s+R/o|$)", r"Father['\s]*s?\s*Name\s*[:\|\-]?(.*)"], normalize_name)
            add_field_func("caste_category", [r"Recognized\s+Category\s*[:\-]?(.*)", r"recognized\s+as\s+a\s+([A-Z/ ]+)\s+under"], lambda s: s.strip().upper() if s else None)
            add_field_func("sub_caste", [r"Sub-Caste[^\n:]*[:\-]?(.*)", r"belongs\s+to\s+the\s+([^\n]+)\s+community"], lambda s: s.strip().upper() if s else None)
            add_field_func("certificate_no", [rf"Certificate\s+No\s*[:\-]?\s*([{cert_chars}]+)", rf"Cert\s+No\s*[:\-]?\s*([{cert_chars}]+)", rf"Certificate\s+(?:No|Number)\s*[:\|\-]?\s*([{cert_chars}]+)"], normalize_cert_number)
            add_field_func("issue_date", [r"Issue\s+Date\s*[:\-]?\s*(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})", r"(?:Issue\s+Date|Date\s+of\s+Issue|Date)\s*[:\|\-]?\s*([0-9]{1,4}[/\.\-\s]+[A-Za-z0-9]{1,9}[/\.\-\s]+[0-9]{2,4})"], parse_dt)
            add_field_func("state", [r"GOVERNMENT\s+OF\s+([^\n]+)", r"State\s+of\s+([^,\n]+)"], lambda s: s.strip().upper() if s else None)

        elif doc_type == DocumentType.RESIDENCE_CERT:
            add_field_func("applicant_name", [r"Applicant\s*Full\s*Name\s*[:\|\-]?(.*)", r"certify\s+that\s+([^,]+),", r"Applicant\s*Name\s*[:\|\-]?(.*)", r"Name\s*[:\|\-]?(.*)"], normalize_name)
            add_field_func("father_name", [r"Father['\s]*s?\s*/\s*Guardian['\s]*s?\s*Name\s*[:\|\-]?(.*)", r"Son/Daughter\s+of\s+([^,]+),", r"(?:Son/Daughter|Son|Daughter)\s+of\s+([A-Za-z\s]+?)(?:,|\s+resident|\s+residing|\s+R/o|$)", r"(?:S/o|D/o|W/o)\s*(?:of|/o)?\s*[:\|\-]?\s*([A-Za-z\s]+?)(?:,|\s+resident|\s+residing|\s+R/o|$)", r"Father['\s]*s?\s*Name\s*[:\|\-]?(.*)"], normalize_name)
            add_field_func("state", [r"Domicile\s+State\s*[:\|\-]?(.*)", r"State\s+of\s+([A-Za-z]+)", r"State\s*[:\|\-]?(.*)"], lambda s: s.strip().upper() if s else None)
            add_field_func("certificate_no", [rf"Certificate\s+No\s*[:\-]?\s*([{cert_chars}]+)", rf"Cert\s+No\s*[:\-]?\s*([{cert_chars}]+)", rf"Certificate\s+(?:No|Number)\s*[:\|\-]?\s*([{cert_chars}]+)"], normalize_cert_number)
            add_field_func("issue_date", [r"Issue\s+Date\s*[:\-]?\s*(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})", r"(?:Issue\s+Date|Date\s+of\s+Issue|Date)\s*[:\|\-]?\s*([0-9]{1,4}[/\.\-\s]+[A-Za-z0-9]{1,9}[/\.\-\s]+[0-9]{2,4})"], parse_dt)

        elif doc_type == DocumentType.MARKSHEET:
            add_field_func("applicant_name", [r"Candidate\s+Name\s*[:\-]?(.*)", r"Applicant\s*Name\s*[:\-]?(.*)", r"Name\s*[:\-]?(.*)"], normalize_name)
            add_field_func("father_name", [r"Father['\s]*s?\s*Name\s*[:\-]?(.*)", r"(?:S/o|D/o|W/o)\s*[:\-]?\s*([A-Za-z\s]+)"], normalize_name)
            add_field_func("dob", [r"Date\s+of\s+Birth\s*[:\-]?(.*)", r"DOB\s*[:\-]?(.*)", r"(?:Date\s+of\s+Birth|DOB)\s*[:\-]?\s*([0-9]{1,4}[/\.\-\s]+[A-Za-z0-9]{1,9}[/\.\-\s]+[0-9]{2,4})"], parse_dt)
            add_field_func("roll_no", [r"Roll\s+No\s*[:\-]?(.*)"], norm_ident)
            add_field_func("percentage", [r"AGGREGATE\s+RESULT[^\(]*\(([\d.]+)%\)", r"([\d.]+)%"], parse_pct)

        elif doc_type == DocumentType.BANK_PASSBOOK:
            add_field_func("applicant_name", [r"Account\s+Holder\s+Name\s*[:\-]?(.*)", r"Holder\s+Name\s*[:\-]?(.*)", r"Applicant\s*Name\s*[:\-]?(.*)"], normalize_name)
            add_field_func("account_no", [r"Account\s+Number\s*[:\-]?(.*)"], norm_ident)
            add_field_func("ifsc", [r"Bank\s+IFSC\s+Code\s*[:\-]?(.*)", r"IFSC\s*[:\-]?(.*)"], norm_ifsc)
            add_field_func("dbt_seeded", [r"DBT\s*/\s*Aadhaar\s+Seeding\s*[:\-]?(.*)", r"DBT\s*[:\-]?(.*)"], lambda s: True if s and ("ACTIVE" in s.upper() or "SEEDED" in s.upper()) else False)

        elif doc_type == DocumentType.APPLICATION_FORM:
            add_field_func("applicant_name", [r"Applicant\s+Full\s+Name\s*[:\-]?(.*)", r"Applicant\s*Name\s*[:\-]?(.*)", r"Name\s*[:\-]?(.*)"], normalize_name)
            add_field_func("father_name", [r"Father['\s]*s?\s*/\s*Guardian['\s]*s?\s*Name\s*[:\-]?(.*)", r"Father['\s]*s?\s*Name\s*[:\-]?(.*)", r"(?:S/o|D/o|W/o)\s*[:\-]?\s*([A-Za-z\s]+)"], normalize_name)
            add_field_func("dob", [r"Date\s+of\s+Birth\s*\(DOB\)\s*[:\-]?(.*)", r"Date\s+of\s+Birth\s*[:\-]?(.*)", r"DOB\s*[:\-]?(.*)"], parse_dt)
            add_field_func("caste_category", [r"Social\s+Category\s*[:\-]?(.*)"], lambda s: s.strip().upper() if s else None)
            add_field_func("annual_income", [r"Declared\s+Annual\s+Family\s+Income\s*[:\-]?(.*)", r"(?:Total\s+)?(?:Annual\s+)?(?:Family\s+)?Income\s*[:\|\-]\s*(.*)"], normalize_income)
            add_field_func("income_cert_no", [rf"Income\s+Certificate\s+Reference\s+No\s*[:\-]?\s*([{cert_chars}]+)", rf"(?:Income\s+)?Certificate\s+(?:Reference\s+)?(?:No|Number)\s*[:\|\-]?\s*([{cert_chars}]+)"], normalize_cert_number)
            add_field_func("caste_cert_no", [rf"Caste\s+Certificate\s+Reference\s+No\s*[:\-]?\s*([{cert_chars}]+)"], normalize_cert_number)
            add_field_func("residence_cert_no", [rf"Residence\s+Certificate\s+Reference\s+No\s*[:\-]?\s*([{cert_chars}]+)"], normalize_cert_number)
            add_field_func("account_no", [r"Bank\s+Account\s+Number\s*[:\-]?(.*)", r"Account\s+Number\s*[:\-]?(.*)"], norm_ident)
            add_field_func("ifsc", [r"Bank\s+IFSC\s+Code\s*[:\-]?(.*)", r"IFSC\s*[:\-]?(.*)"], norm_ifsc)

        elif doc_type == DocumentType.AADHAAR:
            add_field_func("applicant_name", [r"Government\s+of\s+India[^\n]*\n\s*([A-Za-z\s]+)", r"Name\s*[:\-]?\s*([A-Za-z\s]+)", r"To\s*[:\-]?\s*([A-Za-z\s]+)", r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"], normalize_name)
            add_field_func("dob", [r"(?:DOB|Date\s+of\s+Birth|Year\s+of\s+Birth)\s*[:\-]?\s*([0-9]{1,4}[/\.\-\s]+[A-Za-z0-9]{1,9}[/\.\-\s]+[0-9]{2,4})"], parse_dt)
            add_field_func("gender", [r"\b(MALE|FEMALE|TRANSGENDER)\b"], lambda s: s.strip().upper() if s else None)
            add_field_func("aadhaar_no", [r"([X\d]{4}\s+[X\d]{4}\s+\d{4})", r"(\d{4}\s+\d{4}\s+\d{4})"], lambda s: re.sub(r'\s+', '', s) if s else None)
            add_field_func("aadhaar_no", [r"([X\d]{4}\s+[X\d]{4}\s+\d{4})", r"(\d{4}\s+\d{4}\s+\d{4})"], lambda s: re.sub(r'\s+', '', s) if s else None)
