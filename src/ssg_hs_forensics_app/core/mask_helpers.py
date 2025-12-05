# src/ssg_hs_forensics_app/core/mask_helpers.py

"""
Mask Helpers
------------

Tiny functional utilities used by the CLI and workflow:

    • filter_by_area(masks, min_area)
    • remove_background_masks(masks, image_area, threshold)
    • sort_by_confidence(masks)

All masks are simple dicts created via make_mask_record().
"""

from __future__ import annotations
from typing import List, Dict


def filter_by_area(masks: List[Dict], min_area: int) -> List[Dict]:
    """
    Filter out masks with area < min_area.
    """
    return [
        m for m in masks
        if (m.get("area") or 0) >= min_area
    ]


def remove_background_masks(
    masks: List[Dict],
    image_area: int,
    threshold: float,
) -> List[Dict]:
    """
    Remove masks whose area / image_area >= threshold.
    """
    return [
        m for m in masks
        if ((m.get("area") or 0) / image_area) <= threshold
    ]


def sort_by_confidence(
    masks: List[Dict],
    descending: bool = True
) -> List[Dict]:
    """
    Sort masks by confidence score (float).
    """
    return sorted(
        masks,
        key=lambda m: m.get("confidence", 0.0),
        reverse=descending,
    )
