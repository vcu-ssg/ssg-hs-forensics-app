"""
Permanent mask-storage utilities.

Provides:
    write_masks_json(image_path, masks, output_folder, *, input_info=None, model_info=None, runinfo=None)
    write_masks_h5(image_path, masks, output_folder, *, input_info=None, model_info=None, runinfo=None)
    load_masks_json(path)
    load_masks_h5(path)
    list_mask_files(mask_folder)
    validate_mask_json(path)
    mask_name_for_image(image_path)

Mask files are stored under the folder defined in:
    [application].mask_folder
"""

from __future__ import annotations

import json
import h5py
import numpy as np
from pathlib import Path
from loguru import logger


# =====================================================================
# Filenames
# =====================================================================

def mask_name_for_image(image_path: str | Path, ext: str = "json") -> str:
    """
    Given an image file, return the standard mask filename:
        foo.jpg → foo_masks.json (default)
        foo.jpg → foo_masks.h5   (with ext="h5")
    """
    stem = Path(image_path).stem
    return f"{stem}_masks.{ext}"


# =====================================================================
# Write Masks JSON
# =====================================================================

def write_masks_json(
    image_path: str | Path,
    masks: list,
    output_folder: str | Path,
    *,
    input_info: dict | None = None,
    model_info: dict | None = None,
    runinfo: dict | None = None
) -> Path:
    """
    Writes enriched JSON file containing:
      "input", "model", "runinfo", "masks"
    """

    output_folder = Path(output_folder).expanduser().resolve()
    output_folder.mkdir(parents=True, exist_ok=True)

    out_path = output_folder / mask_name_for_image(image_path, ext="json")
    logger.debug(f"Writing mask JSON: {out_path}")

    def convert(obj):
        try:
            if isinstance(obj, np.ndarray):
                return obj.tolist()
        except Exception:
            pass
        return obj

    payload = {
        "input": input_info or {},
        "model": model_info or {},
        "runinfo": runinfo or {},
        "masks": masks,
    }

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=convert)
    except Exception as e:
        logger.error(f"Failed to write JSON mask file {out_path}: {e}")
        raise

    return out_path


# =====================================================================
# Load Masks JSON
# =====================================================================

def load_masks_json(path: str | Path) -> dict:
    """
    Loads an enriched mask JSON file.

    Returns the full dict with:
      { "input", "model", "runinfo", "masks" }
    """
    path = Path(path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"Mask JSON file does not exist: {path}")

    logger.debug(f"Loading mask JSON file: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =====================================================================
# Simple JSON Validation
# =====================================================================

def validate_mask_json(path: str | Path) -> bool:
    """
    Validates an enriched JSON file:
       - JSON parses
       - Top-level keys exist
       - masks is a list
    """
    try:
        data = load_masks_json(path)
    except Exception as e:
        logger.error(f"Invalid JSON file {path}: {e}")
        return False

    if not isinstance(data, dict):
        logger.error(f"Mask file {path} must be a JSON object, found: {type(data)}")
        return False

    if "masks" not in data:
        logger.error(f"Mask file {path} missing 'masks' key")
        return False

    if not isinstance(data["masks"], list):
        logger.error(f"'masks' must be a list, found: {type(data['masks'])}")
        return False

    return True


# =====================================================================
# Write Masks HDF5 (single file)
# =====================================================================

def write_masks_h5(
    image_path: str | Path,
    masks: list,
    output_folder: str | Path,
    *,
    input_info: dict | None = None,
    model_info: dict | None = None,
    runinfo: dict | None = None
) -> Path:
    """
    Writes all mask output, metadata, and input info into a single HDF5 file.

    Structure:
        /input/*
        /model/*
        /runinfo/*
        /masks/<idx>/segmentation
        /masks/<idx>/metadata/*
    """

    output_folder = Path(output_folder).expanduser().resolve()
    output_folder.mkdir(parents=True, exist_ok=True)

    out_path = output_folder / mask_name_for_image(image_path, ext="h5")
    logger.debug(f"Writing mask H5 file: {out_path}")

    try:
        with h5py.File(out_path, "w") as h5:

            # ---------------
            # Input metadata
            # ---------------
            grp_input = h5.create_group("input")
            if input_info:
                for k, v in input_info.items():
                    _write_h5_value(grp_input, k, v)

            # ---------------
            # Model metadata
            # ---------------
            grp_model = h5.create_group("model")
            if model_info:
                for k, v in model_info.items():
                    _write_h5_value(grp_model, k, v)

            # ---------------
            # Run metadata
            # ---------------
            grp_run = h5.create_group("runinfo")
            if runinfo:
                for k, v in runinfo.items():
                    _write_h5_value(grp_run, k, v)

            # ---------------
            # Masks
            # ---------------
            grp_masks = h5.create_group("masks")

            for idx, mask in enumerate(masks):
                mgrp = grp_masks.create_group(str(idx))

                # segmentation array is special → ensure ndarray
                seg = mask.get("segmentation")
                if seg is not None:
                    seg = np.asarray(seg, dtype=np.uint8)
                    mgrp.create_dataset("segmentation", data=seg, compression="gzip")

                # write remaining mask fields under metadata
                meta = mgrp.create_group("metadata")
                for k, v in mask.items():
                    if k == "segmentation":
                        continue
                    _write_h5_value(meta, k, v)

    except Exception as e:
        logger.error(f"Failed writing HDF5 mask file {out_path}: {e}")
        raise

    return out_path


# =====================================================================
# Support: write python values into HDF5 safely
# =====================================================================

def _write_h5_value(group: h5py.Group, key: str, value):
    """
    Writes Python values into an HDF5 group:
      - scalars
      - strings
      - lists
      - numpy arrays
      - dicts (creates nested groups)
    """
    if value is None:
        group.attrs[key] = "None"
        return

    # nested dict → make subgroup
    if isinstance(value, dict):
        sub = group.create_group(key)
        for k, v in value.items():
            _write_h5_value(sub, k, v)
        return

    # numpy arrays
    if isinstance(value, np.ndarray):
        group.create_dataset(key, data=value, compression="gzip")
        return

    # lists → convert to dataset
    if isinstance(value, list):
        arr = np.asarray(value)
        group.create_dataset(key, data=arr, compression="gzip")
        return

    # everything else → attribute
    try:
        group.attrs[key] = value
    except Exception:
        group.attrs[key] = str(value)


# =====================================================================
# Load H5
# =====================================================================

def load_masks_h5(path: str | Path) -> dict:
    """
    Load the full HDF5 structure into a dict matching the JSON structure:

    Returns:
      {
        "input": {...},
        "model": {...},
        "runinfo": {...},
        "masks": [
            { "segmentation": array, ... },
            ...
        ]
      }
    """
    path = Path(path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"HDF5 file does not exist: {path}")

    logger.debug(f"Loading mask H5 file: {path}")

    out = {"input": {}, "model": {}, "runinfo": {}, "masks": []}

    with h5py.File(path, "r") as h5:

        # input/model/runinfo groups
        for section in ["input", "model", "runinfo"]:
            grp = h5.get(section)
            if grp:
                out[section] = _read_h5_group(grp)

        # masks
        grp_masks = h5.get("masks")
        if grp_masks:
            for idx in sorted(grp_masks.keys(), key=lambda x: int(x)):
                mgrp = grp_masks[idx]

                mask_obj = {}
                seg = mgrp.get("segmentation")
                if seg is not None:
                    mask_obj["segmentation"] = seg[()]

                meta = mgrp.get("metadata")
                if meta is not None:
                    mask_obj.update(_read_h5_group(meta))

                out["masks"].append(mask_obj)

    return out


# =====================================================================
# Support: recursively read HDF5 group
# =====================================================================

def _read_h5_group(group: h5py.Group) -> dict:
    """
    Returns a Python dict of everything under the HDF5 group.
    """
    result = {}

    # attributes
    for k, v in group.attrs.items():
        result[k] = v

    # datasets
    for k, v in group.items():
        if isinstance(v, h5py.Dataset):
            result[k] = v[()]
        elif isinstance(v, h5py.Group):
            result[k] = _read_h5_group(v)

    return result


# =====================================================================
# List Mask Files
# =====================================================================

def list_mask_files(mask_folder: str | Path):
    """
    Recursively list *.json and *.h5 mask files.
    """
    folder = Path(mask_folder).expanduser().resolve()
    if not folder.exists():
        return []

    return sorted(list(folder.rglob("*_masks.json")) +
                  list(folder.rglob("*_masks.h5")))
