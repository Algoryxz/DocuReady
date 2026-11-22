"""
scripts/diagnose_deskew_failure_modes.py

Investigates potential failure modes of the projection-profile deskew estimator:
1. Blank pages
2. Sparse text (single word / 3 words)
3. Single line documents
4. Short receipts
5. Tables with rules (grid lines)
6. Tables without rules
7. Box borders / heavy border frames
8. Multi-column text
9. Mixed text + image / photo
10. Background shadows / gradient illumination
11. Low contrast / faint text
12. JPEG compression artifacts
13. Blur / out-of-focus
14. High Gaussian noise
15. Low DPI (e.g. 72 DPI, 100 DPI)
16. Extreme aspect ratios (very tall receipt 1:8, very wide banner 8:1)
17. Landscape vs portrait orientation
18. Pure horizontal lines without text
19. Pure vertical lines (e.g. barcodes, vertical rules)
20. Crosshatch grid (competing peaks at 0° and 45°)
"""

import math
import numpy as np
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFilter

from docuready.ingest.deskew import estimate_skew_angle, deskew_image


def create_base_canvas(w=1600, h=2200, bg=(255, 255, 255)) -> PIL.Image.Image:
    return PIL.Image.new("RGB", (w, h), bg)


def add_text_lines(img: PIL.Image.Image, n_lines=15, start_y=300, spacing=60, text="THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG"):
    draw = PIL.ImageDraw.Draw(img)
    for i in range(n_lines):
        y = start_y + i * spacing
        draw.text((200, y), f"LINE {i+1:02d}: {text}", fill=(0, 0, 0))


def test_scenario(name: str, base_img: PIL.Image.Image, gt_skew: float, max_err=0.5):
    # Rotate by gt_skew (counter-clockwise)
    if abs(gt_skew) > 1e-4:
        rot_img = base_img.rotate(gt_skew, expand=True, fillcolor=(255, 255, 255), resample=PIL.Image.Resampling.BILINEAR)
    else:
        rot_img = base_img.copy()

    # Deskew estimation
    est_corr, conf = estimate_skew_angle(rot_img, max_angle=45.0)

    # Note: est_corr should be approximately -gt_skew (to restore upright)
    expected_corr = -gt_skew if abs(gt_skew) >= 1.0 else 0.0
    err = abs(est_corr - expected_corr)
    passed = err <= max_err

    status = "PASS" if passed else "FAIL"
    print(f"[{status:4}] {name:38} | GT: {gt_skew:+5.1f}° | Exp: {expected_corr:+5.1f}° | Est: {est_corr:+5.1f}° | Err: {err:4.2f}° | Conf: {conf:5.1f}")
    return {
        "name": name,
        "gt_skew": gt_skew,
        "expected_corr": expected_corr,
        "est_corr": est_corr,
        "error": err,
        "confidence": conf,
        "passed": passed
    }


def run_all_scenarios():
    print("=" * 90)
    print("RUNNING ADVERSARIAL STRESS SCENARIOS FOR DESKEW ESTIMATOR")
    print("=" * 90)

    results = []

    # 1. Blank page
    im = create_base_canvas()
    results.append(test_scenario("1. Blank Page (Upright)", im, 0.0))
    results.append(test_scenario("1b. Blank Page (Tilted 10°)", im, 10.0))

    # 2. Sparse text: only 3 words
    im = create_base_canvas()
    draw = PIL.ImageDraw.Draw(im)
    draw.text((600, 1000), "CONFIDENTIAL DOCUMENT 2026", fill=(0, 0, 0))
    results.append(test_scenario("2. Sparse 3-word document (5°)", im, 5.0))
    results.append(test_scenario("2b. Sparse 3-word document (10°)", im, 10.0))

    # 3. Single text line
    im = create_base_canvas()
    draw = PIL.ImageDraw.Draw(im)
    draw.text((200, 1000), "CERTIFICATE OF BIRTH - REGISTRATION NUMBER 104928 - GOVERNMENT OF ODISHA", fill=(0, 0, 0))
    results.append(test_scenario("3. Single Line Document (7°)", im, 7.0))

    # 4. Short receipt (narrow 500x1200)
    im = create_base_canvas(500, 1200)
    add_text_lines(im, n_lines=12, start_y=150, spacing=40, text="ITEM CODE: 90218 - AMOUNT: 450.00")
    results.append(test_scenario("4. Short Receipt (5°)", im, 5.0))
    results.append(test_scenario("4b. Short Receipt (12°)", im, 12.0))

    # 5. Table with heavy horizontal rules
    im = create_base_canvas()
    draw = PIL.ImageDraw.Draw(im)
    for r in range(12):
        y = 300 + r * 100
        draw.line([(100, y), (1500, y)], fill=(0, 0, 0), width=4)
        draw.text((150, y + 30), f"TABLE ROW {r+1}: ANNUAL TAXABLE REVENUE ENTRY", fill=(0, 0, 0))
    results.append(test_scenario("5. Table with Heavy Rules (6°)", im, 6.0))

    # 6. Heavy Border Frame / Box Borders
    im = create_base_canvas()
    draw = PIL.ImageDraw.Draw(im)
    draw.rectangle([(80, 80), (1520, 2120)], outline=(0, 0, 0), width=12) # Thick page border
    add_text_lines(im, n_lines=10, start_y=400, spacing=70)
    results.append(test_scenario("6. Thick Box Border (8°)", im, 8.0))

    # 7. Pure Horizontal Lines (NO text)
    im = create_base_canvas()
    draw = PIL.ImageDraw.Draw(im)
    for y in range(200, 2000, 150):
        draw.line([(100, y), (1500, y)], fill=(0, 0, 0), width=3)
    results.append(test_scenario("7. Pure Horizontal Lines (10°)", im, 10.0))

    # 8. Pure Vertical Lines (Barcodes / vertical rules)
    im = create_base_canvas()
    draw = PIL.ImageDraw.Draw(im)
    for x in range(200, 1400, 40):
        draw.line([(x, 300), (x, 1800)], fill=(0, 0, 0), width=5)
    results.append(test_scenario("8. Pure Vertical Lines (0°)", im, 0.0))
    results.append(test_scenario("8b. Pure Vertical Lines (10°)", im, 10.0))

    # 9. Severe Shadow / Diagonal Illumination Gradient
    im = create_base_canvas()
    add_text_lines(im, n_lines=18, start_y=250, spacing=60)
    # Apply severe diagonal dark gradient
    arr = np.array(im, dtype=np.float32)
    h, w, _ = arr.shape
    y_coords, x_coords = np.mgrid[0:h, 0:w]
    # Shadow factor from top-left (0.2) to bottom-right (1.0)
    shadow = 0.2 + 0.8 * ((x_coords / w) * 0.5 + (y_coords / h) * 0.5)
    shadow = np.expand_dims(shadow, axis=2)
    arr = np.clip(arr * shadow, 0, 255).astype(np.uint8)
    shadow_im = PIL.Image.fromarray(arr)
    results.append(test_scenario("9. Severe Diagonal Shadow (5°)", shadow_im, 5.0))
    results.append(test_scenario("9b. Severe Diagonal Shadow (0°)", shadow_im, 0.0))

    # 10. Heavy Gaussian Noise / Salt & Pepper
    im = create_base_canvas()
    add_text_lines(im, n_lines=15, start_y=300, spacing=60)
    arr = np.array(im, dtype=np.float32)
    noise = np.random.normal(0, 45, arr.shape)
    noisy_arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    noisy_im = PIL.Image.fromarray(noisy_arr)
    results.append(test_scenario("10. Heavy Gaussian Noise (7°)", noisy_im, 7.0))

    # 11. Low Contrast / Faint Ink
    im = create_base_canvas()
    draw = PIL.ImageDraw.Draw(im)
    for i in range(15):
        y = 300 + i * 60
        # Faint gray text on white background (contrast < 20%)
        draw.text((200, y), f"FAINT LINE {i+1:02d}: THIS IS VERY LOW CONTRAST CARBON COPY", fill=(215, 215, 215))
    results.append(test_scenario("11. Faint Carbon Copy (5°)", im, 5.0))
    results.append(test_scenario("11b. Faint Carbon Copy (0°)", im, 0.0))

    # 12. Extreme Aspect Ratio: Banner (2400 x 400)
    im = create_base_canvas(2400, 400)
    add_text_lines(im, n_lines=4, start_y=80, spacing=60, text="WIDE HORIZONTAL BANNER CERTIFICATE HEADING")
    results.append(test_scenario("12. Wide Banner Aspect Ratio (6°)", im, 6.0))

    # 13. Multi-column Newspaper / Gazette Layout
    im = create_base_canvas()
    draw = PIL.ImageDraw.Draw(im)
    for col_x in [150, 650, 1150]:
        for r in range(25):
            y = 200 + r * 45
            draw.text((col_x, y), f"Col entry {r+1}: Gazette notification text snippet", fill=(0, 0, 0))
    results.append(test_scenario("13. 3-Column Layout (8°)", im, 8.0))

    # 14. Competing Crosshatch Grid (45° diagonal lines + 0° text)
    im = create_base_canvas()
    draw = PIL.ImageDraw.Draw(im)
    # Add 45 degree diagonal hatching
    for d in range(-2000, 4000, 80):
        draw.line([(d, 0), (d + 2200, 2200)], fill=(180, 180, 180), width=2)
    add_text_lines(im, n_lines=15, start_y=300, spacing=60)
    results.append(test_scenario("14. Crosshatch Watermark (5°)", im, 5.0))
    results.append(test_scenario("14b. Crosshatch Watermark (0°)", im, 0.0))

    n_pass = sum(1 for r in results if r["passed"])
    n_fail = sum(1 for r in results if not r["passed"])
    print("=" * 90)
    print(f"ADVERSARIAL STRESS TEST SUMMARY: {n_pass} PASSED, {n_fail} FAILED (TOTAL {len(results)})")
    print("=" * 90)


if __name__ == "__main__":
    run_all_scenarios()
