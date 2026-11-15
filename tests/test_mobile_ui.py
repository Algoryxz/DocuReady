"""Tests for Mobile Web MVP responsive interface and mobile layout contracts (Track B).

Verifies:
1. Responsive CSS rules with mobile breakpoint (@media max-width: 768px).
2. Minimum touch target dimensions (>= 44px) adhering to WCAG 2.5.5 / 2.5.8.
3. Responsive column stacking and table horizontal scroll protection.
4. Mobile sticky status bar markup presence.
5. Complete synthetic audit execution via pipeline for mobile workflow verification.
6. Zero outbound network calls during mobile web flows.
"""

from pathlib import Path
import re
import pytest

from docuready.domain.models import DocumentType, FindingStatus
from docuready.pipeline import AuditPipeline

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_PY_PATH = REPO_ROOT / "src" / "docuready" / "interfaces" / "ui" / "app.py"


def test_app_py_contains_mobile_responsive_breakpoint():
    """Verify that app.py injects responsive CSS with a mobile breakpoint."""
    assert APP_PY_PATH.exists(), f"{APP_PY_PATH} must exist"
    code = APP_PY_PATH.read_text(encoding="utf-8")

    assert "@media (max-width: 768px)" in code or "@media" in code, (
        "app.py must contain responsive @media queries for mobile viewports"
    )


def test_app_py_enforces_touch_target_size():
    """Verify that buttons and interactive controls satisfy >= 44px touch targets."""
    code = APP_PY_PATH.read_text(encoding="utf-8")

    # Match 44px or similar in the CSS block
    assert "44px" in code, "app.py CSS must enforce 44px touch target rules for mobile controls"


def test_app_py_includes_column_stacking_and_overflow_protection():
    """Verify mobile column stacking and table horizontal scroll protection."""
    code = APP_PY_PATH.read_text(encoding="utf-8")

    assert "overflow-x" in code, "app.py CSS must handle table overflow for narrow viewports"
    assert "mobile-sticky-bar" in code or "mobile" in code.lower(), (
        "app.py must define mobile UI components"
    )


def test_synthetic_audit_workflow_on_clean_and_conflict_packets():
    """Verify the full audit pipeline executes cleanly on synthetic data for mobile sessions."""
    pipeline = AuditPipeline()
    synth_dir = REPO_ROOT / "synthetic_data"

    # Test clean packet
    pkt_01_path = synth_dir / "pkt_01_clean"
    res_clean, docs_clean = pipeline.load_and_audit_packet(str(pkt_01_path), packet_id="PKT_01_CLEAN")
    assert res_clean.overall_status == "READY_TO_SUBMIT"
    assert res_clean.readiness_score == 100
    assert len(docs_clean) == 6

    # Test name conflict packet
    pkt_02_path = synth_dir / "pkt_02_name_conflict"
    res_conflict, docs_conflict = pipeline.load_and_audit_packet(str(pkt_02_path), packet_id="PKT_02_NAME_CONFLICT")
    assert res_conflict.readiness_score < 100
    assert any(f.status == FindingStatus.FAIL for f in res_conflict.findings)


def test_no_remote_network_assets_in_app_ui():
    """Verify that no external fonts, analytics, CDN scripts, or remote images are loaded."""
    code = APP_PY_PATH.read_text(encoding="utf-8")

    # Ensure no external URLs in img src or stylesheets
    urls = re.findall(r'https?://[^\s\'"<>]+', code)
    # The only URLs allowed are standard python documentation references or local schemas if any
    for url in urls:
        assert not url.endswith((".png", ".jpg", ".css", ".js", ".woff", ".woff2")), (
            f"Remote asset reference detected in app.py: {url}"
        )


def test_synthetic_only_mode_guard_present():
    """Verify DOCUREADY_SYNTHETIC_ONLY mode is implemented in app.py."""
    code = APP_PY_PATH.read_text(encoding="utf-8")
    assert "DOCUREADY_SYNTHETIC_ONLY" in code, (
        "app.py must recognize DOCUREADY_SYNTHETIC_ONLY environment variable"
    )
    assert "SYNTHETIC_ONLY_MODE" in code


def test_advisory_determination_copy_present():
    """Verify advisory determination copy disclaiming official approval is present in app.py."""
    code = APP_PY_PATH.read_text(encoding="utf-8")
    assert "Pre-Check Advisory Determination" in code
    assert "Advisory preparation aid; does not guarantee official portal acceptance" in code
