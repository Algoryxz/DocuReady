"""
Independent Benchmark Evaluation Metrics for Loop 11
DocuReady - Research Loop 11

Implements independent, unbiased metrics for OCR, Layout, Field Extraction, and Decision Engine evaluation:
- Levenshtein-based Character Error Rate (CER) and Word Error Rate (WER)
- Bounding Box Intersection-over-Union (IoU)
- Key-Value Field Precision, Recall, and F1
- Decision Engine Reliability (False READY, False NOT_READY rates)
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple


def compute_levenshtein_distance(s1: str, s2: str) -> int:
    """Computes exact edit distance (insertions, deletions, substitutions)."""
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    return dp[m][n]


def compute_cer(reference: str, hypothesis: str) -> float:
    """Computes Character Error Rate = Levenshtein(ref, hyp) / max(1, len(ref))."""
    ref = reference.strip()
    hyp = hypothesis.strip()
    if not ref:
        return 0.0 if not hyp else 1.0
    dist = compute_levenshtein_distance(ref, hyp)
    return min(1.0, dist / len(ref))


def compute_wer(reference: str, hypothesis: str) -> float:
    """Computes Word Error Rate = Levenshtein_words(ref, hyp) / max(1, len(ref_words))."""
    ref_words = [w for w in re.split(r"\s+", reference.strip()) if w]
    hyp_words = [w for w in re.split(r"\s+", hypothesis.strip()) if w]
    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    m, n = len(ref_words), len(hyp_words)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    return min(1.0, dp[m][n] / len(ref_words))


def compute_bbox_iou(box1: List[float], box2: List[float]) -> float:
    """Computes standard Intersection over Union for [x0, y0, x1, y1] boxes."""
    if not box1 or not box2 or len(box1) != 4 or len(box2) != 4:
        return 0.0

    x_left = max(box1[0], box2[0])
    y_top = max(box1[1], box2[1])
    x_right = min(box1[2], box2[2])
    y_bottom = min(box1[3], box2[3])

    if x_right <= x_left or y_bottom <= y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    box1_area = max(0.0, (box1[2] - box1[0]) * (box1[3] - box1[1]))
    box2_area = max(0.0, (box2[2] - box2[0]) * (box2[3] - box2[1]))
    union_area = box1_area + box2_area - intersection_area

    if union_area <= 0.0:
        return 0.0
    return min(1.0, intersection_area / union_area)


def compute_field_metrics(
    ground_truth_fields: Dict[str, str],
    extracted_fields: Dict[str, str],
    normalize_values: bool = True
) -> Dict[str, float]:
    """Computes exact and normalized Precision, Recall, and F1 across target fields."""
    tp = 0
    fp = 0
    fn = 0

    def clean(s: Optional[str]) -> str:
        if not s:
            return ""
        s = re.sub(r"[^\w\s]", "", str(s).lower())
        return re.sub(r"\s+", " ", s).strip()

    for k, gt_v in ground_truth_fields.items():
        ext_v = extracted_fields.get(k)
        if ext_v is not None:
            c_gt = clean(gt_v) if normalize_values else str(gt_v).strip()
            c_ext = clean(ext_v) if normalize_values else str(ext_v).strip()
            if c_gt == c_ext:
                tp += 1
            else:
                fp += 1
        else:
            fn += 1

    for k, ext_v in extracted_fields.items():
        if k not in ground_truth_fields:
            fp += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn
    }
