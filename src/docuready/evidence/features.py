"""Nine-feature extraction vector for DocuReady evidence calibration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from docuready.domain.enums import ExtractionMethod


FEATURE_NAMES: tuple[str, ...] = (
    "ocr_token_confidence",
    "supporting_token_count",
    "anchor_label_proximity",
    "label_match_confidence",
    "format_validation",
    "candidate_ambiguity",
    "layout_consistency",
    "extraction_source",
    "rotation_skew",
)


@dataclass(frozen=True)
class CalibrationFeatureVector:
    """Immutable 9-feature vector x in R^9 for logistic evidence calibration."""

    ocr_token_confidence: float
    supporting_token_count: float
    anchor_label_proximity: float
    label_match_confidence: float
    format_validation: float
    candidate_ambiguity: float
    layout_consistency: float
    extraction_source: float
    rotation_skew: float

    def to_list(self) -> List[float]:
        """Return the ordered 9-dimensional feature vector."""
        return [
            self.ocr_token_confidence,
            self.supporting_token_count,
            self.anchor_label_proximity,
            self.label_match_confidence,
            self.format_validation,
            self.candidate_ambiguity,
            self.layout_consistency,
            self.extraction_source,
            self.rotation_skew,
        ]

    def as_dict(self) -> Dict[str, float]:
        """Return a named dictionary representation for provenance/evaluation."""
        return dict(zip(FEATURE_NAMES, self.to_list()))


def compute_nine_features(
    *,
    field_name: str,
    extraction_method: ExtractionMethod,
    is_syntax_valid: bool,
    token_confidence: float | None = None,
    label_detected: bool = True,
    label_distance_pt: float = 0.0,
    label_match_confidence: float | None = None,
    candidate_count: int = 1,
    supporting_tokens_count: int = 1,
    layout_consistency: float = 0.90,
    rotation_deg: float = 0.0,
) -> CalibrationFeatureVector:
    """Compute the normalized 9-dimensional feature vector for a field extraction."""
    is_ocr = extraction_method == ExtractionMethod.LOCAL_OCR

    # 1. OCR token confidence (native vector text defaults to 1.0)
    if not is_ocr:
        x_tok = 1.0
    else:
        x_tok = max(0.0, min(1.0, float(token_confidence) if token_confidence is not None else 0.50))

    # 2. Supporting token count (normalized; penalize single-token person names)
    tok_count = max(0, int(supporting_tokens_count))
    if field_name in ("applicant_name", "father_name") and tok_count < 2:
        x_sup = 0.25 if tok_count == 1 else 0.0
    else:
        x_sup = min(1.0, tok_count / 3.0)

    # 3. Anchor label proximity
    if not label_detected:
        x_prox = 0.20
    elif label_distance_pt <= 25.0:
        x_prox = 1.00
    elif label_distance_pt <= 60.0:
        x_prox = 0.75
    elif label_distance_pt <= 150.0:
        x_prox = 0.50
    else:
        x_prox = 0.30

    # 4. Label match confidence
    if label_match_confidence is not None:
        x_lbl = max(0.0, min(1.0, float(label_match_confidence)))
    else:
        x_lbl = 1.0 if label_detected else 0.20

    # 5. Format validation indicator
    x_fmt = 1.0 if is_syntax_valid else 0.0

    # 6. Candidate ambiguity penalty signal (0.0 when unique, up to 1.0 when >= 4)
    x_amb = min(1.0, max(0, int(candidate_count) - 1) / 3.0)

    # 7. Layout consistency score
    x_lay = max(0.0, min(1.0, float(layout_consistency)))

    # 8. Extraction source mode (1.0 = OCR raster, 0.0 = native vector)
    x_src = 1.0 if is_ocr else 0.0

    # 9. Rotation / skew penalty signal (0.0 = upright, 1.0 = >= 15 deg skew)
    x_rot = min(1.0, abs(float(rotation_deg)) / 15.0)

    return CalibrationFeatureVector(
        ocr_token_confidence=round(x_tok, 4),
        supporting_token_count=round(x_sup, 4),
        anchor_label_proximity=round(x_prox, 4),
        label_match_confidence=round(x_lbl, 4),
        format_validation=round(x_fmt, 4),
        candidate_ambiguity=round(x_amb, 4),
        layout_consistency=round(x_lay, 4),
        extraction_source=round(x_src, 4),
        rotation_skew=round(x_rot, 4),
    )
