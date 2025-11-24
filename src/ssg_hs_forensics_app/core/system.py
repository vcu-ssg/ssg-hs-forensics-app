# src/ssg_hs_forensics_app/core/system.py

from __future__ import annotations
import subprocess
from typing import Tuple
import platform


# ------------------------------------------------------------
# Detect CUDA hardware (torch-independent)
# ------------------------------------------------------------

def detect_cuda_hardware() -> Tuple[bool, str]:
    """
    Returns (available, detail)

    Checks:
      1. nvidia-smi (GPU present + NVIDIA driver installed)
      2. nvcc --version (CUDA toolkit installed)

    Fully independent of torch.
    """

    # nvidia-smi check (most reliable)
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, check=True
        )
        gpu_name = result.stdout.strip()
        if gpu_name:
            return True, gpu_name
        return False, "nvidia-smi found but no GPU name detected"
    except Exception:
        pass

    # CUDA toolkit check
    try:
        result = subprocess.run(
            ["nvcc", "--version"],
            capture_output=True, text=True, check=True
        )
        if "Cuda compilation tools" in result.stdout:
            return True, "CUDA toolkit installed (device unknown)"
    except Exception:
        pass

    return False, "No NVIDIA driver or CUDA toolkit detected"


# ------------------------------------------------------------
# Torch status
# ------------------------------------------------------------

def detect_torch() -> Tuple[bool, bool, str]:
    """
    Returns (torch_installed, torch_cuda_available, detail)
    """
    try:
        import torch
    except Exception:
        return False, False, "torch not installed"

    try:
        cuda = torch.cuda.is_available()
        detail = torch.cuda.get_device_name(0) if cuda else "CPU only"
        return True, cuda, detail
    except Exception as e:
        return True, False, f"torch error: {e}"


# ------------------------------------------------------------
# System summary
# ------------------------------------------------------------

def detect_os_version():
    system = platform.system()

    if system != "Windows":
        # macOS or Linux is reported correctly
        return {
            "os_name": system,
            "os_release": platform.release(),
            "os_version": platform.version(),
        }

    # --- Windows special case ---
    raw_version = platform.version()       # "10.0.22631"
    parts = raw_version.split(".")
    build = int(parts[-1]) if parts[-1].isdigit() else 0

    if build >= 22000:
        pretty = "Windows 11"
    else:
        pretty = "Windows 10"   # Windows 11 that reports as 10 will be corrected

    return {
        "os_name": pretty,
        "os_release": platform.release(),  # still "10"
        "os_version": raw_version,
    }

def get_system_summary() -> dict:
    os_info = detect_os_version()
    has_cuda_hw, hw_detail = detect_cuda_hardware()
    has_torch, torch_cuda, torch_detail = detect_torch()

    return {
        "os_name": os_info["os_name"],
        "os_release": os_info["os_release"],
        "os_version": os_info["os_version"],
        "cuda_hardware": has_cuda_hw,
        "cuda_hardware_detail": hw_detail,
        "torch_installed": has_torch,
        "torch_cuda": torch_cuda,
        "torch_detail": torch_detail,
    }
