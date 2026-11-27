import re
from typing import List, Dict, Any, Optional, Tuple

def resolve_narrow_gutter_cell_token(
    cell_words: List[Dict[str, Any]],
    header_text: str,
    col_pattern: Optional[str],
    field_name: str,
    clean_val: str,
) -> Tuple[str, bool, float, Optional[str]]:
    """
    Resolves multi-token narrow-gutter cell bleed via localized spatial association.
    If a cell contains multiple tokens (e.g. '85000 8500') due to narrow gutter fusion,
    checks if col_pattern or field_name matches a specific sub-column header.
    Returns: (resolved_value, is_resolved, sub_conf, reason)
    """
    tokens = clean_val.split()
    if len(tokens) <= 1 or not cell_words or len(cell_words) < len(tokens):
        return clean_val, False, 0.0, None

    # Check if header contains multiple distinct sub-headers (e.g. separated by '_', '|', '/', '&', or multiple labeled amounts)
    sub_headers = [h.strip() for h in re.split(r"[_|/]|(?<=[)])\s+(?=[A-Z])", header_text) if h.strip()]
    
    if len(sub_headers) >= 2 and len(tokens) == 2:
        # Check which sub-header matches col_pattern
        target = col_pattern or field_name
        target_norm = target.lower().replace("_", " ")
        
        match_idx = -1
        for idx, sh in enumerate(sub_headers[:2]):
            sh_norm = sh.lower()
            if any(term in sh_norm for term in target_norm.split()):
                match_idx = idx
                break
                
        if match_idx != -1 and match_idx < len(cell_words):
            # Verify spatial separation between tokens
            w1 = cell_words[0]
            w2 = cell_words[1]
            gap = w2["left"] - w1["right"]
            if gap >= 8:  # Clear interior gap between the numbers
                resolved_token = tokens[match_idx]
                token_conf = cell_words[match_idx].get("conf", 75.0)
                # Boost confidence if exact sub-header match
                return resolved_token, True, max(token_conf, 70.0), None

    return clean_val, False, 0.0, "Multiple whitespace-separated tokens detected in numeric cell (gutter bleed)"
