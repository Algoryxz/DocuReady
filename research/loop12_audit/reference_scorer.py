"""
Reference Scorer and Metric Verification Module for Loop 12
DocuReady - Loop 12 Benchmark Integrity Audit

Provides independent, mathematically verified implementations of:
- Character Error Rate (CER) and Word Error Rate (WER) with Levenshtein distance
- Unicode NFC normalization and clean tokenization
- Strict edge-case handling (empty ref, empty hyp, non-ASCII, deletion)
- Bounding box Intersection over Union (IoU) with bipartite overlap matching
- Field-level Key-Value extraction Precision, Recall, and F1
- Denominator audit verification (zero sample drops)
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional, Set, Tuple


def normalize_text_unicode(text: str, form: str = "NFC") -> str:
    """Normalizes text to standard Unicode normalization form."""
    if not text:
        return ""
    return unicodedata.normalize(form, text)


def compute_levenshtein_distance(s1: str, s2: str) -> int:
    """Computes exact edit distance (insertions, deletions, substitutions) between sequences."""
    m, n = len(s1), len(s2)
    if m == 0:
        return n
    if n == 0:
        return m

    # Use space-optimized two-row dynamic programming
    prev_row = list(range(n + 1))
    curr_row = [0] * (n + 1)

    for i in range(1, m + 1):
        curr_row[0] = i
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            curr_row[j] = min(
                curr_row[j - 1] + 1,      # Insertion
                prev_row[j] + 1,          # Deletion
                prev_row[j - 1] + cost    # Substitution
            )
        prev_row = list(curr_row)

    return prev_row[n]


def compute_cer_reference(
    reference: str,
    hypothesis: str,
    case_sensitive: bool = True,
    normalize_whitespace: bool = True,
    unicode_form: str = "NFC"
) -> float:
    """
    Computes rigorous Character Error Rate (CER).
    Formula: Levenshtein(ref, hyp) / len(ref), clamped to [0.0, 1.0].
    
    Edge-case rules:
    - If both ref and hyp are empty: 0.0 (no error).
    - If ref is empty but hyp is non-empty: 1.0 (pure hallucination).
    - If ref is non-empty but hyp is empty: 1.0 (pure deletion).
    """
    ref = normalize_text_unicode(reference, unicode_form)
    hyp = normalize_text_unicode(hypothesis, unicode_form)

    if normalize_whitespace:
        ref = re.sub(r"\s+", " ", ref).strip()
        hyp = re.sub(r"\s+", " ", hyp).strip()

    if not case_sensitive:
        ref = ref.lower()
        hyp = hyp.lower()

    if not ref and not hyp:
        return 0.0
    if not ref or not hyp:
        return 1.0

    dist = compute_levenshtein_distance(ref, hyp)
    cer = dist / len(ref)
    return min(1.0, round(cer, 4))


def compute_wer_reference(
    reference: str,
    hypothesis: str,
    case_sensitive: bool = True,
    unicode_form: str = "NFC"
) -> float:
    """
    Computes rigorous Word Error Rate (WER).
    Tokenizes on whitespace and computes word-level edit distance.
    Formula: Levenshtein_words(ref, hyp) / len(ref_words), clamped to [0.0, 1.0].
    """
    ref = normalize_text_unicode(reference, unicode_form)
    hyp = normalize_text_unicode(hypothesis, unicode_form)

    if not case_sensitive:
        ref = ref.lower()
        hyp = hyp.lower()

    ref_words = [w for w in re.split(r"\s+", ref.strip()) if w]
    hyp_words = [w for w in re.split(r"\s+", hyp.strip()) if w]

    if not ref_words and not hyp_words:
        return 0.0
    if not ref_words or not hyp_words:
        return 1.0

    dist = compute_levenshtein_distance(ref_words, hyp_words)
    wer = dist / len(ref_words)
    return min(1.0, round(wer, 4))


def compute_bbox_iou_reference(box1: List[float], box2: List[float]) -> float:
    """
    Computes exact Intersection-over-Union (IoU) for two [x0, y0, x1, y1] bounding boxes.
    Returns 0.0 for degenerate boxes or empty intersections.
    """
    if not box1 or not box2 or len(box1) != 4 or len(box2) != 4:
        return 0.0

    # Reject degenerate or inverted boxes
    if box1[0] >= box1[2] or box1[1] >= box1[3] or box2[0] >= box2[2] or box2[1] >= box2[3]:
        return 0.0

    b1_x0, b1_y0, b1_x1, b1_y1 = box1[0], box1[1], box1[2], box1[3]
    b2_x0, b2_y0, b2_x1, b2_y1 = box2[0], box2[1], box2[2], box2[3]

    x_left = max(b1_x0, b2_x0)
    y_top = max(b1_y0, b2_y0)
    x_right = min(b1_x1, b2_x1)
    y_bottom = min(b1_y1, b2_y1)

    if x_right <= x_left or y_bottom <= y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    area1 = (b1_x1 - b1_x0) * (b1_y1 - b1_y0)
    area2 = (b2_x1 - b2_x0) * (b2_y1 - b2_y0)
    union_area = area1 + area2 - intersection_area

    if union_area <= 0.0:
        return 0.0

    return min(1.0, round(intersection_area / union_area, 4))


def match_bboxes_greedy_iou(
    ground_truth_boxes: List[List[float]],
    predicted_boxes: List[List[float]],
    iou_threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Performs real bipartite matching between ground-truth and predicted bounding boxes
    using greedy maximum-IoU assignment.
    """
    if not ground_truth_boxes or not predicted_boxes:
        return {
            "matched_count": 0,
            "mean_matched_iou": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "pairs": []
        }

    # Compute pairwise IoU matrix
    matched_gt: Set[int] = set()
    matched_pred: Set[int] = set()
    matched_pairs: List[Tuple[int, int, float]] = []

    # Flatten candidates: (iou, gt_idx, pred_idx)
    candidates = []
    for g_idx, g_box in enumerate(ground_truth_boxes):
        for p_idx, p_box in enumerate(predicted_boxes):
            iou = compute_bbox_iou_reference(g_box, p_box)
            if iou >= iou_threshold:
                candidates.append((iou, g_idx, p_idx))

    # Sort descending by IoU
    candidates.sort(key=lambda x: x[0], reverse=True)

    for iou, g_idx, p_idx in candidates:
        if g_idx not in matched_gt and p_idx not in matched_pred:
            matched_gt.add(g_idx)
            matched_pred.add(p_idx)
            matched_pairs.append((g_idx, p_idx, iou))

    tp = len(matched_pairs)
    fp = len(predicted_boxes) - tp
    fn = len(ground_truth_boxes) - tp

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    mean_iou = sum(p[2] for p in matched_pairs) / tp if tp > 0 else 0.0

    return {
        "matched_count": tp,
        "mean_matched_iou": round(mean_iou, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "pairs": matched_pairs
    }


def compute_field_metrics_reference(
    ground_truth_fields: Dict[str, Any],
    extracted_fields: Dict[str, Any],
    normalize_values: bool = True
) -> Dict[str, Any]:
    """
    Computes strict key-value field extraction Precision, Recall, and F1.
    """
    tp = 0
    fp = 0
    fn = 0
    field_details = {}

    def clean(val: Any) -> str:
        if val is None:
            return ""
        s = str(val).strip()
        if normalize_values:
            s = re.sub(r"[^\w\s]", "", s.lower())
            s = re.sub(r"\s+", " ", s).strip()
        return s

    for key, gt_raw in ground_truth_fields.items():
        ext_raw = extracted_fields.get(key)
        c_gt = clean(gt_raw)
        c_ext = clean(ext_raw) if ext_raw is not None else ""

        if ext_raw is not None and c_gt == c_ext and c_gt != "":
            tp += 1
            field_details[key] = {"status": "MATCH", "gt": str(gt_raw), "ext": str(ext_raw)}
        elif ext_raw is not None:
            fp += 1
            field_details[key] = {"status": "VALUE_MISMATCH", "gt": str(gt_raw), "ext": str(ext_raw)}
        else:
            fn += 1
            field_details[key] = {"status": "MISSING_FIELD", "gt": str(gt_raw), "ext": None}

    # Any extracted field not present in ground truth counts as false positive
    for key, ext_raw in extracted_fields.items():
        if key not in ground_truth_fields:
            fp += 1
            field_details[key] = {"status": "UNEXPECTED_FIELD", "gt": None, "ext": str(ext_raw)}

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "field_details": field_details
    }
