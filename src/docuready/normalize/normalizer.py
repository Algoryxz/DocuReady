"""
Deterministic Field Normalizers and Canonicalization Routines for DocuReady MVP
"""

import re
import unicodedata
from datetime import datetime, date
from typing import Tuple, Optional, Any, Dict, List

from docuready.domain.enums import MatchGrade

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
    """Normalizes a personal name: strips salutations, symbols, extra spaces, diacritics, returns uppercase."""
    if not s or not isinstance(s, str):
        return ""
    decomposed = unicodedata.normalize("NFKD", s)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    cleaned = stripped.upper()
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
    Compares two names deterministically according to ARCHITECTURE_V2 §4.2:
    - EXACT: identical after case/space/diacritics
    - COMPATIBLE: initial expansion, token reorder, minor spelling/phonetic variant
    - CONFLICT: different surname/given-name tokens
    - AMBIGUOUS: one side unreadable or single token
    """
    s1 = normalize_name(n1)
    s2 = normalize_name(n2)
    if not s1 or not s2:
        return {
            "grade": MatchGrade.AMBIGUOUS,
            "match_grade": MatchGrade.AMBIGUOUS,
            "status": "FAIL",
            "type": "EMPTY_FIELD",
            "similarity": 0.0,
            "notes": "One or both name fields are missing or blank"
        }
    if s1 == s2:
        return {
            "grade": MatchGrade.EXACT,
            "match_grade": MatchGrade.EXACT,
            "status": "PASS",
            "type": "EXACT_MATCH",
            "similarity": 1.0,
            "notes": "Exact character-for-character match"
        }

    toks1 = s1.split()
    toks2 = s2.split()

    # One side single token check (e.g. 'Aarav' vs 'Aarav Sharma')
    if (len(toks1) == 1 or len(toks2) == 1) and not (len(toks1) == 1 and len(toks2) == 1):
        dist = levenshtein_distance(s1, s2)
        max_len = max(len(s1), len(s2))
        sim = 1.0 - (dist / max_len)
        return {
            "grade": MatchGrade.AMBIGUOUS,
            "match_grade": MatchGrade.AMBIGUOUS,
            "status": "REVIEW",
            "type": "SINGLE_TOKEN_NAME",
            "similarity": round(sim, 3),
            "notes": f"One name is a single token ('{s1}' vs '{s2}'); cannot verify full identity"
        }

    t1 = set(toks1)
    t2 = set(toks2)
    jaccard = len(t1 & t2) / len(t1 | t2)
    if jaccard == 1.0:
        return {
            "grade": MatchGrade.COMPATIBLE,
            "match_grade": MatchGrade.COMPATIBLE,
            "status": "PASS",
            "type": "TOKEN_PERMUTATION",
            "similarity": 0.98,
            "notes": "Names contain the exact same tokens in differing order"
        }

    # Initials expansion check (e.g., 'S R NAYAK' vs 'SMRUTI RANJAN NAYAK', 'A. SHARMA' vs 'AARAV SHARMA')
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
                "grade": MatchGrade.COMPATIBLE,
                "match_grade": MatchGrade.COMPATIBLE,
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
            "grade": MatchGrade.COMPATIBLE,
            "match_grade": MatchGrade.COMPATIBLE,
            "status": "REVIEW",
            "type": "MINOR_TYPO_TRANSLITERATION",
            "similarity": round(sim, 3),
            "notes": f"Minor transliteration or spelling distance ({dist} edits: '{s1}' vs '{s2}')"
        }
    elif sim >= 0.70:
        return {
            "grade": MatchGrade.COMPATIBLE,
            "match_grade": MatchGrade.COMPATIBLE,
            "status": "REVIEW",
            "type": "PARTIAL_SIMILARITY",
            "similarity": round(sim, 3),
            "notes": f"Partial phonetic/lexical variation ('{s1}' vs '{s2}')"
        }
    else:
        return {
            "grade": MatchGrade.CONFLICT,
            "match_grade": MatchGrade.CONFLICT,
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

    Two-digit years are mapped to centuries using datetime.strptime(..., '%y') to ensure
    exact agreement with parse_and_normalize_date() (e.g. 68 -> 2068, 69 -> 1969, 70 -> 1970).
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
            p1, p2 = int(parts[0]), int(parts[1])
            year_str = parts[2]
            try:
                if len(year_str) == 2:
                    year = datetime.strptime(year_str, "%y").year
                elif len(year_str) == 4:
                    year = int(year_str)
                else:
                    return []
            except ValueError:
                return []

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
            if (len(parts[0]) == 4 or len(parts[0]) == 2) and 1 <= p2 <= 12 and 1 <= p3 <= 12 and p2 != p3:
                try:
                    if len(parts[0]) == 2:
                        year = datetime.strptime(parts[0], "%y").year
                    else:
                        year = p1
                except ValueError:
                    return []

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


# ----------------- V2 MATCH GRADE COMPARISON FUNCTIONS -----------------
def compare_dates(d1: Any, d2: Any) -> Dict[str, Any]:
    """
    Compares two date values according to ARCHITECTURE_V2 §4.2:
    - EXACT: same date unambiguously
    - AMBIGUOUS: ambiguous format (e.g. DD/MM vs MM/DD), partial or unreadable
    - CONFLICT: different dates
    """
    if d1 is None or d2 is None:
        return {
            "grade": MatchGrade.AMBIGUOUS,
            "match_grade": MatchGrade.AMBIGUOUS,
            "status": "REVIEW",
            "type": "MISSING_DATE",
            "notes": "One or both date fields are missing",
        }
    dt1, status1, amb1 = parse_and_normalize_date(d1)
    dt2, status2, amb2 = parse_and_normalize_date(d2)
    if status1 != "VALID" or status2 != "VALID" or dt1 is None or dt2 is None:
        return {
            "grade": MatchGrade.AMBIGUOUS,
            "match_grade": MatchGrade.AMBIGUOUS,
            "status": "REVIEW",
            "type": "UNPARSEABLE_DATE",
            "notes": f"One or both dates could not be parsed: '{d1}' ({status1}), '{d2}' ({status2})",
        }

    cand1 = get_date_ambiguity_candidates(d1) or [dt1]
    cand2 = get_date_ambiguity_candidates(d2) or [dt2]

    if amb1 or amb2 or len(cand1) > 1 or len(cand2) > 1:
        return {
            "grade": MatchGrade.AMBIGUOUS,
            "match_grade": MatchGrade.AMBIGUOUS,
            "status": "REVIEW",
            "type": "AMBIGUOUS_DATE",
            "candidates_1": [c.isoformat() for c in cand1],
            "candidates_2": [c.isoformat() for c in cand2],
            "notes": f"Ambiguous date format (e.g., DD/MM vs MM/DD): '{d1}' vs '{d2}'",
        }

    if dt1 == dt2:
        return {
            "grade": MatchGrade.EXACT,
            "match_grade": MatchGrade.EXACT,
            "status": "PASS",
            "type": "EXACT_MATCH",
            "notes": f"Dates match identically: {dt1.isoformat()}",
        }
    else:
        return {
            "grade": MatchGrade.CONFLICT,
            "match_grade": MatchGrade.CONFLICT,
            "status": "FAIL",
            "type": "DIFFERING_DATE",
            "notes": f"Dates conflict: {dt1.isoformat()} vs {dt2.isoformat()}",
        }


def compare_identifiers(
    id1: Any,
    id2: Any,
    is_aadhaar: bool = False,
    is_uncertain: bool = False,
) -> Dict[str, Any]:
    """
    Compares identifiers (Aadhaar, certificate numbers, account numbers) per §4.2:
    - EXACT: same digits / normalized alphanumeric characters
    - CONFLICT: different digits
    - AMBIGUOUS: Verhoeff checksum failure (extraction doubt, not identity conflict) or is_uncertain
    """
    if id1 is None or id2 is None:
        return {
            "grade": MatchGrade.AMBIGUOUS,
            "match_grade": MatchGrade.AMBIGUOUS,
            "status": "REVIEW",
            "type": "MISSING_IDENTIFIER",
            "notes": "One or both identifier fields are missing",
        }
    s1 = re.sub(r'[\s\-_/]', '', str(id1).upper())
    s2 = re.sub(r'[\s\-_/]', '', str(id2).upper())
    if not s1 or not s2:
        return {
            "grade": MatchGrade.AMBIGUOUS,
            "match_grade": MatchGrade.AMBIGUOUS,
            "status": "REVIEW",
            "type": "EMPTY_IDENTIFIER",
            "notes": "One or both identifier fields are blank",
        }
    if is_uncertain:
        return {
            "grade": MatchGrade.AMBIGUOUS,
            "match_grade": MatchGrade.AMBIGUOUS,
            "status": "REVIEW",
            "type": "EXTRACTION_UNCERTAIN",
            "notes": "Identifier extraction marked uncertain",
        }
    if is_aadhaar:
        v1 = validate_verhoeff(s1)
        v2 = validate_verhoeff(s2)
        if not v1 or not v2:
            return {
                "grade": MatchGrade.AMBIGUOUS,
                "match_grade": MatchGrade.AMBIGUOUS,
                "status": "REVIEW",
                "type": "CHECKSUM_FAILURE",
                "notes": f"Aadhaar Verhoeff checksum failure (id1_valid={v1}, id2_valid={v2}); treated as extraction doubt, not identity conflict",
            }
    if s1 == s2:
        return {
            "grade": MatchGrade.EXACT,
            "match_grade": MatchGrade.EXACT,
            "status": "PASS",
            "type": "EXACT_MATCH",
            "notes": f"Identifiers match identically: '{s1}'",
        }
    else:
        return {
            "grade": MatchGrade.CONFLICT,
            "match_grade": MatchGrade.CONFLICT,
            "status": "FAIL",
            "type": "DIFFERING_IDENTIFIER",
            "notes": f"Identifiers conflict: '{s1}' vs '{s2}'",
        }


def compare_amounts(
    val1: Any,
    val2: Any,
    tolerance: float = 0.0,
    is_uncertain: bool = False,
) -> Dict[str, Any]:
    """
    Compares currency or numeric amounts per §4.2:
    - EXACT: same value (within 1.0 INR / float precision)
    - COMPATIBLE: within declared tolerance (> 0)
    - CONFLICT: outside tolerance
    - AMBIGUOUS: unit/lakh-crore parse unclear or is_uncertain
    """
    if val1 is None or val2 is None:
        return {
            "grade": MatchGrade.AMBIGUOUS,
            "match_grade": MatchGrade.AMBIGUOUS,
            "status": "REVIEW",
            "type": "MISSING_AMOUNT",
            "notes": "One or both amount fields are missing",
        }
    if is_uncertain:
        return {
            "grade": MatchGrade.AMBIGUOUS,
            "match_grade": MatchGrade.AMBIGUOUS,
            "status": "REVIEW",
            "type": "EXTRACTION_UNCERTAIN",
            "notes": "Amount extraction marked uncertain",
        }
    a1 = normalize_income(val1)
    a2 = normalize_income(val2)
    if a1 is None or a2 is None:
        return {
            "grade": MatchGrade.AMBIGUOUS,
            "match_grade": MatchGrade.AMBIGUOUS,
            "status": "REVIEW",
            "type": "UNPARSEABLE_AMOUNT",
            "notes": f"Amount parsing unclear ('{val1}' vs '{val2}')",
        }
    diff = abs(a1 - a2)
    if diff <= 1.0:
        return {
            "grade": MatchGrade.EXACT,
            "match_grade": MatchGrade.EXACT,
            "status": "PASS",
            "type": "EXACT_MATCH",
            "difference": diff,
            "notes": f"Amounts match identically: {a1:.2f}",
        }
    elif tolerance > 0 and diff <= tolerance:
        return {
            "grade": MatchGrade.COMPATIBLE,
            "match_grade": MatchGrade.COMPATIBLE,
            "status": "REVIEW",
            "type": "WITHIN_TOLERANCE",
            "difference": diff,
            "tolerance": tolerance,
            "notes": f"Amount variation ({diff:.2f}) within declared tolerance ({tolerance:.2f})",
        }
    else:
        return {
            "grade": MatchGrade.CONFLICT,
            "match_grade": MatchGrade.CONFLICT,
            "status": "FAIL",
            "type": "OUTSIDE_TOLERANCE",
            "difference": diff,
            "tolerance": tolerance,
            "notes": f"Amounts conflict: {a1:.2f} vs {a2:.2f} (diff {diff:.2f} > tolerance {tolerance:.2f})",
        }
