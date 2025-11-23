# src/ssg_hs_forensics_app/core/model_factory.py

"""
Functional Unified Model Factory (safe execution version)

Returns:
    (family, model_or_predictor, preset_name, generator_fn)

Used by cmd_generate:
    family, runtime_model, preset_name, generate_fn = make_model(...)

Then:
    masks = generate_fn(runtime_model, np_image, preset_name)
"""

from __future__ import annotations
from typing import Any, Callable, Tuple
from loguru import logger

from ssg_hs_forensics_app.core.model_sam1 import (
    load_sam1,
    sam1_generate_masks,
)
from ssg_hs_forensics_app.core.model_sam2 import (
    load_sam2,
    sam2_generate_masks,
)
from ssg_hs_forensics_app.core.model_sam21 import (
    load_sam21,
    sam21_generate_masks,
)

from ssg_hs_forensics_app.core.safe_generate_masks import safe_generate_masks


# ---------------------------------------------------------
# MAIN FACTORY
# ---------------------------------------------------------
def make_model(
    *,
    family: str,
    model_type: str | None,
    checkpoint: str,
    config: str | None,
    preset: str,
) -> Tuple[str, Any, str, Callable]:
    """
    Build a functional model wrapper.

    Returns: (family, model_or_predictor, preset_name, generate_masks_fn)
    """

    fam = family.lower().strip()

    logger.debug(
        f"[Model Factory] Building model: family={fam}, "
        f"type={model_type}, checkpoint={checkpoint}, "
        f"config={config}, preset={preset}"
    )

    # ---------------------------------------------------------
    # SAM1
    # ---------------------------------------------------------
    if fam == "sam1":
        if not model_type:
            raise ValueError("SAM1 requires model_type (vit_b / vit_l / vit_h)")
        model = load_sam1(checkpoint, model_type=model_type)
        return ("sam1", model, preset, _safe_wrapper(sam1_generate_masks))

    # ---------------------------------------------------------
    # SAM2
    # ---------------------------------------------------------
    if fam == "sam2":
        model, predictor = load_sam2(checkpoint, config)
        return ("sam2", predictor, preset, _safe_wrapper(sam2_generate_masks))

    # ---------------------------------------------------------
    # SAM2.1
    # ---------------------------------------------------------
    if fam in ("sam21", "sam2.1", "sam2_1"):
        model, predictor = load_sam21(checkpoint, config)
        return ("sam21", predictor, preset, _safe_wrapper(sam21_generate_masks))

    raise ValueError(f"Unknown SAM family '{family}'")


# ---------------------------------------------------------
# GENERIC SAFE WRAPPER
# ---------------------------------------------------------
def _safe_wrapper(generator_fn):
    """
    Wrap generator_fn so that calls are dispatched into
    safe_generate_masks() automatically.
    """

    def wrapped(runtime_model, np_image, preset_name):
        logger.debug(
            f"[Model Factory] Dispatching mask generation through safe wrapper "
            f"(preset={preset_name})"
        )
        return safe_generate_masks(
            generator_fn,
            runtime_model,
            np_image,
            preset_name,
            timeout=300,  # can tune later
        )

    return wrapped


# ---------------------------------------------------------
# SUPPORT FUNCTION (CLI convenience)
# ---------------------------------------------------------
def generate_masks(model_tuple, np_image):
    """
    model_tuple = (family, runtime_model, preset_name, generator_fn)
    """
    family, runtime_model, preset_name, generator_fn = model_tuple

    logger.debug(
        f"[Model Factory] generate_masks → family={family}, preset={preset_name}"
    )

    # generator_fn is already a safe wrapper
    return generator_fn(runtime_model, np_image, preset_name)
