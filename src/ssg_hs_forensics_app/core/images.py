# src/ssg_hs_forensics_app/core/images.py

"""
Core utilities for discovering images and loading images as numpy arrays.

This module is shared by:
- CLI (sammy images, sammy list images, sammy generate)
- FastAPI endpoints
- Any other system components needing image discovery or loading.

Image extensions are defined in config.toml under:
    [application]
    image_extensions = ["jpg", "jpeg", "png", "bmp", "tif", "tiff"]
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List
import numpy as np
from PIL import Image
from loguru import logger

from ssg_hs_forensics_app.core.config import get_config


# ----------------------------------------------------------------------
# Extensions
# ----------------------------------------------------------------------

def get_image_exts() -> set[str]:
    """
    Returns a set of normalized file extensions from config.toml.

    Normalized form: {".jpg", ".jpeg", ".png"}
    """
    cfg = get_config()
    ext_list: Iterable[str] = cfg["application"].get(
        "image_extensions", ["jpg", "jpeg", "png"]
    )
    return {f".{ext.lower().lstrip('.')}" for ext in ext_list}


# ----------------------------------------------------------------------
# Image Discovery
# ----------------------------------------------------------------------

def _iter_images(root: Path):
    """
    Generator yielding image Paths under a folder using configured extensions.
    """
    if not root.exists():
        return

    image_exts = get_image_exts()

    for path in root.rglob("*"):
        if path.suffix.lower() in image_exts:
            yield path


def list_images(root: Path) -> List[Path]:
    """
    Return a list of images in a directory tree.
    """
    return list(_iter_images(root))


# ----------------------------------------------------------------------
# Image Loading (new)
# ----------------------------------------------------------------------

def load_image_as_numpy(path: Path) -> np.ndarray:
    """
    Load image at PATH and return a numpy array in (H, W, 3) RGB uint8.

    Ensures:
        • always RGB (alpha removed)
        • dtype uint8
        • shape (height, width, 3)
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    logger.debug(f"Loading image as numpy array: {path}")

    try:
        img = Image.open(path).convert("RGB")  # force 3-channel RGB
    except Exception as e:
        logger.error(f"Failed to open image: {e}")
        raise

    arr = np.asarray(img, dtype=np.uint8)

    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError(
            f"Invalid image shape {arr.shape}. Expected (H, W, 3) RGB array."
        )

    return arr
