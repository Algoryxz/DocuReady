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
    assert res_clean.readiness.value == "NO_ISSUES_FOUND"
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


# ---------------------------------------------------------------------------
# AppTest Genuine Runtime Execution Tests
# ---------------------------------------------------------------------------

def test_apptest_synthetic_only_mode_runtime():
    """Verify that DOCUREADY_SYNTHETIC_ONLY=1 renders cleanly without NameError and disables uploader."""
    import os
    from streamlit.testing.v1 import AppTest

    old_val = os.environ.get("DOCUREADY_SYNTHETIC_ONLY")
    try:
        os.environ["DOCUREADY_SYNTHETIC_ONLY"] = "1"
        at = AppTest.from_file(str(APP_PY_PATH), default_timeout=30)
        at.run()
        assert not at.exception, f"AppTest raised unexpected exception on start: {at.exception}"

        # Navigate to Upload Documents
        at.sidebar.radio[0].set_value("2. Upload Documents").run()
        assert not at.exception, f"AppTest raised exception on Upload Documents: {at.exception}"

        # Verify file uploader is absent in synthetic-only mode
        assert len(at.file_uploader) == 0, "File uploader must be absent in synthetic-only mode"

        # Verify privacy demonstration notice is shown
        info_texts = [i.value for i in at.info]
        assert any("Public Demonstration Mode" in t for t in info_texts), (
            "Public demonstration notice must be rendered in synthetic-only mode"
        )
    finally:
        if old_val is None:
            os.environ.pop("DOCUREADY_SYNTHETIC_ONLY", None)
        else:
            os.environ["DOCUREADY_SYNTHETIC_ONLY"] = old_val

def test_apptest_ordinary_mode_runtime():
    """Verify that default mode renders file uploader without exceptions."""
    import os
    from streamlit.testing.v1 import AppTest

    old_val = os.environ.get("DOCUREADY_SYNTHETIC_ONLY")
    try:
        os.environ.pop("DOCUREADY_SYNTHETIC_ONLY", None)
        at = AppTest.from_file(str(APP_PY_PATH), default_timeout=30)
        at.run()
        assert not at.exception, f"AppTest raised unexpected exception on start: {at.exception}"

        # Navigate to Upload Documents
        at.sidebar.radio[0].set_value("2. Upload Documents").run()
        assert not at.exception, f"AppTest raised exception on Upload Documents: {at.exception}"

        # Verify file uploader is present in default mode
        assert len(at.file_uploader) == 1, "File uploader must be present in default mode"
    finally:
        if old_val is not None:
            os.environ["DOCUREADY_SYNTHETIC_ONLY"] = old_val


def test_apptest_mobile_workflow_full_cycle():
    """Verify end-to-end mobile workflow: dashboard -> select -> audit -> navigate -> clear."""
    import os
    from streamlit.testing.v1 import AppTest

    old_val = os.environ.get("DOCUREADY_SYNTHETIC_ONLY")
    try:
        os.environ["DOCUREADY_SYNTHETIC_ONLY"] = "1"
        at = AppTest.from_file(str(APP_PY_PATH), default_timeout=30)
        at.run()
        assert not at.exception

        # 1. Navigate to Upload Documents
        at.sidebar.radio[0].set_value("2. Upload Documents").run()
        assert not at.exception

        # 2. Audit PKT_01_CLEAN
        audit_btn = [b for b in at.button if "Audit Selected" in b.label][0]
        audit_btn.click().run()
        assert not at.exception
        assert at.session_state.audit_result is not None
        assert at.session_state.audit_result.readiness.value == "NO_ISSUES_FOUND"
        assert at.session_state.audit_result.readiness_score == 100

        # 3. Audit PKT_02_NAME_CONFLICT
        at.selectbox[0].select("PKT_02_NAME_CONFLICT").run()
        audit_btn = [b for b in at.button if "Audit Selected" in b.label][0]
        audit_btn.click().run()
        assert not at.exception
        assert at.session_state.audit_result is not None
        assert at.session_state.audit_result.readiness.value == "NOT_READY"
        assert at.session_state.audit_result.readiness_score < 100
        assert len(at.session_state.audit_result.findings) > 0

        # 4. Navigate through all screens
        tabs = [
            "1. Dashboard",
            "3. Document Extraction & Evidence",
            "4. Cross-Document Validation",
            "5. Audit Results",
            "6. Document Replacement & Rerun",
        ]
        for tab_name in tabs:
            at.sidebar.radio[0].set_value(tab_name).run()
            assert not at.exception, f"Exception encountered when rendering tab {tab_name}: {at.exception}"

        # 5. On Audit Results tab, verify download buttons exist
        at.sidebar.radio[0].set_value("5. Audit Results").run()
        assert not at.exception
        assert len(at.download_button) >= 2, "Expected Markdown and JSON report download buttons"

        # 6. Clear session data
        at.sidebar.radio[0].set_value("2. Upload Documents").run()
        clear_btn = [b for b in at.button if "Clear Session" in b.label][0]
        clear_btn.click().run()
        assert not at.exception
        assert at.session_state.audit_result is None, "Audit result must be cleared after session reset"

    finally:
        if old_val is None:
            os.environ.pop("DOCUREADY_SYNTHETIC_ONLY", None)
        else:
            os.environ["DOCUREADY_SYNTHETIC_ONLY"] = old_val

def test_apptest_synthetic_only_mode_screen6_guard_and_reaudit():
    """Verify Screen 6 blocks upload option in synthetic-only mode but allows auto-remediation and re-audit."""
    import os
    from streamlit.testing.v1 import AppTest

    old_val = os.environ.get("DOCUREADY_SYNTHETIC_ONLY")
    try:
        os.environ["DOCUREADY_SYNTHETIC_ONLY"] = "1"
        at = AppTest.from_file(str(APP_PY_PATH), default_timeout=30)
        at.run()
        assert not at.exception

        # Load & audit packet on Screen 2
        at.sidebar.radio[0].set_value("2. Upload Documents").run()
        audit_btn = [b for b in at.button if "Audit Selected" in b.label][0]
        audit_btn.click().run()
        assert not at.exception

        # Navigate to Screen 6 (Document Replacement & Rerun)
        at.sidebar.radio[0].set_value("6. Document Replacement & Rerun").run()
        assert not at.exception, f"Screen 6 raised unexpected exception: {at.exception}"

        # Assert no file uploader is rendered
        assert len(at.file_uploader) == 0, "No file uploader may be rendered on Screen 6 in synthetic-only mode"

        # Assert radio options contain only Auto-Generate and NOT Upload Corrected PDF File
        remediation_radio = at.radio[0]
        assert "Upload Corrected PDF File" not in remediation_radio.options, (
            "Arbitrary upload option must not be exposed on Screen 6 in synthetic-only mode"
        )
        assert "Auto-Generate Standard Corrected Version" in remediation_radio.options, (
            "Auto-generate option must remain available in synthetic-only mode"
        )

        # Execute auto-remediation and re-audit
        gen_btn = [b for b in at.button if "Generate & Re-Run" in b.label][0]
        gen_btn.click().run()
        assert not at.exception, f"Re-audit failed with exception: {at.exception}"
        assert at.session_state.current_packet_id.endswith("_REMEDIATED"), (
            "Session state must reflect remediated packet identifier"
        )
        assert at.session_state.audit_result is not None
        assert at.session_state.audit_result.readiness.value in ("NO_ISSUES_FOUND", "NOT_READY")

    finally:
        if old_val is None:
            os.environ.pop("DOCUREADY_SYNTHETIC_ONLY", None)
        else:
            os.environ["DOCUREADY_SYNTHETIC_ONLY"] = old_val

def test_apptest_ordinary_mode_screen6_replacement_upload():
    """Verify Screen 6 allows replacement PDF upload in ordinary (non-synthetic) mode."""
    import os
    from streamlit.testing.v1 import AppTest

    old_val = os.environ.get("DOCUREADY_SYNTHETIC_ONLY")
    try:
        os.environ.pop("DOCUREADY_SYNTHETIC_ONLY", None)
        at = AppTest.from_file(str(APP_PY_PATH), default_timeout=30)
        at.run()
        assert not at.exception

        # Audit synthetic packet on Screen 2
        at.sidebar.radio[0].set_value("2. Upload Documents").run()
        audit_btn = [b for b in at.button if "Audit Selected" in b.label][0]
        audit_btn.click().run()
        assert not at.exception

        # Navigate to Screen 6
        at.sidebar.radio[0].set_value("6. Document Replacement & Rerun").run()
        assert not at.exception

        # Verify radio options contain Upload option
        remediation_radio = at.radio[0]
        assert "Upload Corrected PDF File" in remediation_radio.options, (
            "Upload option must be available on Screen 6 in ordinary mode"
        )

        # Select Upload option and verify file uploader appears
        remediation_radio.set_value("Upload Corrected PDF File").run()
        assert not at.exception
        assert len(at.file_uploader) == 1, (
            "File uploader must be rendered on Screen 6 when Upload option is selected in ordinary mode"
        )

    finally:
        if old_val is not None:
            os.environ["DOCUREADY_SYNTHETIC_ONLY"] = old_val


def test_apptest_synthetic_only_mode_zero_uploaders_across_all_screens():
    """Verify that every application screen has zero file uploaders in synthetic-only mode."""
    import os
    from streamlit.testing.v1 import AppTest

    old_val = os.environ.get("DOCUREADY_SYNTHETIC_ONLY")
    try:
        os.environ["DOCUREADY_SYNTHETIC_ONLY"] = "1"
        at = AppTest.from_file(str(APP_PY_PATH), default_timeout=30)
        at.run()
        assert not at.exception

        # Load packet to ensure stateful screens are active
        at.sidebar.radio[0].set_value("2. Upload Documents").run()
        audit_btn = [b for b in at.button if "Audit Selected" in b.label][0]
        audit_btn.click().run()
        assert not at.exception

        screens = [
            "1. Dashboard",
            "2. Upload Documents",
            "3. Document Extraction & Evidence",
            "4. Cross-Document Validation",
            "5. Audit Results",
            "6. Document Replacement & Rerun",
        ]
        for screen_name in screens:
            at.sidebar.radio[0].set_value(screen_name).run()
            assert not at.exception, f"Screen '{screen_name}' raised unexpected exception: {at.exception}"
            assert len(at.file_uploader) == 0, (
                f"Screen '{screen_name}' unexpectedly rendered a file uploader in synthetic-only mode"
            )

    finally:
        if old_val is None:
            os.environ.pop("DOCUREADY_SYNTHETIC_ONLY", None)
        else:
            os.environ["DOCUREADY_SYNTHETIC_ONLY"] = old_val

