"""
DocuReady Loop 32 Codebase Inventory Generator.
Collects and categorizes all modules across Python src, Electron desktop, sidecar, tests, configs, and CI.
"""

import os
import glob
import json

def inspect_file(fpath):
    size = os.path.getsize(fpath)
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    loc = len(lines)
    return {
        "path": fpath.replace("\\", "/"),
        "size_bytes": size,
        "lines_of_code": loc
    }

inventory = {}

# Python src
py_files = glob.glob("src/**/*.py", recursive=True)
inventory["python_modules"] = [inspect_file(f) for f in py_files]

# Electron desktop src
ts_files = glob.glob("apps/desktop/src/**/*", recursive=True)
inventory["desktop_modules"] = [inspect_file(f) for f in ts_files if os.path.isfile(f)]

# Sidecar
sidecar_files = glob.glob("sidecar/**/*", recursive=True)
inventory["sidecar_modules"] = [inspect_file(f) for f in sidecar_files if os.path.isfile(f) and not f.endswith(".traineddata")]

# Tests
test_files = glob.glob("tests/**/*.py", recursive=True)
inventory["python_tests"] = [inspect_file(f) for f in test_files]

# Desktop tests
desktop_test_files = glob.glob("apps/desktop/tests/**/*", recursive=True)
inventory["desktop_tests"] = [inspect_file(f) for f in desktop_test_files if os.path.isfile(f)]

# Summary stats
summary = {
    "total_python_modules": len(inventory["python_modules"]),
    "total_python_loc": sum(m["lines_of_code"] for m in inventory["python_modules"]),
    "total_desktop_modules": len(inventory["desktop_modules"]),
    "total_desktop_loc": sum(m["lines_of_code"] for m in inventory["desktop_modules"]),
    "total_sidecar_files": len(inventory["sidecar_modules"]),
    "total_python_tests": len(inventory["python_tests"]),
    "total_desktop_tests": len(inventory["desktop_tests"])
}
inventory["summary"] = summary

out_path = "research/loop32/module_inventory.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(inventory, f, indent=2)

print(f"Inventory saved to {out_path}.")
print(f"Summary: {summary}")
