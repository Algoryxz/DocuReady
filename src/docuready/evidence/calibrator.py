"""
Field-Level Confidence Calibration and Evidence State Engine for DocuReady Loop 3
Maps raw OCR token confidences and layout features into calibrated correctness probabilities
and discrete epistemic evidence states.
"""

import math
import re
from typing import Dict, Any, Tuple, Optional, Sequence
from docuready.domain.models import EvidenceState, ExtractionMethod
from docuready.evidence.features import CalibrationFeatureVector, compute_nine_features
from docuready.evidence.states import discretize_probability
from docuready.normalize.normalizer import parse_and_normalize_date, validate_ifsc_code, normalize_income


def validate_field_syntax(field_name: str, raw_value: str) -> Tuple[bool, Optional[str]]:
    """
    Validates whether the raw string matches expected syntactic constraints for the field.
    Returns (is_valid, failure_reason)
    """
    val = raw_value.strip()
    if not val:
        return False, "Empty or whitespace-only value"

    # Reject values that are merely echoed labels or separators
    label_echoes = [":", "-", "=", "IN FIGURES", "RS.", "RUPEES", "APPLICANT NAME", "DATE", "CERTIFICATE NO"]
    if val.upper() in label_echoes:
        return False, f"Value is identical to field label or separator: '{val}'"

    if field_name == "applicant_name" or field_name == "father_name":
        # Name should not contain digits or colons
        if re.search(r"[\d:]", val):
            return False, f"Name contains numerical digits or colons: '{val}'"
        words = [w for w in re.split(r"[\s\.\-]+", val) if len(w) > 1]
        if len(words) < 2:
            return False, f"Incomplete name: expected at least two name components, got '{val}'"
        if len(val) > 60:
            return False, f"Name exceeds maximum plausible length (60 chars): '{val}'"
        return True, None

    elif field_name == "dob" or field_name == "issue_date":
        dt, status, is_ambig = parse_and_normalize_date(val)
        if dt is None:
            return False, f"Date format cannot be parsed into a calendar date: '{val}'"
        if dt.year < 1960 or dt.year > 2026:
            return False, f"Date year {dt.year} is outside plausible statutory bounds (1960-2026)"
        return True, None

    elif field_name == "annual_income":
        inc_norm = normalize_income(val)
        if inc_norm is None:
            return False, f"Cannot parse numerical currency figure from: '{val}'"
        if inc_norm <= 0 or inc_norm > 100000000:
            return False, f"Income ₹{inc_norm:,.0f} is outside plausible economic range"
        return True, None

    elif field_name == "ifsc":
        is_ifsc = validate_ifsc_code(val)
        if not is_ifsc:
            return False, f"String '{val}' violates 11-character RBI IFSC structure"
        return True, None

    elif "cert_no" in field_name or "certificate_no" in field_name:
        clean = re.sub(r"[\s\-\/]", "", val)
        if len(clean) < 4:
            return False, f"Certificate reference number too short (<4 chars): '{val}'"
        if not any(c.isdigit() for c in val):
            return False, f"Certificate number contains no digits: '{val}'"
        return True, None

    elif field_name == "account_no":
        clean_digits = re.sub(r"\D", "", val)
        if len(clean_digits) < 8 or len(clean_digits) > 20:
            return False, f"Bank account number length ({len(clean_digits)}) outside 8-20 range"
        return True, None

    elif field_name == "percentage":
        try:
            if "-" in val:
                return False, "Negative percentage"
            m = re.search(r"[\d.]+", val)
            if not m:
                return False, "No digits found in percentage string"
            pct = float(m.group(0))
            if pct < 0.0 or pct > 100.0:
                return False, f"Percentage {pct}% outside 0-100 range"
            return True, None
        except Exception as e:
            return False, f"Invalid percentage format: {e}"

    return True, None


# Default 9-feature logistic parameters: Logit = beta_0 + sum(beta_i * x_i)
DEFAULT_INTERCEPT: float = -4.0
DEFAULT_WEIGHTS: Tuple[float, ...] = (
    4.0,   # x1: ocr_token_confidence
    0.6,   # x2: supporting_token_count
    0.8,   # x3: anchor_label_proximity
    0.6,   # x4: label_match_confidence
    1.8,   # x5: format_validation
    -1.8,  # x6: candidate_ambiguity
    0.5,   # x7: layout_consistency
    -0.5,  # x8: extraction_source (OCR penalty relative to native vector)
    -1.2,  # x9: rotation_skew
)


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)


class ConfidenceCalibrator:
    """
    Computes calibrated field-level correctness probability and evidence state.
    Implements the 9-feature logistic calibration engine:
      Logit = beta_0 + sum_{i=1}^9 beta_i * x_i
      P(Correct | x) = sigmoid(Logit)
    """

    def __init__(
        self,
        tau_high: float = 0.70,     # Below this, OCR fields downgrade to LOW_CONFIDENCE
        tau_abstain: float = 0.45,  # Below this, the extractor completely abstains
        w_token: float = 0.55,
        w_label: float = 0.20,
        w_format: float = 0.25,
        intercept: float = DEFAULT_INTERCEPT,
        weights: Optional[Sequence[float]] = None,
    ):
        self.tau_high = tau_high
        self.tau_abstain = tau_abstain
        # Legacy scalar weights retained as attributes for backward compatibility
        self.w_token = w_token
        self.w_label = w_label
        self.w_format = w_format
        self.intercept = float(intercept)
        self.weights = tuple(float(w) for w in (weights if weights is not None else DEFAULT_WEIGHTS))
        if len(self.weights) != 9:
            raise ValueError(f"Expected 9 logistic weights, got {len(self.weights)}")

    def predict_proba(self, features: CalibrationFeatureVector) -> float:
        """Compute calibrated correctness probability P(Correct | x) via 9-feature logistic model."""
        vec = features.to_list()
        logit = self.intercept + sum(w * x for w, x in zip(self.weights, vec))
        return round(_sigmoid(logit), 3)

    def fit(
        self,
        feature_vectors: Sequence[CalibrationFeatureVector],
        labels: Sequence[int],
        *,
        lr: float = 0.25,
        epochs: int = 500,
        l2: float = 1e-3,
    ) -> "ConfidenceCalibrator":
        """Fit logistic regression parameters (intercept and 9 weights) on a calibration split."""
        if len(feature_vectors) != len(labels):
            raise ValueError("feature_vectors and labels must have equal length")
        if not feature_vectors:
            raise ValueError("Cannot fit calibrator on empty calibration split")

        n = len(feature_vectors)
        b0 = self.intercept
        ws = list(self.weights)

        for _ in range(epochs):
            grad_b0 = 0.0
            grad_w = [0.0] * 9
            for fv, y in zip(feature_vectors, labels):
                x = fv.to_list()
                p = _sigmoid(b0 + sum(w * xi for w, xi in zip(ws, x)))
                err = p - float(y)
                grad_b0 += err
                for i in range(9):
                    grad_w[i] += err * x[i]

            b0 -= lr * (grad_b0 / n)
            for i in range(9):
                ws[i] -= lr * ((grad_w[i] / n) + l2 * ws[i])

        self.intercept = round(b0, 6)
        self.weights = tuple(round(w, 6) for w in ws)
        return self

    def calibrate(
        self,
        field_name: str,
        raw_value: str,
        extraction_method: ExtractionMethod,
        token_confidence: Optional[float] = None,
        label_detected: bool = True,
        label_distance_pt: float = 0.0,
        candidate_count: int = 1,
        supporting_tokens_count: int = 1,
        page_has_date_ambiguity: bool = False,
        label_match_confidence: Optional[float] = None,
        layout_consistency: float = 0.90,
        rotation_deg: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Calculates calibrated correctness probability using the 9-feature logistic model
        and assigns both transitional and canonical EvidenceState.
        """
        # 1. Format Syntax Check
        is_syntax_valid, syntax_err = validate_field_syntax(field_name, raw_value)

        # 2. Compute 9-dimensional feature vector
        features = compute_nine_features(
            field_name=field_name,
            extraction_method=extraction_method,
            is_syntax_valid=is_syntax_valid,
            token_confidence=token_confidence,
            label_detected=label_detected,
            label_distance_pt=label_distance_pt,
            label_match_confidence=label_match_confidence,
            candidate_count=candidate_count,
            supporting_tokens_count=supporting_tokens_count,
            layout_consistency=layout_consistency,
            rotation_deg=rotation_deg,
        )

        # 3. Native Vector Handling (preserves golden snapshot 0.98 / 0.75 contract)
        if extraction_method == ExtractionMethod.NATIVE_VECTOR:
            calibrated_prob = 0.98 if is_syntax_valid else 0.75
            if not is_syntax_valid:
                state = EvidenceState.LOW_CONFIDENCE
            elif page_has_date_ambiguity and ("date" in field_name or field_name == "dob"):
                state = EvidenceState.AMBIGUOUS
            else:
                state = EvidenceState.VERIFIED_TEXT

            canonical_state = discretize_probability(
                calibrated_prob,
                is_ambiguous=(state in (EvidenceState.AMBIGUOUS, EvidenceState.LOW_CONFIDENCE)),
            )
            return {
                "calibrated_confidence": calibrated_prob,
                "evidence_state": state,
                "canonical_evidence_state": canonical_state,
                "features": features.as_dict(),
                "format_valid": is_syntax_valid,
                "syntax_reason": syntax_err,
                "is_uncertain": state in [EvidenceState.AMBIGUOUS, EvidenceState.LOW_CONFIDENCE],
                "uncertainty_reason": syntax_err if not is_syntax_valid else ("Date format ambiguity (DD/MM vs MM/DD)" if state == EvidenceState.AMBIGUOUS else None),
            }

        # 4. Local OCR Handling (9-feature logistic probability)
        calibrated_prob = self.predict_proba(features)

        if not is_syntax_valid:
            state = EvidenceState.LOW_CONFIDENCE
            unc_reason = f"Syntactic format failure: {syntax_err}"
        elif candidate_count > 1:
            state = EvidenceState.AMBIGUOUS
            unc_reason = f"Multiple plausible candidate values found ({candidate_count} candidates)"
        elif page_has_date_ambiguity and ("date" in field_name or field_name == "dob"):
            state = EvidenceState.AMBIGUOUS
            unc_reason = "Ambiguous date representation (DD/MM vs MM/DD)"
        elif calibrated_prob < self.tau_high:
            state = EvidenceState.LOW_CONFIDENCE
            unc_reason = f"Calibrated field confidence ({calibrated_prob*100:.1f}%) is below safety threshold ({self.tau_high*100:.0f}%)"
        else:
            state = EvidenceState.OCR_EXTRACTED
            unc_reason = None

        is_unc = state in [EvidenceState.AMBIGUOUS, EvidenceState.LOW_CONFIDENCE]
        canonical_state = discretize_probability(calibrated_prob, is_ambiguous=is_unc)

        return {
            "calibrated_confidence": calibrated_prob,
            "evidence_state": state,
            "canonical_evidence_state": canonical_state,
            "features": features.as_dict(),
            "format_valid": is_syntax_valid,
            "syntax_reason": syntax_err,
            "is_uncertain": is_unc,
            "uncertainty_reason": unc_reason,
        }
