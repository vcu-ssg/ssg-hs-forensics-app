# src/ssg_hs_forensics_app/core/model_sam21.py

"""
SAM2.1 Loader + Preset-aware Mask Generator
Device-aware, Hydra-safe implementation.
"""

from __future__ import annotations
import numpy as np
from typing import List, Dict
from loguru import logger
import torch

from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

# Robust import of the SAM2 mask generator class
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
                "SAM2.1: No mask generator class found in sam2.automatic_mask_generator."
            )

from ssg_hs_forensics_app.core.mask_schema import make_mask_record
from ssg_hs_forensics_app.core.preset_loader import load_preset_params


# =====================================================================
# Device Resolver (same as SAM2)
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

    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"

    logger.warning(f"Unknown device '{requested}', using CPU fallback.")
    return "cpu"


# =====================================================================
# Loader
# =====================================================================

def load_sam21(
    checkpoint: str,
    config: str,
    device: str = "auto",
):
    """
    Load a SAM2.1 model + predictor.

    Args:
        checkpoint: path to model weights
        config:     path to .yaml config file
        device:     "cpu", "cuda", or "auto"

    Returns:
        (model, predictor)
    """

    resolved_device = _resolve_device(device)

    logger.debug(
        f"[SAM2.1] Loading model:\n"
        f"          checkpoint = {checkpoint}\n"
        f"          config     = {config}\n"
        f"          device     = {resolved_device}"
    )

    # MUST pass strings to Hydra's build_sam2
    model = build_sam2(
        config_file=str(config),
        ckpt_path=str(checkpoint),
        device=resolved_device,
    )

    predictor = SAM2ImagePredictor(model)
    predictor.model_key = "sam21"

    return model, predictor


# =====================================================================
# Mask Generation
# =====================================================================

def sam21_generate_masks(
    predictor,
    np_image: np.ndarray,
    mg_config: Dict[str, any],
) -> List[Dict]:
    """
    Generate SAM2.1 masks.

    mg_config is already a fully expanded parameter dict, such as:

        {
            "points_per_side": 24,
            "pred_iou_thresh": 0.90,
            "stability_score_thresh": 0.96,
            "crop_n_layers": 1,
            "min_mask_region_area": 100,
        }

    This matches model_loader's behavior: it resolves presets *before*
    calling this function.
    """

    model_key = getattr(predictor, "model_key", None)
    if model_key is None:
        raise RuntimeError("SAM2.1 predictor is missing model_key ('sam21').")

    logger.debug(f"[SAM2.1] Using mask parameters for '{model_key}': {mg_config}")

    generator = _MaskGen(
        predictor.model,
        points_per_side=mg_config["points_per_side"],
        pred_iou_thresh=mg_config["pred_iou_thresh"],
        stability_score_thresh=mg_config["stability_score_thresh"],
        crop_n_layers=mg_config["crop_n_layers"],
        min_mask_region_area=mg_config["min_mask_region_area"],
    )

    logger.debug("[SAM2.1] Running mask generator...")
    raw = generator.generate(np_image)

    results = [
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

    logger.debug(f"[SAM2.1] Generated {len(results)} masks")
    return results