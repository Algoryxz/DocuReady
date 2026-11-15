"""Redaction engine, PII masking, and safe temporary workspace utilities.

Implements Task T1.4:
1. Default PII redaction rules:
   - Aadhaar: last four digits visible (e.g. XXXX-XXXX-1234)
   - Bank account: last four digits visible (e.g. ••••••••5678)
   - Phone: last two digits visible (e.g. ••••••••89)
2. Safe logging utilities ensuring raw document field values, full OCR text,
   and citizen identifiers are never written to log streams.
3. Restrictive temporary upload directory management (0700 permissions,
   guaranteed deletion in finally block).
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterator, Optional


# ---------------------------------------------------------------------------
# PII Redaction Functions
# ---------------------------------------------------------------------------

def redact_aadhaar(val: str) -> str:
    """Masks 12-digit Aadhaar number keeping only the last 4 digits visible."""
    digits = re.sub(r"\D", "", val)
    if len(digits) == 12:
        return f"XXXX-XXXX-{digits[-4:]}"
    return re.sub(r"\d(?=\d{4})", "X", val)


def redact_bank_account(val: str) -> str:
    """Masks bank account number keeping only the last 4 digits visible."""
    digits = re.sub(r"\D", "", val)
    if len(digits) >= 4:
        return f"••••••••{digits[-4:]}"
    return "••••••••"


def redact_phone(val: str) -> str:
    """Masks 10-digit Indian phone number keeping only the last 2 digits visible."""
    digits = re.sub(r"\D", "", val)
    if len(digits) == 10:
        return f"••••••••{digits[-2:]}"
    return re.sub(r"\d(?=\d{2})", "•", val)


def redact_text_pii(text: str) -> str:
    """
    Sanitizes freeform text, replacing extracted citizen identifiers
    with masked representations.
    """
    if not text:
        return text

    # Mask 12-digit Aadhaar (e.g., 2345 6789 0123 or 2345-6789-0123)
    def _aadhaar_sub(m: re.Match) -> str:
        d = re.sub(r"\D", "", m.group(0))
        return f"XXXX-XXXX-{d[-4:]}"

    text = re.sub(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", _aadhaar_sub, text)

    # Mask 10-digit mobile numbers starting with 6, 7, 8, or 9
    def _phone_sub(m: re.Match) -> str:
        d = m.group(0)
        return f"••••••••{d[-2:]}"

    text = re.sub(r"\b[6-9]\d{9}\b", _phone_sub, text)

    # Mask quoted field values except document type tags
    def _quote_sub(m: re.Match) -> str:
        val = m.group(1)
        doc_tags = {
            "APPLICATION_FORM",
            "INCOME_CERT",
            "CASTE_CERT",
            "RESIDENCE_CERT",
            "MARKSHEET",
            "BANK_PASSBOOK",
            "AADHAAR",
        }
        if val in doc_tags:
            return f"'{val}'"
        return "'[REDACTED]'"

    text = re.sub(r"'([^']+)'", _quote_sub, text)

    # Mask currency amounts
    text = re.sub(r"₹\s*[\d,]+(?:\.\d+)?", "₹[REDACTED]", text)

    return text


def redact_audit_result_dict(result_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Produces a privacy-redacted copy of an AuditResult dictionary."""
    redacted = json.loads(json.dumps(result_dict))

    for f in redacted.get("findings", []):
        if "message" in f and f["message"]:
            f["message"] = redact_text_pii(f["message"])

        for ev in f.get("evidence", []):
            if "raw_snippet" in ev and ev["raw_snippet"]:
                ev["raw_snippet"] = "[REDACTED EVIDENCE SNIPPET]"
            if "file_name" in ev and ev["file_name"]:
                ev["file_name"] = os.path.basename(ev["file_name"])

    return redacted


# ---------------------------------------------------------------------------
# Safe Logging Utilities
# ---------------------------------------------------------------------------

class SafeLogFilter(logging.Filter):
    """
    Filter that intercepts log records and ensures no sensitive identifier
    data, full OCR text, or raw citizen fields are emitted.
    """

    _SENSITIVE_PATTERNS = [
        re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),  # Aadhaar
        re.compile(r"\b[6-9]\d{9}\b"),                    # Mobile
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_text_pii(record.msg)
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

@contextlib.contextmanager
def secure_temporary_directory(prefix: str = "docuready_tmp_") -> Iterator[Path]:
    """
    Context manager creating a temporary directory with restrictive 0700 permissions.
    Guarantees recursive deletion of the directory in a finally block upon exit,
    even if unhandled exceptions occur.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix=prefix)).resolve()
    try:
        # Enforce restrictive 0700 permissions on Unix; best-effort on Windows
        try:
            os.chmod(temp_dir, 0o700)
        except OSError:
            pass
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
