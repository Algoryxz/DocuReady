"""
Document Extraction Pipeline for DocuReady MVP
Extracts structured fields, bounding boxes, and provenance from PDFs and image scans using PyMuPDF and Local Tesseract OCR.
"""

import os
import re
import io
from typing import Dict, Optional, Tuple, List, Any
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
    validate_ifsc_code, normalize_cert_number
)
from docuready.evidence.calibrator import ConfidenceCalibrator, validate_field_syntax
from docuready.ingest.tesseract_discovery import configure_pytesseract

# Configure local Tesseract binary path dynamically
configure_pytesseract()


def detect_document_type(text: str) -> Optional[DocumentType]:
    """Infers document type from raw extracted text headers using anchor verification."""
    classification = classify_document_content(text)
    return classification.candidate_type


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
                    captured = match.group(1).strip()
                    if captured and captured not in [":", "-", "=", ""]:
                        val = captured
                    elif idx + 1 < len(lines):
                        val = lines[idx + 1].strip()
                    else:
                        val = line
                else:
                    if line.rstrip().endswith(":") or "IN FIGURES" in line.upper():
                        val = lines[idx + 1].strip() if idx + 1 < len(lines) else line
                    else:
                        val = line

                rects = page.search_for(val) if val else page.search_for(line)
                bbox = None
                if rects:
                    r = rects[0]
                    bbox = [round(r.x0, 1), round(r.y0, 1), round(r.x1, 1), round(r.y1, 1)]
                snippet = f"{line}" + (f" -> {lines[idx+1]}" if idx + 1 < len(lines) and val != line else "")
                return val, bbox, snippet

    return None, None, ""


class PageOCRData:
    """Holds OCR results, token bounding boxes and line structures for an image page."""
    def __init__(self, raw_data: Dict[str, List[Any]], dpi: int = 200, rotation_applied: int = 0):
        self.dpi = dpi
        self.rotation_applied = rotation_applied
        self.scale = 72.0 / float(dpi)
        self.lines: List[Dict[str, Any]] = []
        self._build_lines(raw_data)

    def _build_lines(self, data: Dict[str, List[Any]]):
        words_meta = []
        n_boxes = len(data.get("text", []))
        for i in range(n_boxes):
            word = str(data["text"][i]).strip()
            conf = float(data["conf"][i])
            if not word or conf < 0:
                continue

            left = data["left"][i] * self.scale
            top = data["top"][i] * self.scale
            right = (data["left"][i] + data["width"][i]) * self.scale
            bottom = (data["top"][i] + data["height"][i]) * self.scale
            words_meta.append({
                "word": word,
                "box": [left, top, right, bottom],
                "conf": conf,
                "x0": left,
                "y0": top
            })

        if not words_meta:
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
    Requires substantive alphanumeric tokens, high mean confidence, and horizontal geometry invariant.
    """
    texts = data.get("text", [])
    confs = data.get("conf", [])
    widths = data.get("width", [])
    heights = data.get("height", [])

    valid_tokens = []
    total_chars = 0
    for text, conf, w, h in zip(texts, confs, widths, heights):
        word = str(text).strip()
        c = float(conf)
        # Require non-empty token, valid confidence, and at least one alphanumeric character
        if word and c >= 0 and any(ch.isalnum() for ch in word):
            valid_tokens.append((word, c, float(w), float(h)))
            total_chars += len(word)

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

    return True


def _ocr_page(page: pymupdf.Page, dpi: int = 200) -> PageOCRData:
    """Renders page to image with direct buffer decoding, fast-path upright verification, auto-orientation fallback, and timeouts."""
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

    # Step 1: Speculative token OCR on initial 0° image
    try:
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, timeout=OCR_TIMEOUT_SECONDS)
    except Exception:
        data = {"text": [], "conf": [], "left": [], "top": [], "width": [], "height": []}

    # Step 2: Conservative Fast-Path check
    # If the page is demonstrably upright with high token confidence and horizontal geometry, skip OSD entirely!
    if _is_demonstrably_upright(data):
        return PageOCRData(data, dpi=dpi, rotation_applied=0)

    # Step 3: Fast-path gate did not pass (tokens < 15, low confidence, or empty).
    # If there are 0 tokens (e.g. blank scan), skip OSD to avoid 'Too few characters' error.
    valid_token_count = sum(1 for w, c in zip(data.get("text", []), data.get("conf", [])) if str(w).strip() and float(c) >= 0)
    if valid_token_count == 0:
        return PageOCRData(data, dpi=dpi, rotation_applied=0)

    # Step 4: Fallback to OSD for orientation recovery on rotated/uncertain pages
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
            rotated_img = img.rotate(360 - rot, expand=True)
            rot_applied = rot
            # Re-run token OCR on the rotated upright image
            try:
                data = pytesseract.image_to_data(rotated_img, output_type=pytesseract.Output.DICT, timeout=OCR_TIMEOUT_SECONDS)
            except Exception:
                pass  # Keep initial data on secondary failure
    except Exception:
        pass  # Graceful fallback: retain initial token data if OSD fails or times out

    return PageOCRData(data, dpi=dpi, rotation_applied=rot_applied)


def _find_field_in_ocr_page(ocr_data: PageOCRData, patterns: List[str]) -> Tuple[Optional[str], Optional[List[float]], str, float, bool, float, int]:
    """
    Searches an OCR page for matching patterns.
    Returns (value, bounding_box, snippet, confidence, label_detected, label_distance_pt, candidate_count)
    """
    matches = []
    seen_values = set()

    for pattern in patterns:
        for idx, line_obj in enumerate(ocr_data.lines):
            line = line_obj["text"]
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                label_detected = True
                label_dist_pt = 0.0

                if match.groups() and match.group(1) is not None:
                    captured = match.group(1).strip()
                    if captured and captured not in [":", "-", "=", ""]:
                        val = captured
                    elif idx + 1 < len(ocr_data.lines):
                        val = ocr_data.lines[idx + 1]["text"].strip()
                        label_dist_pt = abs(ocr_data.lines[idx + 1]["bbox"][1] - line_obj["bbox"][1])
                    else:
                        val = line
                else:
                    if line.rstrip().endswith(":") or "IN FIGURES" in line.upper():
                        if idx + 1 < len(ocr_data.lines):
                            val = ocr_data.lines[idx + 1]["text"].strip()
                            label_dist_pt = abs(ocr_data.lines[idx + 1]["bbox"][1] - line_obj["bbox"][1])
                        else:
                            val = line
                    else:
                        val = line

                # Reject bare label matches
                if val.upper() in [":", "-", "=", "IN FIGURES", "RS.", "RUPEES", ""]:
                    continue

                bbox = line_obj["bbox"]
                snippet = f"{line}" + (f" -> {ocr_data.lines[idx+1]['text']}" if idx + 1 < len(ocr_data.lines) and val != line else "")
                conf = line_obj["confidence"]
                matches.append((val, bbox, snippet, conf, label_detected, label_dist_pt))
                seen_values.add(val.upper())

    if not matches:
        return None, None, "", 0.0, False, 999.0, 0

    candidate_count = len(seen_values)
    # Pick the match with highest confidence and shortest label distance
    best_match = max(matches, key=lambda m: (m[3] - (0.001 * m[5])))
    val, bbox, snippet, conf, lbl_det, lbl_dist = best_match
    return val, bbox, snippet, conf, lbl_det, lbl_dist, candidate_count


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

    def extract_document(self, file_path: str, expected_type: Optional[DocumentType] = None) -> ExtractedDocument:
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
                ocr_pages: List[PageOCRData] = []
                ocr_text_accum = []
                all_confs = []

                for p in doc:
                    p_ocr = _ocr_page(p, dpi=self.dpi)
                    ocr_pages.append(p_ocr)
                    for l in p_ocr.lines:
                        ocr_text_accum.append(l["text"])
                        all_confs.append(l["confidence"])

                raw_text = "\n".join(ocr_text_accum)
                mean_ocr_conf = round(sum(all_confs) / len(all_confs), 3) if all_confs else 0.0

                classification = classify_document_content(raw_text)
                detected_type = classification.candidate_type

                if "ILLEGIBLE" in raw_text.upper() or "ILLEGIBLE" in native_text.upper() or len(raw_text.strip()) < 20 or not all_confs:
                    # Blank scan, unextractable raster, or explicit illegible marker
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

                doc_type = detected_type or expected_type or self._fallback_type(file_name)
                fields = self._parse_fields_ocr(ocr_pages, doc_type, file_name)

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

    def _parse_fields_ocr(self, ocr_pages: List[PageOCRData], doc_type: DocumentType, file_name: str) -> Dict[str, ExtractedField]:
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
                    ocr_confidence=conf
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

        if doc_type == DocumentType.INCOME_CERT:
            add_field_func("applicant_name", [r"certify\s+that\s+([^,]+),", r"Applicant\s*Name\s*[:\-]?(.*)", r"certify\s+that\s+([A-Za-z\s]+)"], normalize_name)
            add_field_func("father_name", [r"Son/Daughter\s+of\s+([^,]+),", r"Father['\s]*s?\s*Name\s*[:\-]?(.*)"], normalize_name)
            add_field_func("annual_income", [r"Annual\s+Family\s+Income\s*\(in\s+figures\)\s*[:\-]?(.*)", r"Annual\s+Family\s+Income[^\n:]*[:\-]?(.*)"], normalize_income)
            add_field_func("issue_date", [r"Issue\s+Date\s*[:\-]?\s*(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})", r"Date\s+of\s+Issue\s*[:\-]?\s*(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})"], parse_dt)
            add_field_func("certificate_no", [r"Certificate\s+No\s*[:\-]?\s*([A-Za-z0-9/\-]+)", r"Cert\s+No\s*[:\-]?\s*([A-Za-z0-9/\-]+)"], normalize_cert_number)
            add_field_func("state", [r"GOVERNMENT\s+OF\s+([^\n]+)", r"State\s+of\s+([^,\n]+)"], lambda s: s.strip().upper() if s else None)

        elif doc_type == DocumentType.CASTE_CERT:
            add_field_func("applicant_name", [r"Applicant\s*Name\s*[:\-]?(.*)", r"certify\s+that\s+([^,]+),", r"certify\s+that\s+([A-Za-z\s]+)"], normalize_name)
            add_field_func("father_name", [r"Son/Daughter\s+of\s+([^,]+),", r"Father['\s]*s?\s*Name\s*[:\-]?(.*)"], normalize_name)
            add_field_func("caste_category", [r"Recognized\s+Category\s*[:\-]?(.*)", r"recognized\s+as\s+a\s+([A-Z/ ]+)\s+under"], lambda s: s.strip().upper() if s else None)
            add_field_func("sub_caste", [r"Sub-Caste[^\n:]*[:\-]?(.*)", r"belongs\s+to\s+the\s+([^\n]+)\s+community"], lambda s: s.strip().upper() if s else None)
            add_field_func("certificate_no", [r"Certificate\s+No\s*[:\-]?\s*([A-Za-z0-9/\-]+)", r"Cert\s+No\s*[:\-]?\s*([A-Za-z0-9/\-]+)"], normalize_cert_number)
            add_field_func("issue_date", [r"Issue\s+Date\s*[:\-]?\s*(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})"], parse_dt)
            add_field_func("state", [r"GOVERNMENT\s+OF\s+([^\n]+)", r"State\s+of\s+([^,\n]+)"], lambda s: s.strip().upper() if s else None)

        elif doc_type == DocumentType.RESIDENCE_CERT:
            add_field_func("applicant_name", [r"Applicant\s*Full\s*Name\s*[:\-]?(.*)", r"certify\s+that\s+([^,]+),", r"Applicant\s*Name\s*[:\-]?(.*)"], normalize_name)
            add_field_func("father_name", [r"Father['\s]*s?\s*/\s*Guardian['\s]*s?\s*Name\s*[:\-]?(.*)", r"Son/Daughter\s+of\s+([^,]+),"], normalize_name)
            add_field_func("state", [r"Domicile\s+State\s*[:\-]?(.*)", r"State\s+of\s+([A-Za-z]+)", r"State\s*[:\-]?(.*)"], lambda s: s.strip().upper() if s else None)
            add_field_func("certificate_no", [r"Certificate\s+No\s*[:\-]?\s*([A-Za-z0-9/\-]+)", r"Cert\s+No\s*[:\-]?\s*([A-Za-z0-9/\-]+)"], normalize_cert_number)
            add_field_func("issue_date", [r"Issue\s+Date\s*[:\-]?\s*(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})"], parse_dt)

        elif doc_type == DocumentType.MARKSHEET:
            add_field_func("applicant_name", [r"Candidate\s+Name\s*[:\-]?(.*)", r"Applicant\s*Name\s*[:\-]?(.*)", r"Name\s*[:\-]?(.*)"], normalize_name)
            add_field_func("father_name", [r"Father['\s]*s?\s*Name\s*[:\-]?(.*)"], normalize_name)
            add_field_func("dob", [r"Date\s+of\s+Birth\s*[:\-]?(.*)", r"DOB\s*[:\-]?(.*)"], parse_dt)
            add_field_func("roll_no", [r"Roll\s+No\s*[:\-]?(.*)"], lambda s: s.strip() if s else None)
            add_field_func("percentage", [r"AGGREGATE\s+RESULT[^\(]*\(([\d.]+)%\)", r"([\d.]+)%"], parse_pct)

        elif doc_type == DocumentType.BANK_PASSBOOK:
            add_field_func("applicant_name", [r"Account\s+Holder\s+Name\s*[:\-]?(.*)", r"Holder\s+Name\s*[:\-]?(.*)", r"Applicant\s*Name\s*[:\-]?(.*)"], normalize_name)
            add_field_func("account_no", [r"Account\s+Number\s*[:\-]?(.*)"], lambda s: s.strip() if s else None)
            add_field_func("ifsc", [r"Bank\s+IFSC\s+Code\s*[:\-]?(.*)", r"IFSC\s*[:\-]?(.*)"], lambda s: s.strip().upper() if s else None)
            add_field_func("dbt_seeded", [r"DBT\s*/\s*Aadhaar\s+Seeding\s*[:\-]?(.*)", r"DBT\s*[:\-]?(.*)"], lambda s: True if s and ("ACTIVE" in s.upper() or "SEEDED" in s.upper()) else False)

        elif doc_type == DocumentType.APPLICATION_FORM:
            add_field_func("applicant_name", [r"Applicant\s+Full\s+Name\s*[:\-]?(.*)", r"Applicant\s*Name\s*[:\-]?(.*)", r"Name\s*[:\-]?(.*)"], normalize_name)
            add_field_func("father_name", [r"Father['\s]*s?\s*/\s*Guardian['\s]*s?\s*Name\s*[:\-]?(.*)"], normalize_name)
            add_field_func("dob", [r"Date\s+of\s+Birth\s*\(DOB\)\s*[:\-]?(.*)"], parse_dt)
            add_field_func("caste_category", [r"Social\s+Category\s*[:\-]?(.*)"], lambda s: s.strip().upper() if s else None)
            add_field_func("annual_income", [r"Declared\s+Annual\s+Family\s+Income\s*[:\-]?(.*)"], normalize_income)
            add_field_func("income_cert_no", [r"Income\s+Certificate\s+Reference\s+No\s*[:\-]?\s*([A-Za-z0-9/\-]+)"], normalize_cert_number)
            add_field_func("caste_cert_no", [r"Caste\s+Certificate\s+Reference\s+No\s*[:\-]?\s*([A-Za-z0-9/\-]+)"], normalize_cert_number)
            add_field_func("residence_cert_no", [r"Residence\s+Certificate\s+Reference\s+No\s*[:\-]?\s*([A-Za-z0-9/\-]+)"], normalize_cert_number)
            add_field_func("account_no", [r"Bank\s+Account\s+Number\s*[:\-]?(.*)"], lambda s: s.strip() if s else None)
            add_field_func("ifsc", [r"Bank\s+IFSC\s+Code\s*[:\-]?(.*)"], lambda s: s.strip().upper() if s else None)
