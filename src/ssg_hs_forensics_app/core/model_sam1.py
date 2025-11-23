# src/ssg_hs_forensics_app/core/model_sam1.py

"""
SAM1 Loader (ViT-B / ViT-L / ViT-H) + unified mask generator

Now supports device selection (cpu, cuda, mps).
Matches the unified run_model_generate_masks API.
"""

from __future__ import annotations
from typing import Dict, List
from pathlib import Path
import numpy as np
import torch
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


# ------------------------------------------------------------
# SAM1 Model Loader (now with device support)
# ------------------------------------------------------------
def load_sam1(*, checkpoint: str, model_type: str, device: str = "cpu"):
    """
    Load SAM1 with the correct architecture and move it to 'device'.

    model_type ∈ {"vit_b", "vit_l", "vit_h"}
    device ∈ {"cpu", "cuda", "mps"}  (resolved upstream in model_loader)
    """

    name = model_type.lower().strip()
    checkpoint = Path(checkpoint).expanduser().as_posix()

    logger.debug(f"[SAM1] Loading model={name}, checkpoint={checkpoint}")
    logger.debug(f"[SAM1] Requested device: {device}")

    # --------------------------
    # Select SAM1 architecture
    # --------------------------
    if name == "vit_b":
        model = build_sam_vit_b(checkpoint)
    elif name == "vit_l":
        model = build_sam_vit_l(checkpoint)
    elif name == "vit_h":
        model = build_sam_vit_h(checkpoint)
    else:
        raise ValueError(f"Unknown SAM1 model type '{model_type}'")

    model.eval()

    # --------------------------
    # Move to device
    # --------------------------
    try:
        model.to(device)
        logger.debug(f"[SAM1] Model moved to device: {device}")
    except Exception as e:
        logger.error(f"[SAM1] Failed to move model to '{device}': {e}")
        raise

    # Helpful metadata
    model.model_key = f"sam1_{name}"

    return model


# ------------------------------------------------------------
# Unified SAM1 Mask Generation
# ------------------------------------------------------------
def sam1_generate_masks(
    model,
    np_image: np.ndarray,
    mg_config: Dict[str, any],
) -> List[Dict]:
    """
    Mask generation for SAM1 using your unified mg_config and schema.
    """

    if not isinstance(mg_config, dict):
        raise TypeError(
            f"sam1_generate_masks expected mg_config to be dict, "
            f"got {type(mg_config)}"
        )

    logger.debug(f"[SAM1] Using mask parameters: {mg_config}")

    generator = SamAutomaticMaskGenerator(
        model=model,
        **mg_config
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
