"""
Minimal Counterexample Demonstrating Cross-Column Interleaving Defect
DocuReady - Research Loop 13
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.docuready.ingest.extractor import PageOCRData

def test_cross_column_interleaving_counterexample():
    """
    Constructs a 2-column page where:
    Left Column (x=50..200):
      Line 1: "The post-matric scholarship provides financial assistance."
      Line 2: "Eligible students must submit income certificates."
    Right Column (x=350..550):
      Line 1: "State verification offices operate during working hours."
      Line 2: "Incomplete documentation leads to immediate rejection."
    """
    # Simulate Tesseract Output Dict
    words = [
        # Left Col Line 1 (y=100)
        ("The", 50, 100, 25, 12), ("post-matric", 80, 100, 70, 12), ("scholarship", 155, 100, 65, 12),
        # Right Col Line 1 (y=100)
        ("State", 350, 100, 35, 12), ("verification", 390, 100, 75, 12), ("offices", 470, 100, 45, 12),
        # Left Col Line 2 (y=115)
        ("Eligible", 50, 115, 45, 12), ("students", 100, 115, 50, 12), ("must", 155, 115, 30, 12),
        # Right Col Line 2 (y=115)
        ("Incomplete", 350, 115, 65, 12), ("documentation", 420, 115, 80, 12), ("leads", 505, 115, 35, 12)
    ]

    raw_data = {
        "text": [w[0] for w in words],
        "conf": [95.0] * len(words),
        "left": [w[1] for w in words],
        "top": [w[2] for w in words],
        "width": [w[3] for w in words],
        "height": [w[4] for w in words]
    }

    page_ocr = PageOCRData(raw_data, dpi=72)

    print("=== EXTRACTED LINES FROM 2-COLUMN INPUT ===")
    for idx, l in enumerate(page_ocr.lines):
        print(f"Line {idx+1}: {l['text']}")

    # Expected true reading order:
    # 1. Left column lines first
    # 2. Right column lines second
    expected_order = [
        "The post-matric scholarship",
        "Eligible students must",
        "State verification offices",
        "Incomplete documentation leads"
    ]

    interleaved = False
    for l in page_ocr.lines:
        if "scholarship State" in l["text"] or "must Incomplete" in l["text"]:
            interleaved = True

    print(f"\nDefect Present (Cross-Column Interleaving): {interleaved}")
    return interleaved

if __name__ == "__main__":
    test_cross_column_interleaving_counterexample()
