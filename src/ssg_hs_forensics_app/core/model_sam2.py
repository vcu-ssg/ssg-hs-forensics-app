# src/ssg_hs_forensics_app/core/model_sam2.py

"""
SAM2 Loader + Preset-aware Mask Generator
Unified, device-aware version.
"""

from __future__ import annotations
import numpy as np
from typing import List, Dict
from loguru import logger
import torch

from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

# Robust detection of mask generator class
try:
    from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator as _MaskGen
except ImportError:
    try:
        from sam2.automatic_mask_generator import AutomaticMaskGenerator as _MaskGen
    except ImportError:
        import sam2.automatic_mask_generator as _mod
        for _name in dir(_mod):
            if _name.lower().endswith("maskgenerator"):
                _MaskGen = getattr(_mod, _name)
                break
        else:
            raise ImportError(
                "SAM2: No usable mask-generator class found in sam2.automatic_mask_generator."
            )

from ssg_hs_forensics_app.core.mask_schema import make_mask_record
from ssg_hs_forensics_app.core.preset_loader import load_preset_params


# =====================================================================
# Device Resolver
# =====================================================================

def _resolve_device(requested: str) -> str:
    """
    Resolve device specification:

        cpu     → CPU always
        cuda    → CUDA required; error if unavailable
        auto    → CUDA if available, else CPU
    """
    requested = (requested or "auto").lower()

    if requested == "cpu":
        return "cpu"

    if requested == "cuda":
        if torch.cuda.is_available():
            return "cuda"
        raise RuntimeError("Config requested device='cuda' but CUDA is unavailable.")

    # auto
    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"

    logger.warning(f"Unknown device '{requested}', falling back to CPU.")
    return "cpu"


# =====================================================================
# Loader
# =====================================================================

def load_sam2(
    checkpoint: str,
    config: str,
    device: str = "auto",
):
    """
    Load a SAM2 model + predictor.

    Args:
        checkpoint: path to .pt file
        config:     path to .yaml file
        device:     "cpu", "cuda", or "auto" (default)

    Returns:
        (model, predictor)
    """

    resolved_device = _resolve_device(device)

    logger.debug(
        f"[SAM2] Loading model:\n"
        f"        checkpoint = {checkpoint}\n"
        f"        config     = {config}\n"
        f"        device     = {resolved_device}"
    )

    # Hydra requires config_file STRING (filename-like), not Path object
    model = build_sam2(
        config_file=str(config),
        ckpt_path=str(checkpoint),
        device=resolved_device,
    )

    predictor = SAM2ImagePredictor(model)
    predictor.model_key = "sam2"

    return model, predictor


# =====================================================================
# Mask Generation
# =====================================================================

def sam2_generate_masks(
    predictor,
    np_image: np.ndarray,
    mg_config: Dict[str, any],
):
    """
    Generate SAM2 masks.

    mg_config is already a fully-expanded parameter dict such as:
        {
            "points_per_side": 24,
            "pred_iou_thresh": 0.90,
            "stability_score_thresh": 0.96,
            "crop_n_layers": 1,
            "min_mask_region_area": 100,
        }

    This matches how model_loader passes preset parameters.
    """

    model_key = getattr(predictor, "model_key", None)
    if model_key is None:
        raise RuntimeError("SAM2 predictor missing model_key (should be 'sam2').")

    logger.debug(f"[SAM2] Using mask parameters for '{model_key}': {mg_config}")

    # Instantiate the SAM2 mask generator using mg_config
    generator = _MaskGen(
        predictor.model,
        points_per_side=mg_config["points_per_side"],
        pred_iou_thresh=mg_config["pred_iou_thresh"],
        stability_score_thresh=mg_config["stability_score_thresh"],
        crop_n_layers=mg_config["crop_n_layers"],
        min_mask_region_area=mg_config["min_mask_region_area"],
    )

    logger.debug("[SAM2] Running mask generator...")
    raw = generator.generate(np_image)

    masks = [
        make_mask_record(
            mask=m["segmentation"],
            confidence=float(m.get("score", 0.0)),
            bbox=m.get("bbox"),
            area=m.get("area"),
            track_id=m.get("track_id"),
            metadata={},
        )
        for m in raw
    ]

    logger.debug(f"[SAM2] Generated {len(masks)} masks")
    return masks