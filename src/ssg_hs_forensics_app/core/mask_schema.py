# src/ssg_hs_forensics_app/core/mask_schema.py
"""
Unified Mask Schema — Functional Version

SAM1, SAM2, and SAM2.1 masks are normalized into a stable dictionary schema.
This file intentionally avoids classes and dataclasses; it is 100% functional
for simplicity, portability, and easier debugging.

Unified mask record shape:

    {
        "mask": np.ndarray(float32, HxW),
        "confidence": float,
        "bbox": [x1, y1, x2, y2] or None,
        "area": int or None,
        "track_id": int or None,
        "metadata": dict (arbitrary key/value pairs)
    }

`serialize_mask_record()` returns only metadata suitable for HDF5 datasets.
Mask arrays are stored separately.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List
import numpy as np


# ---------------------------------------------------------------------
# Functional constructor — creates a unified mask record (dict)
# ---------------------------------------------------------------------
def make_mask_record(
    mask: np.ndarray,
    confidence: float,
    bbox: Optional[List[int]] = None,
    area: Optional[int] = None,
    track_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a unified mask record.

    Parameters:
        mask:        numpy array HxW; will be cast to float32
        confidence:  float confidence score (SAM1 IOU / SAM2 prob)
        bbox:        [x1, y1, x2, y2] or None
        area:        integer pixel area
        track_id:    SAM2 video tracking ID or None
        metadata:    freeform dictionary

    Returns:
        dict representing a unified mask record
    """
    if metadata is None:
        metadata = {}

    # Ensure float32 mask
    mask = np.asarray(mask, dtype=np.float32)

    return {
        "mask": mask,
        "confidence": float(confidence),
        "bbox": bbox,
        "area": int(area) if area is not None else None,
        "track_id": track_id,
        "metadata": metadata,
    }


# ---------------------------------------------------------------------
# Serialization for HDF5: returns metadata only
# ---------------------------------------------------------------------
def serialize_mask_record(mask_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a mask record into HDF5-storable metadata.

    Mask arrays are intentionally omitted — HDF5 stores them separately.

    Parameters:
        mask_record: dict produced by make_mask_record()

    Returns:
        dict of metadata fields only
    """
    return {
        "confidence": float(mask_record["confidence"]),
        "bbox": mask_record["bbox"],
        "area": (
            int(mask_record["area"])
            if mask_record.get("area") is not None
            else None
        ),
        "track_id": mask_record.get("track_id"),
        "metadata": mask_record.get("metadata", {}),
    }
