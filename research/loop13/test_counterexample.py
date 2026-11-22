"""
Test Column-Aware Clustering on Counterexample
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.loop13.spatial_layout_experiment import cluster_words_column_aware

words = [
    # Full-Width Header (y=50)
    ("GOVERNMENT", 50, 50, 80, 12), ("SCHOLARSHIP", 140, 50, 90, 12), ("NOTIFICATION", 240, 50, 90, 12),
    # Left Col Line 1 (y=100)
    ("The", 50, 100, 25, 12), ("post-matric", 80, 100, 70, 12), ("scholarship", 155, 100, 65, 12),
    # Right Col Line 1 (y=100)
    ("State", 350, 100, 35, 12), ("verification", 390, 100, 75, 12), ("offices", 470, 100, 45, 12),
    # Left Col Line 2 (y=115)
    ("Eligible", 50, 115, 45, 12), ("students", 100, 115, 50, 12), ("must", 155, 115, 30, 12),
    # Right Col Line 2 (y=115)
    ("Incomplete", 350, 115, 65, 12), ("documentation", 420, 115, 80, 12), ("leads", 505, 115, 35, 12),
    # Full-Width Footer (y=200)
    ("End", 50, 200, 25, 12), ("of", 80, 200, 15, 12), ("Official", 100, 200, 50, 12), ("Notice", 155, 200, 45, 12)
]

words_meta = [
    {
        "word": w[0],
        "box": [w[1], w[2], w[1]+w[3], w[2]+w[4]],
        "conf": 95.0,
        "x0": float(w[1]),
        "y0": float(w[2])
    }
    for w in words
]

lines = cluster_words_column_aware(words_meta)
print("=== COLUMN-AWARE CLUSTERED LINES ===")
for idx, l in enumerate(lines):
    line_text = " ".join(w["word"] for w in l)
    print(f"Line {idx+1}: {line_text}")
