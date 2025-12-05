# src/ssg_hs_forensics_app/core/images.py

"""
Core utilities for discovering images and loading metadata / arrays.

This module provides:
  • list_images(...)  → returns ordered metadata records with sequence numbers
  • get_image_by_index(...)
  • get_image_by_name(...)
  • load_image_as_numpy(...)
  • extract_image_metadata(...)
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
from PIL import Image, ExifTags
import os
from datetime import datetime

from ssg_hs_forensics_app.core.config import get_config


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def get_image_exts() -> set[str]:
    """Returns file extensions from config.toml as {".jpg", ".png"}"""
    cfg = get_config()
    ext_list = cfg["application"].get("image_extensions", ["jpg", "jpeg", "png"])
    return {f".{ext.lower().lstrip('.')}" for ext in ext_list}


def _iter_images(root: Path):
    """Yields image paths under ROOT."""
    if not root.exists():
        return

    image_exts = get_image_exts()
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in image_exts:
            yield path


# ------------------------------------------------------------
# Metadata extraction
# ------------------------------------------------------------

def extract_image_metadata(path: Path) -> Dict:
    """
    Extract metadata from an image file.
    Returns a dict compatible with CLI and FastAPI.
    """

    record = {}
    path = Path(path).resolve()

    record["path"] = str(path)
    record["name"] = path.name
    record["folder"] = str(path.parent)

    # Basic file info
    stat = path.stat()
    record["size_bytes"] = stat.st_size
    record["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
    record["created"] = datetime.fromtimestamp(stat.st_ctime).isoformat()

    # Image info
    try:
        with Image.open(path) as im:
            record["format"] = im.format
            record["mode"] = im.mode
            record["width"], record["height"] = im.size

            # EXIF
            exif_data = {}
            try:
                raw_exif = im.getexif()
                for tag_id, val in raw_exif.items():
                    tag = ExifTags.TAGS.get(tag_id, str(tag_id))
                    exif_data[tag] = val
            except Exception:
                pass

            record["exif"] = exif_data

    except Exception as e:
        record["error"] = f"Failed to read image: {e}"

    return record


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def list_images(root: Path) -> List[Dict]:
    """
    Returns a list of metadata dicts, each with a sequence number.
    Ordered alphabetically by filename.
    """

    paths = sorted(list(_iter_images(root)), key=lambda p: str(p).lower())

    records = []
    for i, p in enumerate(paths, start=1):
        meta = extract_image_metadata(p)
        meta["index"] = i  # assign sequence number
        records.append(meta)

    return records


def get_image_by_index(records: List[Dict], index: int) -> Optional[Dict]:
    """Lookup image metadata by assigned sequence number."""
    for rec in records:
        if rec.get("index") == index:
            return rec
    return None


def get_image_by_name(records: List[Dict], name: str) -> Optional[Dict]:
    """Lookup image metadata by filename (case-insensitive)."""
    name = name.lower().strip()
    for rec in records:
        if rec["name"].lower() == name:
            return rec
    return None


def load_image_as_numpy(path: Path) -> np.ndarray:
    """
    Load an image and return a numpy array (H, W, 3) RGB.
    """

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    with Image.open(path) as img:
        img = img.convert("RGB")

    arr = np.asarray(img, dtype=np.uint8)

    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError(f"Invalid image shape {arr.shape}")

    return arr
