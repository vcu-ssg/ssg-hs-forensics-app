"""
Mask generator wrappers for SAM.

Provides:
    build_mask_generator(model, mg_cfg)
    run_generator(generator, image_path)
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
from PIL import Image
from loguru import logger

from segment_anything import SamAutomaticMaskGenerator


# ---------------------------------------------------------------------
# Allowed SAM AutomaticMaskGenerator parameters
# (Your extended list – good coverage)
# ---------------------------------------------------------------------
ALLOWED_KEYS = {
    "points_per_side", "points_per_batch",
    "pred_iou_thresh", "stability_score_thresh",
    "stability_score_offset", "box_nms_thresh",
    "crop_n_layers", "crop_nms_thresh",
    "crop_overlap_ratio", "crop_n_points_downscale_factor",
    "point_grids", "min_mask_region_area",
    "output_mode",
}


# ---------------------------------------------------------------------
# Build mask generator
# ---------------------------------------------------------------------
def build_mask_generator(model, mg_cfg: dict):
    """
    Filters mg_cfg to allowed SAM keys and returns a generator instance.
    """
    filtered = {k: v for k, v in mg_cfg.items() if k in ALLOWED_KEYS}

    if filtered != mg_cfg:
        for k in mg_cfg.keys():
            if k not in ALLOWED_KEYS:
                logger.debug(f"Ignoring unknown mask-generator key: {k}")

    logger.debug(f"Final mask-generator config: {filtered}")

    return SamAutomaticMaskGenerator(model, **filtered)


# ---------------------------------------------------------------------
# Run SAM mask generator safely
# ---------------------------------------------------------------------
def run_generator(mask_generator, image_path: str | Path, mg_cfg: dict = None):
    """
    Runs the mask generator with automatic downscaling if enabled.
    """

    image_path = Path(image_path)
    logger.debug(f"Loading image with Pillow: {image_path}")

    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        raise FileNotFoundError(f"Could not open image {image_path}: {e}")

    np_image = np.array(img)

    # --------------------------------------------------------------
    # AUTO-RESIZE LOGIC (NEW + REQUIRED)
    # --------------------------------------------------------------
    if mg_cfg:
        auto_resize = mg_cfg.get("auto_resize", False)
        max_dim = int(mg_cfg.get("max_dimension", 2048))

        if auto_resize:
            h, w = np_image.shape[:2]
            longest = max(h, w)

            if longest > max_dim:
                scale = max_dim / longest
                new_w = int(w * scale)
                new_h = int(h * scale)

                logger.debug(
                    f"Auto-resizing image from {w}x{h} → {new_w}x{new_h} "
                    f"(max_dimension={max_dim})"
                )

                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                np_image = np.array(img)

    logger.debug(f"Running SAM on resized image: shape={np_image.shape}")

    try:
        masks = mask_generator.generate(np_image)
    except RuntimeError as e:
        logger.error(f"Mask generator failed: {e}")
        if "out of memory" in str(e).lower():
            logger.error("OOM detected — reduce points_per_side or enable auto_resize.")
        raise

    logger.debug(f"SAM returned {len(masks)} masks")
    return masks
