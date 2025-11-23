# src/ssg_hs_forensics_app/core/model_sam1.py

"""
SAM1 Loader (ViT-B / ViT-L / ViT-H) + Preset-aware Mask Generator
"""

from __future__ import annotations
from typing import Dict, List
from pathlib import Path
import numpy as np
from loguru import logger

from ssg_hs_forensics_app.vendor.sam1.segment_anything.build_sam import (
    build_sam_vit_b,
    build_sam_vit_l,
    build_sam_vit_h,
)
from ssg_hs_forensics_app.vendor.sam1.segment_anything.automatic_mask_generator import (
    SamAutomaticMaskGenerator,
)
from ssg_hs_forensics_app.core.mask_schema import make_mask_record
from ssg_hs_forensics_app.core.preset_loader import load_preset_params


# ------------------------------------------------------------
# SAM1 Model Loader
# ------------------------------------------------------------
def load_sam1(checkpoint: str, *, model_type: str):
    """
    Load SAM1 with the correct architecture.
    model_type ∈ {"vit_b", "vit_l", "vit_h"}
    """

    name = model_type.lower().strip()

    checkpoint = Path(checkpoint).expanduser().as_posix()
    logger.debug(f"Loading SAM1 ({name}) checkpoint: {checkpoint}")

    if name == "vit_b":
        model = build_sam_vit_b(checkpoint)

    elif name == "vit_l":
        model = build_sam_vit_l(checkpoint)

    elif name == "vit_h":
        model = build_sam_vit_h(checkpoint)

    else:
        raise ValueError(
            f"Unknown SAM1 model type '{model_type}'. "
            f"Allowed types: vit_b, vit_l, vit_h"
        )

    # Mark this model's key so preset loader knows which preset block to use
    model.model_key = f"sam1_{name}"

    model.eval()
    return model


# ------------------------------------------------------------
# SAM1 Mask Generation (Preset-aware)
# ------------------------------------------------------------
def sam1_generate_masks(
    model,
    np_image: np.ndarray,
    preset_name: str,
) -> List[Dict]:
    """
    Generate segmentation masks for SAM1 using the preset specified by:
        [presets.sam1_<type>.<preset_name>]

    Example:
        presets.sam1_vit_b.default
        presets.sam1_vit_b.fast
    """

    model_key = getattr(model, "model_key", None)
    if model_key is None:
        raise RuntimeError(
            "SAM1 model is missing model_key. "
            "Did load_sam1() assign model.model_key?"
        )

    # Load preset parameters from config
    params = load_preset_params(model_key, preset_name)

    logger.debug(
        f"[SAM1] Using preset '{preset_name}' "
        f"for model '{model_key}': {params}"
    )

    # Build mask generator *with preset parameters*
    generator = SamAutomaticMaskGenerator(
        model,
        points_per_side=params["points_per_side"],
        pred_iou_thresh=params["pred_iou_thresh"],
        stability_score_thresh=params["stability_score_thresh"],
        crop_n_layers=params["crop_n_layers"],
        crop_n_points_downscale_factor=params["crop_n_points_downscale_factor"],
        min_mask_region_area=params["min_mask_region_area"],
        output_mode=params["output_mode"],
    )

    logger.debug("[SAM1] Running generator.generate()")
    raw_masks = generator.generate(np_image)

    masks = [
        make_mask_record(
            mask=m["segmentation"],
            confidence=m.get("predicted_iou", 0.0),
            bbox=m.get("bbox"),
            area=m.get("area"),
            track_id=None,
            metadata={},
        )
        for m in raw_masks
    ]

    logger.debug(f"[SAM1] Completed mask generation → {len(masks)} masks")
    return masks
