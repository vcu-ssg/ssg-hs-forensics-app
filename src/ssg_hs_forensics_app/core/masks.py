# src/ssg_hs_forensics_app/core/masks.py

"""
Core utilities for discovering and loading HDF5 mask files.

This module is shared by:
- CLI (`sammy masks`)
- FastAPI endpoints
- Any system component needing mask discovery or metadata.

Functions provided:
    list_mask_records(...) → returns sorted list of mask records w/ index numbers
    get_mask_by_index(...)
    get_mask_by_name(...)
    load_mask_file(...) → full load via core.mask_writer
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

from ssg_hs_forensics_app.core.mask_writer import load_masks_h5, list_mask_files


# ------------------------------------------------------------
# Metadata extraction (lightweight)
# ------------------------------------------------------------

def extract_mask_metadata(path: Path) -> Dict:
    """
    Extract summary metadata from an HDF5 mask file.
    Fast, since it only reads what load_masks_h5() normally gives.
    """
    meta = {}
    meta["path"] = str(path)
    meta["name"] = path.name

    try:
        data = load_masks_h5(path)
        meta["num_masks"] = len(data.get("masks", []))

        runinfo = data.get("runinfo", {})
        meta["start_time"] = runinfo.get("start_time")
        meta["end_time"] = runinfo.get("end_time")

        input_info = data.get("input_info", {})
        logger.trace( f"{input_info}" )

        meta["image_path"] = input_info.get("image_path", "unknown")
        meta["image_name"] = Path(meta["image_path"]).name

    except Exception as e:
        meta["error"] = str(e)

    return meta


# ------------------------------------------------------------
# Public API: list + lookup
# ------------------------------------------------------------

def list_mask_records(folder: Path) -> List[Dict]:
    """
    Returns list of metadata dicts for *.h5 mask files.
    Each record has:
        - index
        - name
        - path
        - num_masks
        - start_time
        - image_path
        - (optional) error
    """
    masks = [
        p for p in list_mask_files(folder)
        if p.suffix.lower() == ".h5"
    ]

    masks = sorted(masks, key=lambda p: str(p).lower())

    records = []
    for i, p in enumerate(masks, start=1):
        info = extract_mask_metadata(p)
        info["index"] = i
        records.append(info)

    return records


def get_mask_by_index(records: List[Dict], index: int) -> Optional[Dict]:
    """Lookup by sequence number."""
    for rec in records:
        if rec["index"] == index:
            return rec
    return None


def get_mask_by_name(records: List[Dict], name: str) -> Optional[Dict]:
    """Lookup by filename (case-insensitive)."""
    target = name.lower()
    for rec in records:
        if rec["name"].lower() == target:
            return rec
    return None


# ------------------------------------------------------------
# Full load for visualization or deeper analysis
# ------------------------------------------------------------

def load_mask_file(path: Path):
    """Full H5 load. Pure wrapper for mask_writer.load_masks_h5."""
    return load_masks_h5(Path(path))
