"""
Permanent mask-storage utilities.

Provides:
    write_masks_json(image_path, masks, output_folder)
    load_masks_json(path)
    list_mask_files(mask_folder)
    validate_mask_json(path)
    mask_name_for_image(image_path)

Mask files are stored under the folder defined in:
    [application].mask_folder
"""

from __future__ import annotations

import json
from pathlib import Path
from loguru import logger


# =====================================================================
# Filenames
# =====================================================================

def mask_name_for_image(image_path: str | Path) -> str:
    """
    Given an image file, return the standard mask filename:
        foo.jpg → foo_masks.json
    """
    stem = Path(image_path).stem
    return f"{stem}_masks.json"


# =====================================================================
# Write Masks JSON
# =====================================================================

def write_masks_json(
    image_path: str | Path,
    masks: list,
    output_folder: str | Path
) -> Path:
    """
    Writes mask output to the permanent mask storage folder.

    Parameters:
        image_path: path to original image
        masks: list of mask dicts from SAM
        output_folder: resolved mask output folder

    Returns:
        Path to written JSON file
    """
    output_folder = Path(output_folder).expanduser().resolve()
    output_folder.mkdir(parents=True, exist_ok=True)

    filename = mask_name_for_image(image_path)
    out_path = output_folder / filename

    logger.debug(f"Writing mask JSON: {out_path}")

    # Convert non-JSON objects (numpy arrays, tensors)
    def convert(obj):
        try:
            import numpy as np
            if isinstance(obj, np.ndarray):
                return obj.tolist()
        except Exception:
            pass
        return obj

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(masks, f, indent=2, default=convert)
    except Exception as e:
        logger.error(f"Failed writing mask file {out_path}: {e}")
        raise

    return out_path


# =====================================================================
# Load Masks JSON
# =====================================================================

def load_masks_json(path: str | Path) -> list:
    """
    Loads a mask JSON file from disk.

    Parameters:
        path: Full path to a mask JSON file or relative to CWD.

    Returns:
        List of mask dicts

    Raises:
        FileNotFoundError
        json.JSONDecodeError
    """
    path = Path(path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"Mask file does not exist: {path}")

    logger.debug(f"Loading mask JSON file: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =====================================================================
# Simple Structural Validation
# =====================================================================

def validate_mask_json(path: str | Path) -> bool:
    """
    Performs lightweight validation on a mask JSON file:
        - JSON parses
        - Top-level is a list
        - Each item is a dict (SAM mask format)

    Returns:
        True if valid, False otherwise.
    """
    try:
        data = load_masks_json(path)
    except Exception as e:
        logger.error(f"Invalid JSON file {path}: {e}")
        return False

    if not isinstance(data, list):
        logger.error(f"Mask file {path} must be a JSON list, found {type(data)}")
        return False

    for i, m in enumerate(data):
        if not isinstance(m, dict):
            logger.error(f"Mask entry #{i} is not a dict: {type(m)}")
            return False

    return True


# =====================================================================
# List Mask Files
# =====================================================================

def list_mask_files(mask_folder: str | Path):
    """
    Recursively lists all *.json mask files in mask_folder.

    Returns:
        List[Path]
    """
    folder = Path(mask_folder).expanduser().resolve()
    if not folder.exists():
        return []

    return sorted(folder.rglob("*_masks.json"))


def make_output_json_path(image_path: str | Path, output_folder: str | Path) -> Path:
    """
    Compute the mask JSON output path without writing anything.
    Mirrors write_masks_json() filename rules.

    Example:
        image:  /images/foo.jpg
        output: <mask_folder>/foo_masks.json
    """
    output_folder = Path(output_folder).expanduser().resolve()
    filename = mask_name_for_image(image_path)
    return output_folder / filename
