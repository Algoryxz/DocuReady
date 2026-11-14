"""
Field-Level Confidence Calibration and Evidence State Engine for DocuReady Loop 3
Maps raw OCR token confidences and layout features into calibrated correctness probabilities
and discrete epistemic evidence states.
"""

import re
from typing import Dict, Any, Tuple, Optional
from docuready.domain.models import EvidenceState, ExtractionMethod
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


class ConfidenceCalibrator:
    """
    Computes calibrated field-level correctness probability and evidence state.
    Uses multi-feature regression: token confidence, label proximity, format validity,
    and candidate multiplicity.
    """

    def __init__(
        self,
        tau_high: float = 0.70,     # Below this, OCR fields downgrade to LOW_CONFIDENCE
        tau_abstain: float = 0.45,  # Below this, the extractor completely abstains (NOT_FOUND / UNREADABLE)
        w_token: float = 0.55,
        w_label: float = 0.20,
        w_format: float = 0.25
    ):
        self.tau_high = tau_high
        self.tau_abstain = tau_abstain
        self.w_token = w_token
        self.w_label = w_label
        self.w_format = w_format

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
        page_has_date_ambiguity: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates calibrated correctness probability and assigns the discrete EvidenceState.
        """
        # 1. Format Syntax Check
        is_syntax_valid, syntax_err = validate_field_syntax(field_name, raw_value)

        # 2. Native Vector Handling
        if extraction_method == ExtractionMethod.NATIVE_VECTOR:
            calibrated_prob = 0.98 if is_syntax_valid else 0.75
            if not is_syntax_valid:
                state = EvidenceState.LOW_CONFIDENCE
            elif page_has_date_ambiguity and ("date" in field_name or field_name == "dob"):
                state = EvidenceState.AMBIGUOUS
            else:
                state = EvidenceState.VERIFIED_TEXT

            return {
                "calibrated_confidence": calibrated_prob,
                "evidence_state": state,
                "format_valid": is_syntax_valid,
                "syntax_reason": syntax_err,
                "is_uncertain": state in [EvidenceState.AMBIGUOUS, EvidenceState.LOW_CONFIDENCE],
                "uncertainty_reason": syntax_err if not is_syntax_valid else ("Date format ambiguity (DD/MM vs MM/DD)" if state == EvidenceState.AMBIGUOUS else None)
            }

        # 3. Local OCR Handling
        s_tok = float(token_confidence) if token_confidence is not None else 0.50
        s_tok = max(0.0, min(1.0, s_tok))

        # Label proximity score
        if not label_detected:
            s_lbl = 0.20
        elif label_distance_pt <= 25.0:
            s_lbl = 1.00
        elif label_distance_pt <= 60.0:
            s_lbl = 0.75
        elif label_distance_pt <= 150.0:
            s_lbl = 0.50
        else:
            s_lbl = 0.30

        # Syntax format score
        s_fmt = 1.00 if is_syntax_valid else 0.10

        # Multi-feature linear combination
        raw_prob = (self.w_token * s_tok) + (self.w_label * s_lbl) + (self.w_format * s_fmt)

        # Penalties for ambiguity and token fragmentation
        penalty = 0.0
        if candidate_count > 1:
            penalty += 0.15 * min(3, candidate_count - 1)
        if field_name in ["applicant_name", "father_name"] and supporting_tokens_count < 2:
            penalty += 0.20

        calibrated_prob = max(0.05, min(0.99, raw_prob - penalty))
        calibrated_prob = round(calibrated_prob, 3)

        # Determine EvidenceState
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

        return {
            "calibrated_confidence": calibrated_prob,
            "evidence_state": state,
            "format_valid": is_syntax_valid,
            "syntax_reason": syntax_err,
            "is_uncertain": is_unc,
            "uncertainty_reason": unc_reason
        }
