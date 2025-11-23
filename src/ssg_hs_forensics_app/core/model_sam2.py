# src/ssg_hs_forensics_app/core/model_sam2.py

"""
SAM2 Loader + Preset-aware Mask Generator (Unified Schema)
"""

from __future__ import annotations
import numpy as np
from typing import List, Dict
from loguru import logger

from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

# -----------------------------------------------------------
# Robust import of SAM2 automatic mask generator
# -----------------------------------------------------------

try:
    from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator as _MaskGen
except ImportError:
    try:
        from sam2.automatic_mask_generator import AutomaticMaskGenerator as _MaskGen
    except ImportError:
        # Fallback: try to find any class ending in "MaskGenerator"
        import sam2.automatic_mask_generator as _mod
        for _name in dir(_mod):
            if _name.lower().endswith("maskgenerator"):
                _MaskGen = getattr(_mod, _name)
                break
        else:
            raise ImportError(
                "SAM2: No mask generator class found in sam2.automatic_mask_generator."
            )

# Unified mask dictionary schema
from ssg_hs_forensics_app.core.mask_schema import make_mask_record

# Preset loader
from ssg_hs_forensics_app.core.preset_loader import load_preset_params


# -----------------------------------------------------------
# Load SAM2 model + predictor
# -----------------------------------------------------------
def load_sam2(checkpoint: str, config: str):
    """
    Load SAM2 using its YAML config + checkpoint.

    Returns:
        model, predictor
    """

    logger.debug(f"[SAM2] Loading model: checkpoint={checkpoint}, config={config}")

    model = build_sam2(
        config_path=config,
        checkpoint_path=checkpoint,
    )

    predictor = SAM2ImagePredictor(model)

    # Default model_key — overwritten by model_loader to be exact ("sam2_hiera_small")
    predictor.model_key = "sam2"

    return model, predictor


# -----------------------------------------------------------
# Generate SAM2 masks (Preset-aware)
# -----------------------------------------------------------
def sam2_generate_masks(
    predictor,
    np_image: np.ndarray,
    preset_name: str,
) -> List[Dict]:
    """
    Generate SAM2 masks using unified schema and a preset block:

        [presets.sam2_<variant>.<preset_name>]

    Examples:
        presets.sam2_hiera_tiny.default
        presets.sam2_hiera_small.fast
        presets.sam2_hiera_large.detailed
    """

    model_key = getattr(predictor, "model_key", None)
    if model_key is None:
        raise RuntimeError(
            "SAM2 predictor is missing model_key. "
            "Your load_sam2() must assign predictor.model_key."
        )

    # Load preset parameters (SAM2 uses probability masks)
    params = load_preset_params(model_key, preset_name)

    logger.debug(
        f"[SAM2] Using preset '{preset_name}' "
        f"for model '{model_key}': {params}"
    )

    # Instantiate SAM2 mask generator with preset parameters
    generator = _MaskGen(
        predictor.model,
        points_per_side=params["points_per_side"],
        pred_iou_thresh=params["pred_iou_thresh"],
        stability_score_thresh=params["stability_score_thresh"],
        crop_n_layers=params["crop_n_layers"],
        min_mask_region_area=params["min_mask_region_area"],
        output_mode=params["output_mode"],  # typically "probability"
    )

    logger.debug("[SAM2] Running generator.generate()")
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

    logger.debug(f"[SAM2] Completed mask generation → {len(results)} masks")
    return results
