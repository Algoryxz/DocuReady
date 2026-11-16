"""
Deterministic Demonstration Reset Script
HackNation 2026 Loop 5 Engineering Directive

Completely cleans all ephemeral staging directories, terminates orphan processes,
and validates that the demonstration starts from a clean, known state.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def reset_demo_state():
    print("=== Initiating DocuReady Demo Reset Procedure ===")

    # 1. Kill any running sidecar or desktop processes
    if sys.platform == "win32":
        print("1. Terminating any lingering sidecar or desktop processes...")
        subprocess.run(
            ["powershell", "-Command", "Get-Process docuready_sidecar,DocuReady -ErrorAction SilentlyContinue | Stop-Process -Force"],
            capture_output=True,
            text=True
        )

    # 2. Clean Ephemeral Workspace Directories
    print("2. Cleaning ephemeral workspace temp directories...")
    temp_candidates = [
        Path(tempfile.gettempdir()) / "docuready-desktop",
        Path(tempfile.gettempdir()) / "clean_sidecar_validation",
    ]

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        temp_candidates.append(Path(local_app_data) / "Temp" / "docuready-desktop")

    purged_count = 0
    for cand in temp_candidates:
        if cand.exists():
            try:
                shutil.rmtree(cand)
                print(f"   Purged: {cand}")
                purged_count += 1
            except Exception as e:
                print(f"   Warning: could not delete {cand}: {e}")

    # 3. Verify Validation Corpus Integrity
    print("3. Verifying validation corpus files...")
    corpus_dir = ROOT / "tests" / "validation_corpus"
    if not corpus_dir.exists() or len(list(corpus_dir.glob("*.pdf"))) < 10:
        print("   Regenerating validation corpus...")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_validation_corpus.py")], check=True)
    else:
        print(f"   Validation corpus intact ({len(list(corpus_dir.glob('*.pdf')))} files present).")

    # 4. Verify Sidecar Binary Ready
    print("4. Verifying packaged sidecar binary...")
    sidecar_exe = ROOT / "sidecar" / "dist" / "docuready_sidecar" / "docuready_sidecar.exe"
    if not sidecar_exe.exists():
        print("   Sidecar binary missing! Rebuilding...")
        subprocess.run(["pyinstaller", "--clean", "-y", str(ROOT / "sidecar" / "docuready_sidecar.spec")], check=True)
    else:
        print(f"   Sidecar binary verified: {sidecar_exe}")

    print("=== Demo Reset Complete. Application ready for live scenario. ===")


if __name__ == "__main__":
    reset_demo_state()
