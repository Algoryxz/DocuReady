# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for DocuReady standalone desktop sidecar."""
import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
repo_root = Path(SPECPATH).resolve().parent
src_dir = str(repo_root / "src")

# Ensure src is on sys.path during analysis
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

hidden_imports = [
    "docuready",
    "docuready.domain.models",
    "docuready.domain.enums",
    "docuready.pipeline",
    "docuready.report.redact",
    "docuready.report.exporter",
    "docuready.ingest.extractor",
    "docuready.ingest.slot_classifier",
    "docuready.ingest.pdf_backend",
    "docuready.ingest.pdf_backend.base",
    "docuready.ingest.pdf_backend.pymupdf_backend",
    "docuready.normalize.normalizer",
    "docuready.evidence.calibrator",
    "docuready.rules.engine",
    "docuready.rules.matrix",
    "pymupdf",
    "fitz",
    "PIL",
    "PIL.Image",
    "numpy",
    "pydantic",
    "pytesseract",
] + collect_submodules("docuready")

datas = collect_data_files("pymupdf")

a = Analysis(
    [os.path.join(SPECPATH, "docuready_sidecar.py")],
    pathex=[src_dir, SPECPATH],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "streamlit", "reportlab"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="docuready_sidecar",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="docuready_sidecar",
)
