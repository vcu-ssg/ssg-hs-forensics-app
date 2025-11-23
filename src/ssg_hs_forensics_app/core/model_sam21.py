# src/ssg_hs_forensics_app/core/model_sam21.py

"""
SAM2.1 Loader + Preset-aware Mask Generator (Unified Schema)
"""

from __future__ import annotations
import numpy as np
from typing import List, Dict
from loguru import logger

# ----------------------------
# SAM2 / SAM2.1 imports
# ----------------------------

# Correct builder for SAM2 & SAM2.1
from sam2.build_sam import build_sam2

# SAM2 image predictor API (works for SAM2.1)
from sam2.sam2_image_predictor import SAM2ImagePredictor

# -----------------------------------------------------------
# Robust auto-mask-generator resolver (same logic as SAM2)
# -----------------------------------------------------------

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
                "SAM2.1: no mask generator class found in sam2.automatic_mask_generator"
            )

# Unified storage format
from ssg_hs_forensics_app.core.mask_schema import make_mask_record

# Preset loader
from ssg_hs_forensics_app.core.preset_loader import load_preset_params


# -----------------------------------------------------------
# Load SAM 2.1 Model
# -----------------------------------------------------------
def load_sam21(checkpoint: str, config: str):
    """
    Load SAM2.1 variant using same builder as SAM2, but with SAM2.1 YAML.

    Returns:
        model, predictor
    """

    logger.debug(f"[SAM2.1] Loading model: checkpoint={checkpoint}, config={config}")

    model = build_sam2(
        config_path=config,
        checkpoint_path=checkpoint,
    )

    predictor = SAM2ImagePredictor(model)

    # Assign model_key for preset lookup
    # The model_type (e.g., "hiera_small") is not passed here, so store generic key.
    predictor.model_key = "sam21"  # overridden by model_loader for specificity

    return model, predictor


# -----------------------------------------------------------
# Generate SAM2.1 Masks (Preset-aware)
# -----------------------------------------------------------
def sam21_generate_masks(
    predictor,
    np_image: np.ndarray,
    preset_name: str,
) -> List[Dict]:
    """
    Generate unified SAM2.1 masks using presets:

        [presets.sam2_1_<variant>.<preset>]

    Each preset block must contain:
        points_per_side
        pred_iou_thresh
        stability_score_thresh
        crop_n_layers
        min_mask_region_area
        output_mode ("probability")
    """

    model_key = getattr(predictor, "model_key", None)
    if model_key is None:
        raise RuntimeError(
            "SAM2.1 predictor is missing model_key. "
            "Your load_sam21() must assign predictor.model_key."
        )

    # Load preset block for SAM2.1
    params = load_preset_params(model_key, preset_name)

    logger.debug(
        f"[SAM2.1] Using preset '{preset_name}' "
        f"for model '{model_key}': {params}"
    )

    # Build mask generator with preset parameters
    generator = _MaskGen(
        predictor.model,
        points_per_side=params["points_per_side"],
        pred_iou_thresh=params["pred_iou_thresh"],
        stability_score_thresh=params["stability_score_thresh"],
        crop_n_layers=params["crop_n_layers"],
        min_mask_region_area=params["min_mask_region_area"],
        output_mode=params["output_mode"],
    )

    logger.debug("[SAM2.1] Running generator.generate()")
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

    logger.debug(f"[SAM2.1] Completed mask generation → {len(results)} masks")
    return results
