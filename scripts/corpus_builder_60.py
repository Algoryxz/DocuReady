"""
Realistic Document Corpus Builder for DocuReady Loop 2
Compiles 60 diverse document samples with optical, photographic, and structural degradations:
- Clean vector PDFs
- Raster image scanned PDFs (zero selectable vector text)
- Rotated scans (deskew challenges)
- Low-resolution scans (72 DPI, 50 DPI)
- Mobile-camera perspective distortion (OpenCV warp)
- Uneven lighting, shadows & glare
- JPEG compression artifacts
- Faint/partially obscured text
- Stamps and overlapping tahsil seals
- Multi-page documents
- Handwritten annotations
- Alternative layouts & regional formats
- Blank and corrupted files
"""

import os
import io
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import pymupdf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4

from docuready.domain.models import DocumentType
from docuready.generator import (
    generate_income_certificate, generate_caste_certificate,
    generate_residence_certificate, generate_marksheet,
    generate_bank_passbook, generate_application_form
)

CORPUS_DIR = "synthetic_data/realistic_corpus_60"
MANIFEST_FILE = "synthetic_data/REALISTIC_CORPUS_MANIFEST.json"


def _render_pdf_to_image(pdf_path: str, dpi: int = 200) -> Image.Image:
    """Renders page 0 of a PDF into a PIL Image."""
    doc = pymupdf.open(pdf_path)
    page = doc[0]
    pix = page.get_pixmap(dpi=dpi)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    return img


def _save_image_as_scanned_pdf(img: Image.Image, output_pdf_path: str):
    """Saves a PIL image as a pure raster scanned PDF (no selectable text)."""
    os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=85)
    img_byte_arr.seek(0)

    # Use PyMuPDF to create a clean PDF with only an embedded image
    pdf_doc = pymupdf.open()
    rect = pymupdf.Rect(0, 0, img.width * 72 / 200, img.height * 72 / 200)
    page = pdf_doc.new_page(width=rect.width, height=rect.height)
    page.insert_image(rect, stream=img_byte_arr.getvalue())
    pdf_doc.save(output_pdf_path)
    pdf_doc.close()


def apply_rotation(img: Image.Image, angle_degrees: float) -> Image.Image:
    """Rotates image with white background."""
    return img.rotate(angle_degrees, expand=True, fillcolor=(255, 255, 255))


def apply_low_resolution(img: Image.Image, factor: float = 0.35) -> Image.Image:
    """Downscales and upscales to simulate low-DPI scan."""
    w, h = img.size
    small = img.resize((int(w * factor), int(h * factor)), resample=Image.Resampling.BILINEAR)
    return small.resize((w, h), resample=Image.Resampling.NEAREST)


def apply_perspective_distortion(img: Image.Image) -> Image.Image:
    """Simulates mobile camera snapshot taken at an angle using OpenCV."""
    np_img = np.array(img)
    h, w = np_img.shape[:2]
    pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
    # Shift top corners inward to simulate tilted smartphone camera
    dx = int(w * 0.12)
    dy = int(h * 0.08)
    pts2 = np.float32([[dx, dy], [w - dx, dy], [0, h], [w, h]])
    M = cv2.getPerspectiveTransform(pts1, pts2)
    warped = cv2.warpPerspective(np_img, M, (w, h), borderValue=(245, 245, 245))
    return Image.fromarray(warped)


def apply_shadow_and_uneven_lighting(img: Image.Image) -> Image.Image:
    """Simulates uneven desk lamp lighting / smartphone shadow."""
    np_img = np.array(img).astype(np.float32)
    h, w = np_img.shape[:2]
    # Linear gradient shadow from bottom-right to top-left
    x = np.linspace(1.0, 0.45, w)
    y = np.linspace(1.0, 0.55, h)
    xx, yy = np.meshgrid(x, y)
    mask = xx * yy
    mask = np.dstack([mask, mask, mask])
    shaded = np_img * mask
    shaded = np.clip(shaded, 0, 255).astype(np.uint8)
    return Image.fromarray(shaded)


def apply_heavy_jpeg_compression(img: Image.Image, quality: int = 15) -> Image.Image:
    """Simulates WhatsApp / low-bandwidth mobile compression artifacts."""
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return Image.open(buf)


def apply_overlapping_seal(img: Image.Image, position: str = "middle") -> Image.Image:
    """Simulates official purple/magenta revenue round stamp overlapping text."""
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    cx, cy = (w // 2, h // 2) if position == "middle" else (w // 3, h // 3)
    radius = int(w * 0.14)
    # Draw circular concentric seals with purple ink
    seal_color = (130, 20, 140, 110) # Semi-transparent purple
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=seal_color, width=4)
    draw.ellipse([cx - radius + 10, cy - radius + 10, cx + radius - 10, cy + radius - 10], outline=seal_color, width=2)
    draw.text((cx - radius + 20, cy - 10), "TAHSILDAR * GOVT OF ODISHA *", fill=seal_color)
    draw.text((cx - 30, cy + 15), "SEAL", fill=seal_color)

    base = img.convert("RGBA")
    combined = Image.alpha_composite(base, overlay)
    return combined.convert("RGB")


def apply_handwritten_annotations(img: Image.Image) -> Image.Image:
    """Simulates ink pen marginal notes and endorsement signatures."""
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    ink_color = (20, 30, 160, 180) # Blue ballpoint ink
    draw.line([(w * 0.7, h * 0.85), (w * 0.88, h * 0.83), (w * 0.85, h * 0.87)], fill=ink_color, width=3)
    draw.text((int(w * 0.65), int(h * 0.81)), "Verified with Tahsil RoR - RI 14/2", fill=ink_color)
    draw.text((int(w * 0.08), int(h * 0.12)), "Case No: 9942/2025", fill=ink_color)
    base = img.convert("RGBA")
    combined = Image.alpha_composite(base, overlay)
    return combined.convert("RGB")


def build_realistic_corpus():
    os.makedirs(CORPUS_DIR, exist_ok=True)
    manifest = {
        "corpus_name": "DocuReady Realistic Document Scans Corpus (Loop 2)",
        "total_samples": 60,
        "date_created": "2026-11-13",
        "description": "60 multi-condition applicant documents with controlled optical, perspective and physical degradations.",
        "samples": {}
    }

    # Reference standard data
    base_tmp = os.path.join(CORPUS_DIR, "_tmp_clean")
    os.makedirs(base_tmp, exist_ok=True)

    # 1. Generate base clean vector documents
    inc_base = os.path.join(base_tmp, "inc.pdf")
    cst_base = os.path.join(base_tmp, "cst.pdf")
    res_base = os.path.join(base_tmp, "res.pdf")
    mrk_base = os.path.join(base_tmp, "mrk.pdf")
    bnk_base = os.path.join(base_tmp, "bnk.pdf")
    app_base = os.path.join(base_tmp, "app.pdf")

    generate_income_certificate(inc_base, "Smruti Ranjan Nayak", "Ramesh Chandra Nayak", "Rs. 1,80,000/-", "10/01/2025", "E-INC/2025/104928")
    generate_caste_certificate(cst_base, "Smruti Ranjan Nayak", "Ramesh Chandra Nayak", "SEBC", "Chasa", "12/03/2024", "CST/2025/88192")
    generate_residence_certificate(res_base, "Smruti Ranjan Nayak", "Ramesh Chandra Nayak", "Plot 104, Saheed Nagar, Bhubaneswar", "ODISHA", "15/01/2025", "RES/2025/99812")
    generate_marksheet(mrk_base, "Smruti Ranjan Nayak", "Ramesh Chandra Nayak", "14/05/2003", "2309BA1042", 78.5)
    generate_bank_passbook(bnk_base, "Smruti Ranjan Nayak", "30987654301", "SBIN0001234")
    generate_application_form(app_base, "Smruti Ranjan Nayak", "Ramesh Chandra Nayak", "14/05/2003", "Rs. 1,80,000/-", "SEBC",
                              income_cert_no="E-INC/2025/104928", caste_cert_no="CST/2025/88192", residence_cert_no="RES/2025/99812",
                              account_no="30987654301", ifsc="SBIN0001234")

    # Group definitions
    def add_meta(sid, doc_type, gen_method, degradation, expected_extraction, expected_status, file_name, fields):
        manifest["samples"][sid] = {
            "sample_id": sid,
            "document_type": doc_type,
            "file_name": file_name,
            "generation_method": gen_method,
            "degradation_applied": degradation,
            "expected_extraction": expected_extraction,
            "expected_audit_status": expected_status,
            "expected_fields": fields
        }

    sample_counter = 1

    # Tier 1: Clean Vector PDFs (10 samples)
    clean_pairs = [
        (DocumentType.INCOME_CERT, inc_base),
        (DocumentType.CASTE_CERT, cst_base),
        (DocumentType.RESIDENCE_CERT, res_base),
        (DocumentType.MARKSHEET, mrk_base),
        (DocumentType.BANK_PASSBOOK, bnk_base),
        (DocumentType.APPLICATION_FORM, app_base),
        (DocumentType.INCOME_CERT, inc_base),
        (DocumentType.CASTE_CERT, cst_base),
        (DocumentType.MARKSHEET, mrk_base),
        (DocumentType.APPLICATION_FORM, app_base)
    ]
    for dt, src_pdf in clean_pairs:
        sid = f"SMP_{sample_counter:02d}"
        fn = f"{sid.lower()}_{dt.value.lower()}_clean.pdf"
        dst = os.path.join(CORPUS_DIR, fn)
        with open(src_pdf, "rb") as f_in, open(dst, "wb") as f_out:
            f_out.write(f_in.read())
        add_meta(sid, dt.value, "ReportLab Vector", "None (Clean Digital Vector)", "NATIVE_VECTOR", "PASS", fn,
                 {"applicant_name": "SMRUTI RANJAN NAYAK"})
        sample_counter += 1

    # Tier 2: Clean Raster Scanned PDFs (8 samples, 200 DPI, zero vector text)
    raster_sources = [inc_base, cst_base, res_base, mrk_base, bnk_base, app_base, inc_base, mrk_base]
    for src_pdf in raster_sources:
        sid = f"SMP_{sample_counter:02d}"
        img = _render_pdf_to_image(src_pdf, dpi=200)
        fn = f"{sid.lower()}_raster_scan.pdf"
        dst = os.path.join(CORPUS_DIR, fn)
        _save_image_as_scanned_pdf(img, dst)
        add_meta(sid, "SCAN_DOCUMENT", "Raster Scanned", "Raster Image at 200 DPI (Zero Selectable Vector Text)", "LOCAL_OCR", "PASS", fn,
                 {"applicant_name": "SMRUTI RANJAN NAYAK"})
        sample_counter += 1

    # Tier 3: Rotated Scans (6 samples: 2, -3, 5, -5, 90, 180 degrees)
    rotations = [2.0, -3.0, 5.0, -4.5, 90.0, 180.0]
    for deg in rotations:
        sid = f"SMP_{sample_counter:02d}"
        img = _render_pdf_to_image(inc_base, dpi=200)
        rot_img = apply_rotation(img, deg)
        fn = f"{sid.lower()}_rotated_{int(deg)}deg.pdf"
        dst = os.path.join(CORPUS_DIR, fn)
        _save_image_as_scanned_pdf(rot_img, dst)
        exp_ext = "LOCAL_OCR" if abs(deg) <= 5.0 else "UNEXTRACTED_OR_OCR"
        exp_st = "PASS" if abs(deg) <= 5.0 else "REVIEW"
        add_meta(sid, "INCOME_CERT", "Raster Rotated", f"Skewed/Rotated by {deg} degrees", exp_ext, exp_st, fn,
                 {"applicant_name": "SMRUTI RANJAN NAYAK"})
        sample_counter += 1

    # Tier 4: Low-Resolution Scans (6 samples: 75 DPI downscale)
    low_res_sources = [inc_base, mrk_base, cst_base, bnk_base, app_base, res_base]
    for src_pdf in low_res_sources:
        sid = f"SMP_{sample_counter:02d}"
        img = _render_pdf_to_image(src_pdf, dpi=200)
        low_img = apply_low_resolution(img, factor=0.35)
        fn = f"{sid.lower()}_low_dpi.pdf"
        dst = os.path.join(CORPUS_DIR, fn)
        _save_image_as_scanned_pdf(low_img, dst)
        add_meta(sid, "DEGRADED_SCAN", "Raster Low-Res", "Downsampled to 70 DPI equivalent with pixel blur", "LOCAL_OCR", "REVIEW", fn,
                 {"applicant_name": "SMRUTI RANJAN NAYAK"})
        sample_counter += 1

    # Tier 5: Mobile-Camera Perspective Distortion (6 samples)
    perspective_sources = [inc_base, mrk_base, app_base, bnk_base, cst_base, res_base]
    for src_pdf in perspective_sources:
        sid = f"SMP_{sample_counter:02d}"
        img = _render_pdf_to_image(src_pdf, dpi=200)
        warp_img = apply_perspective_distortion(img)
        fn = f"{sid.lower()}_mobile_perspective.pdf"
        dst = os.path.join(CORPUS_DIR, fn)
        _save_image_as_scanned_pdf(warp_img, dst)
        add_meta(sid, "MOBILE_PHOTO", "Perspective Skew", "Smartphone trapezoidal perspective warp angle", "LOCAL_OCR", "REVIEW", fn,
                 {"applicant_name": "SMRUTI RANJAN NAYAK"})
        sample_counter += 1

    # Tier 6: Uneven Lighting & Shadows (6 samples)
    lighting_sources = [inc_base, mrk_base, cst_base, bnk_base, app_base, res_base]
    for src_pdf in lighting_sources:
        sid = f"SMP_{sample_counter:02d}"
        img = _render_pdf_to_image(src_pdf, dpi=200)
        shadow_img = apply_shadow_and_uneven_lighting(img)
        fn = f"{sid.lower()}_shadow_gradient.pdf"
        dst = os.path.join(CORPUS_DIR, fn)
        _save_image_as_scanned_pdf(shadow_img, dst)
        add_meta(sid, "SHADOWED_SCAN", "Non-uniform Lighting", "Desk lamp lighting gradient with 45% shadow", "LOCAL_OCR", "REVIEW", fn,
                 {"applicant_name": "SMRUTI RANJAN NAYAK"})
        sample_counter += 1

    # Tier 7: JPEG Compression Artifacts (4 samples, quality=15)
    jpeg_sources = [inc_base, mrk_base, bnk_base, app_base]
    for src_pdf in jpeg_sources:
        sid = f"SMP_{sample_counter:02d}"
        img = _render_pdf_to_image(src_pdf, dpi=200)
        jpeg_img = apply_heavy_jpeg_compression(img, quality=15)
        fn = f"{sid.lower()}_jpeg_artifacts.pdf"
        dst = os.path.join(CORPUS_DIR, fn)
        _save_image_as_scanned_pdf(jpeg_img, dst)
        add_meta(sid, "COMPRESSED_FILE", "Lossy Compression", "Severe JPEG quantization ringing artifacts (Q=15)", "LOCAL_OCR", "REVIEW", fn,
                 {"applicant_name": "SMRUTI RANJAN NAYAK"})
        sample_counter += 1

    # Tier 8: Stamps & Overlapping Seals (4 samples)
    seal_sources = [inc_base, cst_base, res_base, mrk_base]
    for src_pdf in seal_sources:
        sid = f"SMP_{sample_counter:02d}"
        img = _render_pdf_to_image(src_pdf, dpi=200)
        seal_img = apply_overlapping_seal(img, position="middle")
        fn = f"{sid.lower()}_overlapping_seal.pdf"
        dst = os.path.join(CORPUS_DIR, fn)
        _save_image_as_scanned_pdf(seal_img, dst)
        add_meta(sid, "STAMPED_CERT", "Sealed Physical", "Revenue round stamp ink overlapping demographic text", "LOCAL_OCR", "REVIEW", fn,
                 {"applicant_name": "SMRUTI RANJAN NAYAK"})
        sample_counter += 1

    # Tier 9: Handwritten Annotations (4 samples)
    hand_sources = [inc_base, mrk_base, app_base, bnk_base]
    for src_pdf in hand_sources:
        sid = f"SMP_{sample_counter:02d}"
        img = _render_pdf_to_image(src_pdf, dpi=200)
        hand_img = apply_handwritten_annotations(img)
        fn = f"{sid.lower()}_handwritten_annotations.pdf"
        dst = os.path.join(CORPUS_DIR, fn)
        _save_image_as_scanned_pdf(hand_img, dst)
        add_meta(sid, "ANNOTATED_DOC", "Physical Markup", "Ink ballpoint pen verification marks and marginal notes", "LOCAL_OCR", "PASS", fn,
                 {"applicant_name": "SMRUTI RANJAN NAYAK"})
        sample_counter += 1

    # Tier 10: Multi-page & Alternative Layouts (4 samples)
    for i in range(1, 5):
        sid = f"SMP_{sample_counter:02d}"
        fn = f"{sid.lower()}_multipage_layout_{i}.pdf"
        dst = os.path.join(CORPUS_DIR, fn)
        c = canvas.Canvas(dst, pagesize=letter)
        # Page 1
        c.drawString(100, 750, f"GOVERNMENT OF ODISHA - WELFARE PORTAL CERTIFICATE #{i}")
        c.drawString(100, 730, "SECTION A: GENERAL PREAMBLE AND NOTIFICATION")
        c.drawString(100, 700, "Statutory authority under Section 4(b)")
        c.showPage()
        # Page 2
        c.drawString(100, 750, "SECTION B: APPLICANT DEMOGRAPHIC RECORD")
        c.drawString(100, 720, "Applicant Name: Smruti Ranjan Nayak")
        c.drawString(100, 690, "Father's Name: Ramesh Chandra Nayak")
        c.drawString(100, 660, "Date of Birth: 14/05/2003")
        c.drawString(100, 630, "Annual Family Income: 1,80,000")
        c.drawString(100, 600, "Certificate No: MULTI-PAGE-2025-9912")
        c.showPage()
        c.save()
        add_meta(sid, "INCOME_CERT", "Multi-Page ReportLab", "Two-page document with demographics on page 2", "NATIVE_VECTOR", "PASS", fn,
                 {"applicant_name": "SMRUTI RANJAN NAYAK", "annual_income": 180000.0})
        sample_counter += 1

    # Tier 11: Blank & Corrupted Files (2 samples: 59 and 60)
    # 59: Blank page PDF
    sid_59 = f"SMP_{sample_counter:02d}"
    fn_59 = f"{sid_59.lower()}_blank_scan.pdf"
    dst_59 = os.path.join(CORPUS_DIR, fn_59)
    c_blank = canvas.Canvas(dst_59, pagesize=letter)
    c_blank.showPage()
    c_blank.save()
    add_meta(sid_59, "BLANK_PAGE", "Zero Content", "Completely blank page with zero text or graphics", "UNEXTRACTED", "UNKNOWN", fn_59, {})
    sample_counter += 1

    # 60: Truncated corrupted binary PDF
    sid_60 = f"SMP_{sample_counter:02d}"
    fn_60 = f"{sid_60.lower()}_corrupted_header.pdf"
    dst_60 = os.path.join(CORPUS_DIR, fn_60)
    with open(dst_60, "wb") as f_bad:
        f_bad.write(b"%PDF-1.4 TruncatedCorruptedHeaderPayload\x00\xff\xfe\xca\xfe")
    add_meta(sid_60, "CORRUPTED_STREAM", "Corrupt Bytes", "Non-PDF corrupted byte sequence", "UNEXTRACTED", "UNKNOWN", fn_60, {})

    with open(MANIFEST_FILE, "w", encoding="utf-8") as f_out:
        json.dump(manifest, f_out, indent=2)

    print(f"Generated {len(manifest['samples'])} realistic document samples in '{CORPUS_DIR}'.")
    return manifest


if __name__ == "__main__":
    build_realistic_corpus()
