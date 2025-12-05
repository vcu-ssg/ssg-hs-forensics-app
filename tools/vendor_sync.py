#!/usr/bin/env python3
"""
Vendor Sync Script

Installs vendored copies of:

    SAM1 → vendor/sam1/segment_anything/...
    SAM2 → vendor/sam2/sam2/...

This ensures that imports work:

    from ssg_hs_forensics_app.vendor.sam1.segment_anything import ...
    from ssg_hs_forensics_app.vendor.sam2.sam2.build_sam2 import build_sam2

Run:

    poetry run python tools/vendor_sync.py
"""

import shutil
import subprocess
from pathlib import Path
import sys
import os

ROOT = Path(__file__).resolve().parent.parent
TEMP_DIR = ROOT / ".vendor_tmp"
VENDOR_DIR = ROOT / "src" / "ssg_hs_forensics_app" / "vendor"

SAM1_REPO = "https://github.com/facebookresearch/segment-anything.git"
SAM2_REPO = "https://github.com/facebookresearch/segment-anything-2.git"

SAM1_DST = VENDOR_DIR / "sam1"
SAM2_DST = VENDOR_DIR / "sam2"

SAM1_SOURCE_SUBDIR = "segment_anything"


# -------------------------------------------------------------------
# Utility helpers
# -------------------------------------------------------------------

def run(cmd: list):
    print(f">>> {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def safe_rmtree(path: Path):
    if not path.exists():
        return

    def onerror(func, p, exc_info):
        try:
            os.chmod(p, 0o700)
        except Exception:
            pass
        func(p)

    print(f"Removing {path}")
    shutil.rmtree(path, onerror=onerror)


def ensure_git():
    try:
        subprocess.run(["git", "--version"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print("ERROR: Git is not installed or not on PATH.")
        sys.exit(1)


# -------------------------------------------------------------------
# Clone repos
# -------------------------------------------------------------------

def clone_repos():
    safe_rmtree(TEMP_DIR)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print("\n=== Cloning SAM1 ===")
    sam1_tmp = TEMP_DIR / "sam1"
    run(["git", "clone", "--depth=1", SAM1_REPO, str(sam1_tmp)])

    print("\n=== Cloning SAM2 ===")
    sam2_tmp = TEMP_DIR / "sam2"
    run(["git", "clone", "--depth=1", SAM2_REPO, str(sam2_tmp)])

    return sam1_tmp, sam2_tmp


# -------------------------------------------------------------------
# Install SAM1
# -------------------------------------------------------------------

def install_sam1(repo_root: Path):
    print("\n=== Installing SAM1 into vendor/sam1 ===")

    safe_rmtree(SAM1_DST)
    SAM1_DST.mkdir(parents=True, exist_ok=True)

    src = repo_root / SAM1_SOURCE_SUBDIR
    if not src.exists():
        print("ERROR: SAM1 expected folder not found:", src)
        sys.exit(1)

    shutil.copytree(src, SAM1_DST / SAM1_SOURCE_SUBDIR)

    print("SAM1 vendored OK.")


# -------------------------------------------------------------------
# Install SAM2 (Full package)
# -------------------------------------------------------------------

def install_sam2(repo_root: Path):
    print("\n=== Installing SAM2 into vendor/sam2 ===")

    safe_rmtree(SAM2_DST)
    SAM2_DST.mkdir(parents=True, exist_ok=True)

    src_pkg = repo_root / "sam2"
    if not src_pkg.exists():
        print("ERROR: SAM2 expected python package not found:", src_pkg)
        sys.exit(1)

    dst_pkg = SAM2_DST / "sam2"

    print("Copying SAM2 package:", src_pkg)
    shutil.copytree(
        src_pkg,
        dst_pkg,
        ignore=shutil.ignore_patterns(
            ".git", "__pycache__", "*.md", "demo", "notebooks", "training", "tools"
        )
    )

    # Ensure __init__.py exists
    init_py = dst_pkg / "__init__.py"
    if not init_py.exists():
        init_py.write_text(
            "# Auto-generated vendor package marker\n"
            "from .build_sam import *\n"
        )

    print("SAM2 vendored OK.")


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():
    print("\n=== Vendor Sync ===")

    ensure_git()
    sam1_tmp, sam2_tmp = clone_repos()

    install_sam1(sam1_tmp)
    install_sam2(sam2_tmp)

    print("\nCleaning temporary folder...")
    safe_rmtree(TEMP_DIR)

    print("\nVendor sync complete ✓")


if __name__ == "__main__":
    main()
