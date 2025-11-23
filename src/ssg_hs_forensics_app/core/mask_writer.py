# src/ssg_hs_forensics_app/core/mask_writer.py

"""
Unified HDF5 Mask I/O (Writer + Reader + File Listing)

This module stores and loads:
    • Raw JPEG image bytes
    • Mask arrays
    • Metadata (input, model, preset, runtime)

HDF5 Layout:
    /image/jpeg              uint8[…]
    /masks/N/mask            uint8[H,W]
    /masks/N/confidence      float
    /masks/N/bbox            int[4]
    /masks/N/area            int
    /masks/N/track_id        int
    /masks/N/metadata        JSON text

    /metadata/input_info
    /metadata/model_info
    /metadata/preset_info
    /metadata/runinfo
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List
import numpy as np
import h5py


# ---------------------------------------------------------------------
# Canonical Output Path Builder
# ---------------------------------------------------------------------

def mask_output_path(
    image_path: Path,
    model_key: str,
    preset: str,
    mask_folder: Path,
) -> Path:
    """Build canonical output filename."""
    safe_model = model_key.lower()
    safe_preset = preset.lower()
    filename = f"{image_path.stem}.{safe_model}.{safe_preset}.h5"
    return mask_folder / filename


# ---------------------------------------------------------------------
# HDF5 Writer (JPEG bytes version)
# ---------------------------------------------------------------------

def write_masks_h5(
    out_path: Path,
    masks: List[Dict],
    jpeg_bytes: bytes,
    image_info: Dict,
    model_info: Dict,
    preset_info: Dict,
    runinfo: Dict,
) -> Path:
    """Write masks + metadata + original JPEG bytes to HDF5."""

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with h5py.File(out_path, "w") as h5:

        # Store raw JPEG bytes
        h5.create_dataset(
            "image/jpeg",
            data=np.frombuffer(jpeg_bytes, dtype=np.uint8),
            compression="gzip",
        )

        # Masks
        g_masks = h5.create_group("masks")

        for idx, m in enumerate(masks):
            mg = g_masks.create_group(str(idx))

            # float32 → uint8 mask
            mask_arr = np.asarray(m["mask"], dtype=np.float32)
            mask_uint8 = (mask_arr * 255).astype("uint8")
            mg.create_dataset("mask", data=mask_uint8, compression="gzip")

            mg.create_dataset("confidence", data=float(m.get("confidence", 0.0)))

            bbox = m.get("bbox")
            if bbox is None:
                mg.create_dataset("bbox", data=np.array([], dtype="int32"))
            else:
                mg.create_dataset("bbox", data=np.asarray(bbox, dtype="int32"))

            mg.create_dataset("area", data=int(m.get("area") or 0))

            mg.create_dataset(
                "track_id",
                data=int(m.get("track_id")) if m.get("track_id") is not None else -1,
            )

            metadata_json = json.dumps(m.get("metadata", {}), ensure_ascii=False)
            mg.create_dataset("metadata", data=metadata_json)

        # Global Metadata
        g_meta = h5.create_group("metadata")

        g_meta.create_dataset("input_info",
                              data=json.dumps(image_info, ensure_ascii=False))

        g_meta.create_dataset("model_info",
                              data=json.dumps(model_info, ensure_ascii=False))

        g_meta.create_dataset("preset_info",
                              data=json.dumps(preset_info, ensure_ascii=False))

        g_meta.create_dataset("runinfo",
                              data=json.dumps(runinfo, ensure_ascii=False))

    return out_path


# ---------------------------------------------------------------------
# HDF5 Loader (Reader)
# ---------------------------------------------------------------------

def load_masks_h5(path: Path) -> Dict:
    """
    Load a mask HDF5 file into a friendly Python dict.

    Returns dict with:
        {
            "jpeg_bytes": b"...",
            "input_info": {...},
            "model_info": {...},
            "preset_info": {...},
            "runinfo": {...},
            "masks": [ { "segmentation": bool array, ... }, ... ]
        }
    """

    out = {}
    path = Path(path)

    with h5py.File(path, "r") as h5:

        # JPEG bytes
        jpeg_dset = h5["image/jpeg"]
        out["jpeg_bytes"] = bytes(jpeg_dset[:])

        # Metadata
        meta = h5["metadata"]

        out["input_info"] = json.loads(meta["input_info"][()].decode("utf-8"))
        out["model_info"] = json.loads(meta["model_info"][()].decode("utf-8"))
        out["preset_info"] = json.loads(meta["preset_info"][()].decode("utf-8"))
        out["runinfo"] = json.loads(meta["runinfo"][()].decode("utf-8"))

        # Masks
        masks = []
        g_masks = h5["masks"]

        for idx in g_masks.keys():
            mg = g_masks[idx]

            mask_uint8 = mg["mask"][()]
            mask_bool = mask_uint8 > 127

            metadata_json = mg["metadata"][()].decode("utf-8")
            metadata = json.loads(metadata_json)

            masks.append({
                "segmentation": mask_bool,
                "confidence": float(mg["confidence"][()]),
                "bbox": mg["bbox"][()].tolist(),
                "area": int(mg["area"][()]),
                "track_id": int(mg["track_id"][()]),
                "metadata": metadata,
            })

        out["masks"] = masks

    return out


# ---------------------------------------------------------------------
# List HDF5 mask files
# ---------------------------------------------------------------------

def list_mask_files(folder: Path) -> List[Path]:
    """Return all *.h5 files inside a folder."""
    folder = Path(folder)
    if not folder.exists():
        return []
    return sorted(folder.glob("*.h5"))
