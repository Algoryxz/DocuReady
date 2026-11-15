"""
Deterministic Field Normalizers and Canonicalization Routines for DocuReady MVP
"""

import re
from datetime import datetime, date
from typing import Tuple, Optional, Any, Dict

# ----------------- VERHOEFF CHECKSUM (ISO/IEC 7064) -----------------
D_TABLE = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 6, 7, 8, 9, 0, 1, 2, 3, 4],
    [6, 7, 8, 9, 5, 1, 2, 3, 4, 0],
    [7, 8, 9, 5, 6, 2, 3, 4, 0, 1],
    [8, 9, 5, 6, 7, 3, 4, 0, 1, 2],
    [9, 5, 6, 7, 8, 4, 0, 1, 2, 3]
]

P_TABLE = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 0, 7],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
]

def validate_verhoeff(num_str: str) -> bool:
    """Validates 12-digit number against Verhoeff checksum algorithm."""
    if not num_str or not str(num_str).strip().isdigit() or len(str(num_str).strip()) != 12:
        return False
    c = 0
    inv = str(num_str).strip()[::-1]
    for i, ch in enumerate(inv):
        c = D_TABLE[c][P_TABLE[i % 8][int(ch)]]
    return c == 0

def generate_verhoeff_12(prefix_11: str) -> str:
    """Appends the correct check digit to an 11-digit prefix to form a valid 12-digit number."""
    prefix = str(prefix_11)[:11]
    for d in range(10):
        cand = f"{prefix}{d}"
        if validate_verhoeff(cand):
            return cand
    return f"{prefix}0"


# ----------------- NAME NORMALIZATION & COMPARISON -----------------
HONORIFICS_PATTERN = r'\b(MR|MS|MRS|SHRI|SMT|DR|KUMAR|KUMARI|MISS|MD|MOHD|SRI|SMTI)\b'

def normalize_name(s: Optional[str]) -> str:
    """Normalizes a personal name: strips salutations, symbols, extra spaces, returns uppercase."""
    if not s or not isinstance(s, str):
        return ""
    cleaned = s.upper()
    cleaned = re.sub(HONORIFICS_PATTERN, ' ', cleaned)
    cleaned = re.sub(r'[^A-Z\s]', ' ', cleaned)
    tokens = cleaned.split()
    return " ".join(tokens)

def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculates Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            ins = prev[j + 1] + 1
            delete = curr[j] + 1
            sub = prev[j] + (0 if c1 == c2 else 1)
            curr.append(min(ins, delete, sub))
        prev = curr
    return prev[-1]

def compare_names(n1: str, n2: str) -> Dict[str, Any]:
    """
    Compares two names deterministically:
    Returns dict with match_status ('PASS', 'REVIEW', 'FAIL'), type, similarity, and notes.
    """
    s1 = normalize_name(n1)
    s2 = normalize_name(n2)
    if not s1 or not s2:
        return {
            "status": "FAIL",
            "type": "EMPTY_FIELD",
            "similarity": 0.0,
            "notes": "One or both name fields are missing or blank"
        }
    if s1 == s2:
        return {
            "status": "PASS",
            "type": "EXACT_MATCH",
            "similarity": 1.0,
            "notes": "Exact character-for-character match"
        }

    t1 = set(s1.split())
    t2 = set(s2.split())
    jaccard = len(t1 & t2) / len(t1 | t2)
    if jaccard == 1.0:
        return {
            "status": "PASS",
            "type": "TOKEN_PERMUTATION",
            "similarity": 0.98,
            "notes": "Names contain the exact same tokens in differing order"
        }

    # Initials expansion check (e.g., 'S R NAYAK' vs 'SMRUTI RANJAN NAYAK')
    toks1 = s1.split()
    toks2 = s2.split()
    if len(toks1) == len(toks2) and len(toks1) > 1:
        initials_match = True
        has_initial = False
        for a, b in zip(toks1, toks2):
            if len(a) == 1 or len(b) == 1:
                has_initial = True
                if a[0] != b[0]:
                    initials_match = False
                    break
            elif a != b:
                initials_match = False
                break
        if initials_match and has_initial:
            return {
                "status": "REVIEW",
                "type": "INITIALS_EXPANSION",
                "similarity": 0.88,
                "notes": f"Name contains single-letter initials ('{s1}' vs '{s2}')"
            }

    dist = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    sim = 1.0 - (dist / max_len)

    if dist <= 2 and sim >= 0.82:
        return {
            "status": "REVIEW",
            "type": "MINOR_TYPO_TRANSLITERATION",
            "similarity": round(sim, 3),
            "notes": f"Minor transliteration or spelling distance ({dist} edits: '{s1}' vs '{s2}')"
        }
    elif sim >= 0.70:
        return {
            "status": "REVIEW",
            "type": "PARTIAL_SIMILARITY",
            "similarity": round(sim, 3),
            "notes": f"Partial phonetic/lexical variation ('{s1}' vs '{s2}')"
        }
    else:
        return {
            "status": "FAIL",
            "type": "CONTRADICTORY_NAME",
            "similarity": round(sim, 3),
            "notes": f"Applicant names conflict distinctly: '{n1}' vs '{n2}'"
        }


# ----------------- DATE NORMALIZATION & PARSING -----------------
DATE_FORMATS = [
    "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y",
    "%d/%m/%y", "%d-%m-%y",
    "%d-%b-%Y", "%d %b %Y", "%d %B %Y",
    "%Y/%m/%d"
]

def parse_and_normalize_date(date_str: Any) -> Tuple[Optional[date], str, bool]:
    """
    Parses arbitrary date representation.
    Returns: (parsed_date, parse_status, is_ambiguous)
    parse_status: 'VALID', 'INVALID_FORMAT', 'UNREADABLE', 'EMPTY'
    """
    if date_str is None:
        return None, "EMPTY", False
    if isinstance(date_str, (date, datetime)):
        dt = date_str if isinstance(date_str, date) else date_str.date()
        return dt, "VALID", False

    s = str(date_str).strip()
    if not s:
        return None, "EMPTY", False
    if '?' in s or 'X' in s.upper():
        return None, "UNREADABLE", False

    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(s, fmt).date()
            # Check ambiguity: day <= 12 and month <= 12
            parts = re.split(r'[/.-]', s)
            ambiguous = False
            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                p1, p2 = int(parts[0]), int(parts[1])
                if 1 <= p1 <= 12 and 1 <= p2 <= 12 and p1 != p2:
                    ambiguous = True
            return dt, "VALID", ambiguous
        except ValueError:
            continue

    return None, "INVALID_FORMAT", False


def get_date_ambiguity_candidates(date_str: Any) -> List[date]:
    """
    Parses an ambiguous date string into its candidate interpretations (DD/MM vs MM/DD).
    Returns a list of unique valid date objects. If the date is unambiguous, malformed,
    or unreadable, returns the single parsed date or an empty list.
    """
    if date_str is None:
        return []
    if isinstance(date_str, (date, datetime)):
        dt = date_str if isinstance(date_str, date) else date_str.date()
        return [dt]

    s = str(date_str).strip()
    if not s or '?' in s or 'X' in s.upper():
        return []

    parts = re.split(r'[/.-]', s)
    if len(parts) == 3:
        # Case A: P1/P2/P3 where P1 and P2 are day/month or month/day and P3 is year
        if parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit():
            p1, p2, p3 = int(parts[0]), int(parts[1]), int(parts[2])
            year = p3
            if year < 100:
                year += 2000 if year < 70 else 1900
            if 1 <= p1 <= 12 and 1 <= p2 <= 12 and p1 != p2:
                candidates: List[date] = []
                try:
                    candidates.append(date(year, p2, p1))  # DD/MM/YYYY: p1=day, p2=month
                except ValueError:
                    pass
                try:
                    candidates.append(date(year, p1, p2))  # MM/DD/YYYY: p1=month, p2=day
                except ValueError:
                    pass
                if len(candidates) == 2:
                    return candidates

        # Case B: YYYY/P2/P3 where P2 and P3 are month/day or day/month
        if parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit():
            p1, p2, p3 = int(parts[0]), int(parts[1]), int(parts[2])
            if len(parts[0]) == 4 and 1 <= p2 <= 12 and 1 <= p3 <= 12 and p2 != p3:
                year = p1
                candidates = []
                try:
                    candidates.append(date(year, p2, p3))
                except ValueError:
                    pass
                try:
                    candidates.append(date(year, p3, p2))
                except ValueError:
                    pass
                if len(candidates) == 2:
                    return candidates

    parsed, status, _ = parse_and_normalize_date(date_str)
    if parsed and status == "VALID":
        return [parsed]
    return []


# ----------------- INCOME NORMALIZATION -----------------
def normalize_income(val: Any) -> Optional[float]:
    """
    Parses currency or income expressions into float value in Indian Rupees (INR).
    Handles '₹ 1,80,000/-', '1.8 LPA', '2.5 Lakh', '180000', etc.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)

    s = str(val).upper().replace(",", "").replace("/-", "").replace("RS.", "").replace("₹", "").strip()
    if not s:
        return None

    if "LPA" in s or "LAKH" in s or "LAC" in s:
        match = re.search(r"[\d.]+", s)
        if match:
            try:
                return round(float(match.group(0)) * 100000.0, 2)
            except ValueError:
                return None

    # Standard integer/float extract
    match = re.search(r"\d+(\.\d+)?", s)
    if match:
        try:
            return round(float(match.group(0)), 2)
        except ValueError:
            return None
    return None


# ----------------- IFSC CODE VALIDATION -----------------
def validate_ifsc_code(ifsc: Optional[str]) -> bool:
    """RBI standard format: 4 alphabetic characters, followed by 0, followed by 6 alphanumeric characters."""
    if not ifsc or not isinstance(ifsc, str):
        return False
    return bool(re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', ifsc.strip().upper()))


# ----------------- CERTIFICATE NUMBER NORMALIZATION -----------------
def normalize_cert_number(cert_no: Optional[str]) -> str:
    """Normalizes certificate/registration number: strips whitespace, converts to uppercase."""
    if not cert_no or not isinstance(cert_no, str):
        return ""
    return re.sub(r'[\s\-_]', '', cert_no.strip().upper())
