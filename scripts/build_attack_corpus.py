"""
scripts/build_attack_corpus.py

Generates dedicated adversarial attack test fixtures for DocuReady Loop 02:
1. atk_01_skew_10deg.pdf: 10° rotated scan
2. atk_02_skew_15deg.pdf: 15° rotated scan
3. atk_03_mixed_orientation.pdf: Upright header + 90° rotated body
4. atk_04_sparse_receipt.pdf: Sparse page with < 15 tokens
5. atk_05_blank_with_noise_dots.pdf: Blank scan with noise specks
6. atk_06_inverted_reversible_words.pdf: 180° page with palindromic/reversible words
7. atk_07_vertical_column_numbers.pdf: Upright page with single-char vertical column (width < height)
8. atk_08_landscape_table_90deg.pdf: 90° rotated table with horizontal border rules
9. atk_09_heavy_gaussian_blur.pdf: Heavy Gaussian blur
10. atk_10_extreme_shadow_corner.pdf: Extreme contrast degradation
"""
import io
import os
import random
from pathlib import Path
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFilter
import PIL.ImageFont
import pymupdf

ATTACK_DIR = Path("synthetic_data/attack_corpus")
ATTACK_DIR.mkdir(parents=True, exist_ok=True)

CORPUS_DIR = Path("synthetic_data/realistic_corpus_60")
BASE_SCAN = CORPUS_DIR / "smp_11_raster_scan.pdf"


def _render_pdf(path: Path) -> PIL.Image.Image:
    doc = pymupdf.open(str(path))
    pix = doc[0].get_pixmap(dpi=200)
    img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    return img


def _save_as_pdf(img: PIL.Image.Image, output_path: Path):
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    doc = pymupdf.open()
    rect = pymupdf.Rect(0, 0, img.width * 72.0 / 200.0, img.height * 72.0 / 200.0)
    page = doc.new_page(width=rect.width, height=rect.height)
    page.insert_image(rect, stream=buf.getvalue())
    doc.save(str(output_path))
    doc.close()


def generate_all():
    print(f"Generating attack corpus in {ATTACK_DIR}...")
    base_img = _render_pdf(BASE_SCAN)
    w, h = base_img.size

    # 1. 10° skew
    img_10 = base_img.rotate(10.0, expand=True, fillcolor=(255, 255, 255))
    _save_as_pdf(img_10, ATTACK_DIR / "atk_01_skew_10deg.pdf")

    # 2. 15° skew
    img_15 = base_img.rotate(15.0, expand=True, fillcolor=(255, 255, 255))
    _save_as_pdf(img_15, ATTACK_DIR / "atk_02_skew_15deg.pdf")

    # 3. Mixed orientation: Upright header + 90° rotated body
    mixed_img = PIL.Image.new("RGB", (w, h), (255, 255, 255))
    draw = PIL.ImageDraw.Draw(mixed_img)
    # Header in upright
    draw.text((100, 100), "GOVERNMENT OF ODISHA - REVENUE DEPARTMENT", fill=(0, 0, 0))
    draw.text((100, 150), "OFFICIAL INCOME CERTIFICATE CITIZEN COPY", fill=(0, 0, 0))
    # Body rotated 90 degrees
    body_crop = base_img.crop((100, 300, w - 100, h - 200))
    body_rot = body_crop.rotate(90, expand=True, fillcolor=(255, 255, 255))
    mixed_img.paste(body_rot, (100, 250))
    _save_as_pdf(mixed_img, ATTACK_DIR / "atk_03_mixed_orientation.pdf")

    # 4. Sparse receipt (< 15 tokens)
    sparse_img = PIL.Image.new("RGB", (w, h), (255, 255, 255))
    draw_s = PIL.ImageDraw.Draw(sparse_img)
    draw_s.text((200, 200), "TOKEN FEE RECEIPT", fill=(0, 0, 0))
    draw_s.text((200, 300), "AMOUNT: RS 50", fill=(0, 0, 0))
    draw_s.text((200, 400), "DATE: 12/01/2025", fill=(0, 0, 0))
    _save_as_pdf(sparse_img, ATTACK_DIR / "atk_04_sparse_receipt.pdf")

    # 5. Blank with noise specks
    noise_img = PIL.Image.new("RGB", (w, h), (255, 255, 255))
    draw_n = PIL.ImageDraw.Draw(noise_img)
    random.seed(42)
    for _ in range(60):
        nx = random.randint(50, w - 50)
        ny = random.randint(50, h - 50)
        draw_n.ellipse([nx, ny, nx + random.randint(2, 6), ny + random.randint(2, 6)], fill=(50, 50, 50))
    _save_as_pdf(noise_img, ATTACK_DIR / "atk_05_blank_with_noise_dots.pdf")

    # 6. Inverted reversible words (180° upside-down)
    rev_img = PIL.Image.new("RGB", (w, h), (255, 255, 255))
    draw_r = PIL.ImageDraw.Draw(rev_img)
    reversible_text = [
        "NOW POD NO ON DIP SWIMS MOW WOW NOON",
        "SOS OSD 609 906 888 XXX ZZZ HHH III",
        "MOW NOON SWIM DIP POD NOW ON NO WOW",
        "609 888 906 SOS OSD HHH III XXX ZZZ",
        "THIS IS A CERTIFIED INVERTED WORD TEST",
    ]
    y_pos = 300
    for line in reversible_text:
        draw_r.text((150, y_pos), line, fill=(0, 0, 0))
        y_pos += 120
    # Invert by 180 degrees
    rev_img_180 = rev_img.rotate(180, expand=True, fillcolor=(255, 255, 255))
    _save_as_pdf(rev_img_180, ATTACK_DIR / "atk_06_inverted_reversible_words.pdf")

    # 7. Vertical column of single-character codes (height > width tokens)
    vert_img = PIL.Image.new("RGB", (w, h), (255, 255, 255))
    draw_v = PIL.ImageDraw.Draw(vert_img)
    draw_v.text((200, 100), "OFFICIAL SERIAL CODE LIST", fill=(0, 0, 0))
    y_pos = 200
    for char in ["A", "B", "C", "D", "E", "F", "1", "2", "3", "4", "5", "6", "7", "8", "9", "X", "Y", "Z"]:
        draw_v.text((250, y_pos), char, fill=(0, 0, 0))
        y_pos += 60
    _save_as_pdf(vert_img, ATTACK_DIR / "atk_07_vertical_column_numbers.pdf")

    # 8. Landscape table rotated 90° with prominent horizontal gridlines
    table_img = PIL.Image.new("RGB", (w, h), (255, 255, 255))
    draw_t = PIL.ImageDraw.Draw(table_img)
    draw_t.text((150, 150), "ANNUAL INCOME SCHEDULE ASSESSMENT TABLE", fill=(0, 0, 0))
    # Draw table gridlines
    for r in range(10):
        ry = 250 + r * 100
        draw_t.line([(100, ry), (w - 100, ry)], fill=(0, 0, 0), width=4)
        draw_t.text((120, ry + 20), f"ROW {r+1} INCOME RECORD DETAILS VALUE VERIFIED", fill=(0, 0, 0))
    for c in [100, 400, 800, 1200, w - 100]:
        draw_t.line([(c, 250), (c, 250 + 9 * 100)], fill=(0, 0, 0), width=3)
    # Rotate 90 degrees
    table_90 = table_img.rotate(90, expand=True, fillcolor=(255, 255, 255))
    _save_as_pdf(table_90, ATTACK_DIR / "atk_08_landscape_table_90deg.pdf")

    # 9. Heavy Gaussian blur
    blur_img = base_img.filter(PIL.ImageFilter.GaussianBlur(radius=3.5))
    _save_as_pdf(blur_img, ATTACK_DIR / "atk_09_heavy_gaussian_blur.pdf")

    # 10. Extreme shadow corner
    shadow_img = base_img.copy()
    draw_sh = PIL.ImageDraw.Draw(shadow_img, "RGBA")
    # Diagonal dark gradient
    for i in range(100):
        alpha = int(255 * (i / 100.0) * 0.85)
        draw_sh.rectangle([0, i * (h / 100), w, (i + 1) * (h / 100)], fill=(0, 0, 0, alpha))
    _save_as_pdf(shadow_img.convert("RGB"), ATTACK_DIR / "atk_10_extreme_shadow_corner.pdf")

    print(f"Successfully generated 10 attack fixtures in {ATTACK_DIR}")


if __name__ == "__main__":
    generate_all()
