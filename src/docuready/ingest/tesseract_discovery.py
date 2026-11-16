"""Discovery, validation, and configuration for local Tesseract OCR runtime.

Resolves Tesseract binary and trained-data relative to packaged application
resources, explicit environment overrides, or platform installation paths.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_KNOWN_TESSERACT_WINDOWS_PATHS = [
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
]

_KNOWN_TESSERACT_UNIX_PATHS = [
    Path("/usr/bin/tesseract"),
    Path("/usr/local/bin/tesseract"),
    Path("/opt/homebrew/bin/tesseract"),
]


def find_tesseract_binary() -> Optional[Path]:
    """Finds the Tesseract executable without assuming it is on PATH."""
    # 1. Explicit environment variable override
    env_override = os.environ.get("DOCUREADY_TESSERACT_PATH")
    if env_override:
        p = Path(env_override)
        if p.is_file():
            return p

    # 2. PyInstaller bundled resources (sys._MEIPASS / tesseract)
    if hasattr(sys, "_MEIPASS"):
        meipass_p = (
            Path(sys._MEIPASS)
            / "tesseract"
            / ("tesseract.exe" if sys.platform == "win32" else "tesseract")
        )
        if meipass_p.is_file():
            return meipass_p

    # 3. Executable directory relative (for onedir PyInstaller or Electron resources)
    exe_dir = (
        Path(sys.executable).parent
        / "tesseract"
        / ("tesseract.exe" if sys.platform == "win32" else "tesseract")
    )
    if exe_dir.is_file():
        return exe_dir

    # 4. Resources dir from environment
    res_dir = os.environ.get("DOCUREADY_RESOURCES_DIR")
    if res_dir:
        res_p = (
            Path(res_dir)
            / "tesseract"
            / ("tesseract.exe" if sys.platform == "win32" else "tesseract")
        )
        if res_p.is_file():
            return res_p

    # 5. System PATH lookup
    path_bin = shutil.which("tesseract")
    if path_bin:
        return Path(path_bin)

    # 6. Standard platform paths
    candidate_paths = (
        _KNOWN_TESSERACT_WINDOWS_PATHS
        if sys.platform == "win32"
        else _KNOWN_TESSERACT_UNIX_PATHS
    )
    for cp in candidate_paths:
        try:
            if cp.is_file():
                return cp
        except (PermissionError, OSError):
            continue

    return None


def configure_pytesseract() -> Optional[Path]:
    """Finds Tesseract and configures pytesseract.pytesseract.tesseract_cmd.

    Returns the resolved binary Path if found, otherwise None.
    """
    bin_path = find_tesseract_binary()
    if bin_path:
        try:
            import pytesseract

            pytesseract.pytesseract.tesseract_cmd = str(bin_path)

            # Auto-configure TESSDATA_PREFIX if tessdata exists next to binary
            tessdata_candidate = bin_path.parent / "tessdata"
            if tessdata_candidate.is_dir() and "TESSDATA_PREFIX" not in os.environ:
                os.environ["TESSDATA_PREFIX"] = str(tessdata_candidate)
        except Exception:
            pass
    return bin_path


def get_ocr_runtime_info() -> Dict[str, Any]:
    """Returns structured runtime metadata regarding local OCR availability."""
    bin_path = configure_pytesseract()
    if not bin_path:
        return {
            "available": False,
            "version": None,
            "binary_path": None,
            "languages": [],
            "error": "Tesseract OCR binary not found in standard paths or bundle.",
        }

    version_str: Optional[str] = None
    languages: List[str] = []

    try:
        import pytesseract

        version_str = str(pytesseract.get_tesseract_version())
    except Exception as err:
        return {
            "available": False,
            "version": None,
            "binary_path": str(bin_path),
            "languages": [],
            "error": f"Tesseract execution failed: {err}",
        }

    # Discover traineddata languages
    tessdata_dir: Optional[Path] = None
    if "TESSDATA_PREFIX" in os.environ:
        tessdata_dir = Path(os.environ["TESSDATA_PREFIX"])
    elif (bin_path.parent / "tessdata").is_dir():
        tessdata_dir = bin_path.parent / "tessdata"

    if tessdata_dir and tessdata_dir.is_dir():
        try:
            for file in tessdata_dir.glob("*.traineddata"):
                lang = file.stem
                if lang not in ("osd", "pdf", "snum"):
                    languages.append(lang)
        except Exception:
            pass

    if not languages:
        languages = ["eng"]

    return {
        "available": True,
        "version": version_str,
        "binary_path": bin_path.name,  # Sanitize to filename only (no raw host paths)
        "languages": sorted(languages),
        "error": None,
    }
