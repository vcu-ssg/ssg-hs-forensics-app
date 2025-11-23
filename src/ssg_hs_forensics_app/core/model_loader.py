# src/ssg_hs_forensics_app/core/model_loader.py

"""
Model Loader (Functional API)

Reads the unified model registry from config.toml:

    [models]
    default = "sam1_vit_b"
    autodownload = true

    [models.sam1_vit_b]
    family     = "sam1"
    type       = "vit_b"
    checkpoint = "sam_vit_b_01ec64.pth"
    url        = "https://..."
    config     = ""
    preset     = "default"

Produces a unified functional model tuple via make_model().
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional
from loguru import logger
import requests

from ssg_hs_forensics_app.core.model_factory import make_model


# --------------------------------------------------------------------
# load_model()
# --------------------------------------------------------------------
def load_model(
    cfg: Dict,
    *,
    model_key: Optional[str] = None,
    preset_name: Optional[str] = None,
):
    """
    Load a specific model (if model_key supplied) or fall back to
    the default model from config.

    Args:
        cfg: Entire application config dictionary
        model_key: Optional explicit model to load
        preset_name: Optional explicit preset override (e.g., 'fast')

    Returns:
        (family, runtime_model, preset_name, generator_fn)
    """

    models_cfg = cfg.get("models")
    if not models_cfg:
        raise KeyError("config.toml missing [models] section")

    # ------------------------------------------------------------
    # Determine which model key to use
    # ------------------------------------------------------------
    if model_key is None:
        model_key = models_cfg.get("default")
        if not model_key:
            raise KeyError("[models].default is missing")
        logger.debug(f"[Model Loader] Using default model '{model_key}'")
    else:
        logger.debug(f"[Model Loader] Using explicitly requested model '{model_key}'")

    if model_key not in models_cfg:
        available = ", ".join(k for k in models_cfg.keys() if k != "default")
        raise KeyError(
            f"Model '{model_key}' not found in [models].\n"
            f"Available models: {available}"
        )

    model_cfg = models_cfg[model_key]

    # ------------------------------------------------------------
    # Resolve required fields
    # ------------------------------------------------------------
    family = model_cfg["family"].lower()
    model_type = model_cfg.get("type")  # SAM1 only
    checkpoint = model_cfg["checkpoint"]
    config_yaml = model_cfg.get("config") or None

    # Preset resolution
    preset = preset_name or model_cfg.get("preset", "default")

    # ------------------------------------------------------------
    # Resolve absolute file paths
    # ------------------------------------------------------------
    model_root = Path(cfg["application"]["model_folder"]).expanduser().resolve()

    checkpoint_file = model_root / checkpoint
    checkpoint_path = checkpoint_file.as_posix()

    config_yaml_path = (
        (model_root / config_yaml).as_posix()
        if config_yaml not in (None, "")
        else None
    )

    # ------------------------------------------------------------
    # Auto-download logic
    # ------------------------------------------------------------
    autodownload = bool(models_cfg.get("autodownload", False))
    url = model_cfg.get("url")

    if not checkpoint_file.exists():

        if not autodownload:
            raise FileNotFoundError(
                f"[Model Loader] Checkpoint file not found:\n"
                f"  {checkpoint_file}\n"
                f"Auto-download disabled (models.autodownload = false)."
            )

        if not url:
            raise FileNotFoundError(
                f"[Model Loader] Checkpoint file missing and no URL provided.\n"
                f"Expected: {checkpoint_file}\n"
                f"Add 'url = \"https://...\"' to [models.{model_key}]"
            )

        # Ensure model_root exists
        model_root.mkdir(parents=True, exist_ok=True)

        logger.info(f"[Model Loader] Auto-downloading checkpoint for '{model_key}'")
        logger.info(f"  URL → {url}")
        logger.info(f"  Saving to → {checkpoint_file}")

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(checkpoint_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        except Exception as e:
            raise RuntimeError(
                f"[Model Loader] Failed to download checkpoint:\n"
                f"  URL: {url}\n"
                f"  Error: {e}"
            )

        # Validate
        if not checkpoint_file.exists():
            raise RuntimeError(
                f"[Model Loader] Downloaded checkpoint missing:\n"
                f"  {checkpoint_file}"
            )

    # ------------------------------------------------------------
    # Validate config YAML file (if applicable)
    # ------------------------------------------------------------
    if config_yaml_path is not None:
        config_file = Path(config_yaml_path)
        if not config_file.exists():
            raise FileNotFoundError(
                f"[Model Loader] Model config YAML not found:\n"
                f"  {config_file}\n"
                f"Check [models.{model_key}].config in config.toml"
            )

    # ------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------
    logger.debug(f"[Model Loader] Selected model: {model_key}")
    logger.debug("Resolved Model Info:")
    logger.debug(f"  model_key:       {model_key}")
    logger.debug(f"  family:          {family}")
    logger.debug(f"  type:            {model_type}")
    logger.debug(f"  checkpoint_path: {checkpoint_path}")
    logger.debug(f"  config_yaml:     {config_yaml_path}")
    logger.debug(f"  preset:          {preset}")

    # ------------------------------------------------------------
    # Build and return functional model wrapper from model_factory
    # ------------------------------------------------------------
    return make_model(
        family=family,
        model_type=model_type,
        checkpoint=checkpoint_path,
        config=config_yaml_path,
        preset=preset,
    )
