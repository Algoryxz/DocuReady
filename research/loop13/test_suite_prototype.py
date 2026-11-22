"""
Test Suite Prototype for Spatial Reconstruction
DocuReady - Research Loop 13
"""

import sys
import pymupdf
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.loop13.spatial_reconstruction import cluster_and_order_words, detect_page_layout_structure
from src.docuready.ingest.extractor import PageOCRData, _ocr_page

def run_tests():
    print("=== TEST 1: TWO-COLUMN INDEPENDENT NARRATIVE FLOW ===")
    words_col = [
        ("GOVERNMENT", 50, 50, 80, 12), ("SCHOLARSHIP", 140, 50, 90, 12), ("NOTIFICATION", 240, 50, 90, 12),
        ("The", 50, 100, 25, 12), ("post-matric", 80, 100, 70, 12), ("scholarship", 155, 100, 65, 12),
        ("State", 350, 100, 35, 12), ("verification", 390, 100, 75, 12), ("offices", 470, 100, 45, 12),
        ("Eligible", 50, 115, 45, 12), ("students", 100, 115, 50, 12), ("must", 155, 115, 30, 12),
        ("Incomplete", 350, 115, 65, 12), ("documentation", 420, 115, 80, 12), ("leads", 505, 115, 35, 12),
        ("End", 50, 200, 25, 12), ("of", 80, 200, 15, 12), ("Official", 100, 200, 50, 12), ("Notice", 155, 200, 45, 12)
    ]
    meta_col = [
        {"word": w[0], "box": [w[1], w[2], w[1]+w[3], w[2]+w[4]], "conf": 95.0, "x0": float(w[1]), "y0": float(w[2])}
        for w in words_col
    ]
    lines_col = cluster_and_order_words(meta_col)
    extracted_texts_col = [" ".join(item["word"] for item in l) for l in lines_col]
    print("Extracted Lines:")
    for i, t in enumerate(extracted_texts_col):
        print(f"  {i+1}: {t}")

    assert extracted_texts_col[0] == "GOVERNMENT SCHOLARSHIP NOTIFICATION"
    assert extracted_texts_col[1] == "The post-matric scholarship"
    assert extracted_texts_col[2] == "Eligible students must"
    assert extracted_texts_col[3] == "State verification offices"
    assert extracted_texts_col[4] == "Incomplete documentation leads"
    assert extracted_texts_col[5] == "End of Official Notice"
    print("-> PASS: Two-column narrative de-interleaved into natural reading order!\n")

    print("=== TEST 2: KEY-VALUE FORM PRESERVATION (FUNSD SAMPLE) ===")
    doc = pymupdf.open("research/loop11_benchmark/data/funsd/funsd_001.pdf")
    page_ocr = _ocr_page(doc[0], dpi=150)
    doc.close()

    # Reconstruct words_meta from OCR data
    meta_funsd = []
    scale = 72.0 / 150.0
    for l in page_ocr.lines:
        for w, b, c in zip(l["words"], l["word_boxes"], l["word_confs"]):
            meta_funsd.append({
                "word": w,
                "box": b,
                "conf": c,
                "x0": b[0],
                "y0": b[1]
            })

    lines_funsd = cluster_and_order_words(meta_funsd)
    extracted_funsd = [" ".join(item["word"] for item in l) for l in lines_funsd]
    print("Extracted Lines (First 6):")
    for i, t in enumerate(extracted_funsd[:6]):
        print(f"  {i+1}: {t}")

    # Verify that Label and Value remain together on the same line
    assert any("Enrollment Roll Number:" in t and "DHE-2026-5541" in t for t in extracted_funsd), (
        "Label and Value must remain on the same line in Key-Value forms!"
    )
    assert any("Applicant Full Name:" in t and "ROHIT VERMA" in t for t in extracted_funsd), (
        "Applicant Full Name and ROHIT VERMA must be on the same line!"
    )
    print("-> PASS: Key-Value form table preserves row reading order and field extractability!\n")

    print("=== TEST 3: SINGLE-COLUMN CERTIFICATE (ZERO REGRESSIONS) ===")
    doc_cert = pymupdf.open("tests/validation_corpus/VAL_02_income_cert_clean.pdf")
    cert_ocr = _ocr_page(doc_cert[0], dpi=150)
    doc_cert.close()

    meta_cert = []
    for l in cert_ocr.lines:
        for w, b, c in zip(l["words"], l["word_boxes"], l["word_confs"]):
            meta_cert.append({
                "word": w,
                "box": b,
                "conf": c,
                "x0": b[0],
                "y0": b[1]
            })

    lines_cert = cluster_and_order_words(meta_cert)
    extracted_cert = [" ".join(item["word"] for item in l) for l in lines_cert]
    print("Certificate Lines (First 5):")
    for i, t in enumerate(extracted_cert[:5]):
        print(f"  {i+1}: {t}")

    # Compare line count parity with baseline
    print(f"Baseline line count: {len(cert_ocr.lines)}, Column-Aware line count: {len(lines_cert)}")
    assert len(lines_cert) == len(cert_ocr.lines), "Single-column line count must be identical!"
    print("-> PASS: Single-column certificate exhibits zero regressions!\n")

    print("=== ALL PROTOTYPE TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
