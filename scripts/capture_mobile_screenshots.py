"""Capture mobile and responsive viewport screenshots using headless browser."""

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "screenshots" / "mobile"
EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PORT = 8503
URL = f"http://localhost:{PORT}"

VIEWPORTS = [
    (360, 800, "small_android_360x800.png"),
    (390, 844, "standard_phone_390x844.png"),
    (430, 932, "large_phone_430x932.png"),
    (768, 1024, "tablet_768x1024.png"),
    (1440, 900, "desktop_1440x900.png"),
]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Remove stale screenshots prior to generation
    for _, _, fname in VIEWPORTS:
        (OUTPUT_DIR / fname).unlink(missing_ok=True)

    python_exe = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    if not python_exe.exists():
        python_exe = Path(sys.executable)

    env = os.environ.copy()
    env["DOCUREADY_SYNTHETIC_ONLY"] = "1"

    print(f"Starting Streamlit server on port {PORT}...")
    server = subprocess.Popen(
        [
            str(python_exe),
            "-m",
            "streamlit",
            "run",
            str(REPO_ROOT / "src" / "docuready" / "interfaces" / "ui" / "app.py"),
            f"--server.port={PORT}",
            "--server.headless=true",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait for server to be responsive
        ready = False
        for attempt in range(30):
            try:
                with urllib.request.urlopen(URL, timeout=1) as resp:
                    if resp.status == 200:
                        ready = True
                        break
            except Exception:
                time.sleep(1)

        if not ready:
            print("ERROR: Streamlit server failed to start within 30 seconds.")
            return 1

        print("Streamlit server is ready. Waiting for initial application warmup...")
        time.sleep(3)

        from PIL import Image

        for w, h, fname in VIEWPORTS:
            out_file = OUTPUT_DIR / fname
            print(f"Capturing {fname} ({w}x{h})...")
            cmd = [
                EDGE_EXE,
                "--headless=old",
                "--disable-gpu",
                "--no-sandbox",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=8000",
                f"--window-size={w},{h}",
                f"--screenshot={str(out_file)}",
                URL,
            ]
            res = subprocess.run(cmd, capture_output=True, timeout=30)
            if out_file.exists() and out_file.stat().st_size > 0:
                img = Image.open(out_file)
                unique_colors = len(set(img.get_flattened_data() if hasattr(img, "get_flattened_data") else img.getdata()))
                print(f"  -> Generated {fname}: {out_file.stat().st_size} bytes, dimensions={img.size}, unique_colors={unique_colors}")
                if unique_colors <= 1:
                    print(f"  -> WARNING: {fname} appears blank (single color detected)")
            else:
                print(f"  -> FAILED to generate {fname}: {res.stderr.decode('utf-8', errors='ignore')}")

    finally:
        print("Terminating Streamlit server...")
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()

    print("Screenshot capture routine complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
