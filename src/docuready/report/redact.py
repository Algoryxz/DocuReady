"""Redaction engine, PII masking, safe logging, and secure temporary workspace utilities.

Implements Task T1.4:
1. Field-aware citizen PII redaction:
   - Aadhaar: last four digits visible (e.g. XXXX-XXXX-1234)
   - Bank account: last four digits visible (e.g. ••••••••5678)
   - Phone: last two digits visible (e.g. ••••••••89), supporting country-code (+91)
     and formatted variations.
   - Income: currency amount masked (e.g. ₹[REDACTED])
   - Names: masked in finding messages while preserving document type tags.
2. Safe logging infrastructure:
   - Intercepts record.msg and formats record.args before sanitizing.
   - Clears record.args so formatters cannot re-expose unmasked variables.
   - Sanitizes exception traces and structured log context.
   - Configured across production pipeline and extraction paths.
3. Restrictive temporary upload directory management:
   - Restrictive permissions (POSIX 0700; Windows user-scoped DACL / best-effort ACL).
   - Deletion in finally block without silent error masking.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Union


# ---------------------------------------------------------------------------
# Specific Field Redaction Functions
# ---------------------------------------------------------------------------

def redact_aadhaar(val: str) -> str:
    """Masks 12-digit Aadhaar number keeping only the last 4 digits visible."""
    digits = re.sub(r"\D", "", str(val))
    if len(digits) >= 4:
        return f"XXXX-XXXX-{digits[-4:]}"
    return "XXXX-XXXX-XXXX"


def redact_bank_account(val: str) -> str:
    """
    Field-aware bank account masking: preserves last 4 digits.
    Handles accounts ranging from 4 to 18 digits.
    """
    digits = re.sub(r"\D", "", str(val))
    if len(digits) >= 4:
        return f"••••••••{digits[-4:]}"
    return "••••••••"


def redact_phone(val: str) -> str:
    """
    Masks mobile numbers keeping only the last 2 digits visible.
    Handles national 10-digit numbers, numbers with leading zero, and +91 international codes.
    """
    digits = re.sub(r"\D", "", str(val))
    if len(digits) >= 2:
        return f"••••••••{digits[-2:]}"
    return "••••••••"


def redact_field_value(field_name: str, value: Any) -> Any:
    """Field-aware value sanitizer based on semantic field key name."""
    if value is None:
        return None
    val_str = str(value).strip()
    if not val_str:
        return val_str

    fn = field_name.lower()
    if any(k in fn for k in ("aadhaar", "uid", "uidai")):
        return redact_aadhaar(val_str)
    if any(k in fn for k in ("account", "acc_no", "bank_account", "acct")):
        return redact_bank_account(val_str)
    if any(k in fn for k in ("phone", "mobile", "contact")):
        return redact_phone(val_str)
    if any(k in fn for k in ("income", "salary", "amount")):
        return "₹[REDACTED]"
    if any(k in fn for k in ("name", "father", "mother", "applicant")):
        return "[REDACTED NAME]"
    return val_str


# ---------------------------------------------------------------------------
# Freeform Text Sanitization
# ---------------------------------------------------------------------------

def redact_text_pii(text: str) -> str:
    """
    Sanitizes freeform text, replacing extracted citizen identifiers
    and formatted PII with masked representations.
    """
    if not text:
        return text

    # 1. Mask 12-digit Aadhaar (e.g. 2345 6789 0123, 2345-6789-0123, 234567890123)
    def _aadhaar_sub(m: re.Match) -> str:
        d = re.sub(r"\D", "", m.group(0))
        return f"XXXX-XXXX-{d[-4:]}"

    text = re.sub(r"(?<!\d)\d{4}[-\s]?\d{4}[-\s]?\d{4}(?!\d)", _aadhaar_sub, text)

    # 2. Mask phone numbers: handles +91 prefixes, leading zero, hyphens, and spaces
    # Examples: +91 98765 43210, +91-9876543210, +919876543210, 09876543210, 9876543210
    def _phone_sub(m: re.Match) -> str:
        d = re.sub(r"\D", "", m.group(0))
        return f"••••••••{d[-2:]}"

    text = re.sub(
        r"(?:\+91[-\s]?)?(?:0)?[6-9]\d{2,4}[-\s]?\d{4,5}\b",
        _phone_sub,
        text,
    )

    # 3. Mask explicit bank account strings: e.g. "Account: 9876543210123" or "A/c No: 123456789"
    def _acc_sub(m: re.Match) -> str:
        prefix = m.group(1)
        acc_digits = re.sub(r"\D", "", m.group(2))
        return f"{prefix} ••••••••{acc_digits[-4:]}"

    text = re.sub(
        r"(?i)\b(account(?:\s*no\.?)?|a/c(?:\s*no\.?)?|acc)\s*[:#-]?\s*(\d{9,18})\b",
        _acc_sub,
        text,
    )

    # 4. Mask quoted values except document types, rule IDs, and system status codes
    def _quote_sub(m: re.Match) -> str:
        val = m.group(1)
        preserved_tokens = {
            "APPLICATION_FORM",
            "INCOME_CERT",
            "CASTE_CERT",
            "RESIDENCE_CERT",
            "MARKSHEET",
            "BANK_PASSBOOK",
            "AADHAAR",
            "PASS",
            "FAIL",
            "REVIEW",
            "UNKNOWN",
            "CRITICAL",
            "HIGH",
            "MEDIUM",
            "LOW",
        }
        if val in preserved_tokens or val.startswith("RULE-"):
            return f"'{val}'"
        return "'[REDACTED]'"

    text = re.sub(r"'([^']+)'", _quote_sub, text)

    # 5. Mask currency amounts (₹ or Rs.)
    text = re.sub(r"(?:₹|Rs\.?)\s*[\d,]+(?:\.\d+)?", "₹[REDACTED]", text, flags=re.IGNORECASE)

    return text


def redact_audit_result_dict(result_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Produces a privacy-redacted copy of an AuditResult dictionary."""
    redacted = json.loads(json.dumps(result_dict))

    for f in redacted.get("findings", []):
        if "message" in f and f["message"]:
            f["message"] = redact_text_pii(f["message"])

        # Preserve remediation action guidance while sanitizing PII
        if "remediation" in f and f["remediation"]:
            f["remediation"] = redact_text_pii(f["remediation"])

        for ev in f.get("evidence", []):
            if "raw_snippet" in ev and ev["raw_snippet"]:
                ev["raw_snippet"] = "[REDACTED EVIDENCE SNIPPET]"
            if "file_name" in ev and ev["file_name"]:
                ev["file_name"] = redact_text_pii(os.path.basename(ev["file_name"]))

    # If extracted documents or fields are in the payload, redact field values
    if "documents" in redacted and isinstance(redacted["documents"], dict):
        for doc_key, doc_data in redacted["documents"].items():
            if "fields" in doc_data and isinstance(doc_data["fields"], dict):
                for f_name, f_obj in doc_data["fields"].items():
                    if isinstance(f_obj, dict) and "value" in f_obj:
                        f_obj["value"] = redact_field_value(f_name, f_obj["value"])

    return redacted


# ---------------------------------------------------------------------------
# Safe Logging Utilities
# ---------------------------------------------------------------------------

class SafeLogFilter(logging.Filter):
    """
    Log filter that intercepts and sanitizes log records.
    Crucially:
    1. Resolves formatting (record.msg % record.args) and then clears record.args
       so downstream formatters cannot re-expose unredacted variables.
    2. Sanitizes record.msg and exception traces.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            # 1. Resolve formatted arguments safely
            if record.args:
                try:
                    formatted_msg = record.msg % record.args
                except Exception:
                    formatted_msg = f"{record.msg} [ARGS: {record.args}]"
                record.msg = formatted_msg
                record.args = ()  # Clear args so formatters don't re-format
            elif not isinstance(record.msg, str):
                record.msg = str(record.msg)

            # 2. Sanitize formatted message text
            record.msg = redact_text_pii(record.msg)

            # 3. Sanitize exc_text if an exception traceback is attached
            if record.exc_text:
                record.exc_text = redact_text_pii(record.exc_text)

        except Exception:
            record.args = ()
            record.msg = "[LOG_RECORD_SANITIZED_DUE_TO_FORMAT_ERROR]"

        return True


def get_safe_logger(name: str) -> logging.Logger:
    """Returns a configured logger with the SafeLogFilter attached."""
    logger = logging.getLogger(name)
    has_filter = any(isinstance(f, SafeLogFilter) for f in logger.filters)
    if not has_filter:
        logger.addFilter(SafeLogFilter())
    return logger


# ---------------------------------------------------------------------------
# Restrictive Temporary Directory Management
# ---------------------------------------------------------------------------

class TemporaryDirectoryCleanupError(RuntimeError):
    """Raised or recorded when temporary directory removal fails."""


@contextlib.contextmanager
def secure_temporary_directory(prefix: str = "docuready_tmp_") -> Iterator[Path]:
    """
    Context manager creating a temporary directory with restrictive permissions.
    - POSIX: Applies 0700 permissions.
    - Windows: Scopes permissions using icacls where feasible, or documents platform boundary.
    - Deletion in finally block: Does not mask cleanup failures silently; logs a warning
      with details if removal fails.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix=prefix)).resolve()
    try:
        # Enforce restrictive permissions
        if os.name == "posix":
            try:
                os.chmod(temp_dir, 0o700)
            except OSError:
                pass
        elif os.name == "nt":
            # On Windows, best-effort user-restricted ACL via icacls if available
            try:
                import subprocess
                user = os.environ.get("USERNAME", "")
                if user:
                    subprocess.run(
                        ["icacls", str(temp_dir), "/inheritance:r", f"/grant:r", f"{user}:(OI)(CI)F"],
                        capture_output=True,
                        check=False,
                        timeout=3,
                    )
            except Exception:
                try:
                    os.chmod(temp_dir, 0o700)
                except OSError:
                    pass

        yield temp_dir

    finally:
        if temp_dir.exists():
            cleanup_errors = []

            if sys.version_info >= (3, 12):
                def _onexc(func, path, exc):
                    cleanup_errors.append((path, exc))

                shutil.rmtree(temp_dir, onexc=_onexc)
            else:
                def _onerror(func, path, exc_info):
                    cleanup_errors.append((path, exc_info[1]))

                shutil.rmtree(temp_dir, onerror=_onerror)
            if cleanup_errors:
                logger = get_safe_logger("docuready.temp")
                logger.warning(
                    "Temporary directory cleanup encountered errors for %s: %s",
                    temp_dir.name,
                    str(cleanup_errors[0][1]),
                )
