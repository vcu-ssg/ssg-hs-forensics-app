# src/ssg_hs_forensics_app/core/preset_loader.py

from __future__ import annotations
from loguru import logger
from ssg_hs_forensics_app.core.config import get_config


def load_preset_params(model_key: str, preset_name: str) -> dict:
    """
    Load preset mask-generator parameters for a given model.

    Config structure expected:

        [presets.<model_key>.<preset_name>]

    Example:
        load_preset_params("sam1_vit_b", "default")
        → returns the dict of parameters under:
            [presets.sam1_vit_b.default]

    Raises:
        KeyError with helpful diagnostics if not found.
    """

    cfg = get_config()   # merged built-in + user config

    presets_root = cfg.get("presets")
    if presets_root is None:
        raise KeyError(
            "config.toml is missing a [presets] section. "
            "Expected preset definitions under [presets.<model_key>.<preset_name>]."
        )

    # ------------------------------
    # Check model key
    # ------------------------------
    if model_key not in presets_root:
        available = ", ".join(sorted(presets_root.keys()))
        raise KeyError(
            f"No presets found for model key '{model_key}'.\n"
            f"Available preset groups: {available}"
        )

    model_presets = presets_root[model_key]

    # ------------------------------
    # Check preset name
    # ------------------------------
    if preset_name not in model_presets:
        available = ", ".join(sorted(model_presets.keys()))
        raise KeyError(
            f"Preset '{preset_name}' not defined for model '{model_key}'.\n"
            f"Available presets: {available}"
        )

    params = model_presets[preset_name]

    logger.debug(
        f"[Preset Loader] Loaded presets.{model_key}.{preset_name} → {params}"
    )

    return params
