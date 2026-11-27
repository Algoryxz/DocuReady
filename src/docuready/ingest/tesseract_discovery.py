"""Discovery, validation, and configuration for local Tesseract OCR runtime.

Resolves Tesseract binary and trained-data relative to packaged application
resources, explicit environment overrides, or platform installation paths.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

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


def find_tesseract_binary_with_source() -> tuple[Optional[Path], str]:
    """Finds the Tesseract executable and identifies whether it is bundled or a system prerequisite."""
    # 1. Explicit environment variable override
    env_override = os.environ.get("DOCUREADY_TESSERACT_PATH")
    if env_override:
        p = Path(env_override).resolve()
        if p.is_file():
            res_dir = os.environ.get("DOCUREADY_RESOURCES_DIR")
            is_bundled = False
            try:
                if hasattr(sys, "_MEIPASS") and p.is_relative_to(Path(sys._MEIPASS).resolve()):
                    is_bundled = True
                elif p.is_relative_to(Path(sys.executable).parent.resolve()):
                    is_bundled = True
                elif res_dir and p.is_relative_to(Path(res_dir).resolve()):
                    is_bundled = True
                elif "resources" in str(p).lower() or "sidecar" in str(p).lower():
                    is_bundled = True
            except Exception:
                pass
            return p, "bundled_resource" if is_bundled else "env_override"

    # 2. PyInstaller bundled resources (sys._MEIPASS / tesseract)
    if hasattr(sys, "_MEIPASS"):
        meipass_p = (
            Path(sys._MEIPASS)
            / "tesseract"
            / ("tesseract.exe" if sys.platform == "win32" else "tesseract")
        )
        if meipass_p.is_file():
            return meipass_p, "bundled_resource"

    # 3. Executable directory relative (for onedir PyInstaller or Electron resources)
    exe_dir = (
        Path(sys.executable).parent
        / "tesseract"
        / ("tesseract.exe" if sys.platform == "win32" else "tesseract")
    )
    if exe_dir.is_file():
        return exe_dir, "bundled_resource"

    # 4. Resources dir from environment
    res_dir = os.environ.get("DOCUREADY_RESOURCES_DIR")
    if res_dir:
        res_p = (
            Path(res_dir)
            / "tesseract"
            / ("tesseract.exe" if sys.platform == "win32" else "tesseract")
        )
        if res_p.is_file():
            return res_p, "bundled_resource"
        res_sub_p = (
            Path(res_dir)
            / "docuready_sidecar"
            / "tesseract"
            / ("tesseract.exe" if sys.platform == "win32" else "tesseract")
        )
        if res_sub_p.is_file():
            return res_sub_p, "bundled_resource"

    # If bundled OCR is strictly required (e.g. packaged releases), do not fall back to system PATH
    if os.environ.get("DOCUREADY_REQUIRE_BUNDLED_OCR") in ("1", "true", "True"):
        return None, "none"

    # 5. System PATH lookup
    path_bin = shutil.which("tesseract")
    if path_bin:
        return Path(path_bin), "system_prerequisite"

    # 6. Standard platform paths
    candidate_paths = (
        _KNOWN_TESSERACT_WINDOWS_PATHS
        if sys.platform == "win32"
        else _KNOWN_TESSERACT_UNIX_PATHS
    )
    for cp in candidate_paths:
        try:
            if cp.is_file():
                return cp, "system_prerequisite"
        except (PermissionError, OSError):
            continue

    return None, "none"


def find_tesseract_binary() -> Optional[Path]:
    """Finds the Tesseract executable without assuming it is on PATH."""
    bin_path, _ = find_tesseract_binary_with_source()
    return bin_path


def get_unified_tessdata_dir(bin_path: Path) -> Optional[Path]:
    """Resolves or prepares a unified tessdata directory containing both base and extra language models."""
    import tempfile
    
    # 1. Base tessdata next to tesseract binary
    base_tessdata = bin_path.parent / "tessdata"
    
    # 2. Extra tessdata candidates in repository / sidecar / bundle
    extra_candidates = [
        Path(__file__).resolve().parents[3] / "sidecar" / "tessdata_extra",
        Path(__file__).resolve().parents[3] / "sidecar" / "tessdata",
        Path(sys.executable).parent / "tessdata",
    ]
    if hasattr(sys, "_MEIPASS"):
        extra_candidates.append(Path(sys._MEIPASS) / "tessdata")
        extra_candidates.append(Path(sys._MEIPASS) / "tessdata_extra")

    extra_tessdata = None
    for cand in extra_candidates:
        if cand.is_dir() and (cand / "hin.traineddata").exists():
            extra_tessdata = cand
            break

    if not extra_tessdata:
        return base_tessdata if base_tessdata.is_dir() else None

    # If base_tessdata already has hin.traineddata, just return it
    if base_tessdata.is_dir() and (base_tessdata / "hin.traineddata").exists():
        return base_tessdata

    # Otherwise, create/update a cached unified tessdata folder in tempdir
    unified_dir = Path(tempfile.gettempdir()) / "docuready_unified_tessdata"
    unified_dir.mkdir(parents=True, exist_ok=True)

    # Populate from base
    if base_tessdata.is_dir():
        for f in base_tessdata.glob("*.traineddata"):
            dst = unified_dir / f.name
            try:
                if not dst.exists() or dst.stat().st_size != f.stat().st_size:
                    shutil.copy2(f, dst)
            except Exception:
                pass

    # Populate from extra
    for f in extra_tessdata.glob("*.traineddata"):
        dst = unified_dir / f.name
        try:
            if not dst.exists() or dst.stat().st_size != f.stat().st_size:
                shutil.copy2(f, dst)
        except Exception:
            pass

    return unified_dir


def configure_pytesseract() -> Optional[Path]:
    """Finds Tesseract and configures pytesseract.pytesseract.tesseract_cmd.

    Returns the resolved binary Path if found, otherwise None.
    """
    bin_path, _ = find_tesseract_binary_with_source()
    if bin_path:
        try:
            import pytesseract

            pytesseract.pytesseract.tesseract_cmd = str(bin_path)

            # Auto-configure TESSDATA_PREFIX to unified tessdata directory
            tessdata_candidate = get_unified_tessdata_dir(bin_path)
            if tessdata_candidate and tessdata_candidate.is_dir():
                os.environ["TESSDATA_PREFIX"] = str(tessdata_candidate)
        except Exception:
            pass
    return bin_path


def get_ocr_runtime_info() -> Dict[str, Any]:
    """Returns structured runtime metadata regarding local OCR availability."""
    bin_path = find_tesseract_binary()
    if not bin_path:
        return {
            "available": False,
            "version": None,
            "binary_path": None,
            "languages": [],
            "source": "none",
            "is_bundled": False,
            "error": "Tesseract OCR binary not found in standard paths or bundle.",
        }

    _, source = find_tesseract_binary_with_source()

    version_str: Optional[str] = None
    languages: List[str] = []

    orig_cmd = None
    try:
        import pytesseract
        orig_cmd = getattr(pytesseract.pytesseract, "tesseract_cmd", "tesseract")
        pytesseract.pytesseract.tesseract_cmd = str(bin_path)
        version_str = str(pytesseract.get_tesseract_version())
    except Exception as err:
        try:
            import pytesseract
            if orig_cmd is not None:
                pytesseract.pytesseract.tesseract_cmd = orig_cmd
        except Exception:
            pass
        return {
            "available": False,
            "version": None,
            "binary_path": str(bin_path),
            "languages": [],
            "source": source,
            "is_bundled": (source == "bundled_resource"),
            "error": f"Tesseract execution failed: {err}",
        }

    # Discover traineddata languages directly via tesseract --list-langs (uncached)
    command_discovery_succeeded = False
    try:
        proc_env = os.environ.copy()
        tessdata_next_to_bin = bin_path.parent / "tessdata"
        if tessdata_next_to_bin.is_dir() and "TESSDATA_PREFIX" not in proc_env:
            proc_env["TESSDATA_PREFIX"] = str(tessdata_next_to_bin)
        proc = subprocess.run(
            [str(bin_path), "--list-langs"],
            capture_output=True,
            text=True,
            timeout=10,
            env=proc_env,
        )
        if proc.returncode == 0:
            command_discovery_succeeded = True
            for line in (proc.stdout or "").splitlines():
                lang = line.strip()
                if not lang or lang.lower().startswith("list of available languages"):
                    continue
                if lang not in ("osd", "pdf", "snum") and lang not in languages:
                    languages.append(lang)
    except Exception:
        pass

    # Fallback: scan tessdata directory only when command discovery failed.
    # If TESSDATA_PREFIX is explicitly set, restrict fallback strictly to that location.
    if not command_discovery_succeeded:
        if "TESSDATA_PREFIX" in os.environ:
            override = os.environ["TESSDATA_PREFIX"].strip()
            tessdata_candidates = [Path(override)] if override else []
        else:
            tessdata_candidates = [
                bin_path.parent / "tessdata",
                Path("/usr/share/tesseract-ocr/5/tessdata"),
                Path("/usr/share/tesseract-ocr/4.00/tessdata"),
                Path("/usr/share/tessdata"),
            ]
        for tessdata_dir in tessdata_candidates:
            if tessdata_dir.is_dir():
                try:
                    for file in tessdata_dir.glob("*.traineddata"):
                        lang = file.stem
                        if lang not in ("osd", "pdf", "snum") and lang not in languages:
                            languages.append(lang)
                except Exception:
                    pass
                if languages:
                    break

    return {
        "available": True,
        "version": version_str,
        "binary_path": bin_path.name,  # Sanitize to filename only (no raw host paths)
        "languages": sorted(languages),
        "source": source,
        "is_bundled": (source == "bundled_resource"),
        "error": None,
    }


def normalize_ocr_langs(
    ocr_langs: Optional[Union[str, List[str], Tuple[str, ...]]]
) -> str:
    """Normalize a language specification into a deterministic Tesseract lang string (e.g. 'eng+ori')."""
    if not ocr_langs:
        return "eng"
    if isinstance(ocr_langs, str):
        raw_parts = [p.strip() for p in ocr_langs.replace(",", "+").replace(" ", "+").split("+")]
    else:
        raw_parts = [str(p).strip() for p in ocr_langs]
    deduped: List[str] = []
    for part in raw_parts:
        if part and part not in deduped:
            deduped.append(part)
    return "+".join(deduped) if deduped else "eng"


def check_ocr_language_availability(
    requested_langs: Optional[Union[str, List[str], Tuple[str, ...]]] = None,
) -> Dict[str, Any]:
    """Verify Tesseract binary and requested traineddata language availability without silent fallback."""
    lang_str = normalize_ocr_langs(requested_langs)
    req_list = lang_str.split("+")
    info = get_ocr_runtime_info()
    if not info.get("available"):
        return {
            "available": False,
            "binary_available": False,
            "requested_lang": lang_str,
            "requested_langs": req_list,
            "installed_langs": [],
            "missing_langs": req_list,
            "error": info.get("error") or "Tesseract OCR binary not found.",
        }

    installed = set(info.get("languages") or [])
    missing = [lang for lang in req_list if lang not in installed]
    error_msg = (
        f"Missing Tesseract traineddata for requested language(s): {', '.join(missing)}"
        if missing
        else None
    )
    return {
        "available": len(missing) == 0,
        "binary_available": True,
        "requested_lang": lang_str,
        "requested_langs": req_list,
        "installed_langs": sorted(installed),
        "missing_langs": missing,
        "error": error_msg,
    }
