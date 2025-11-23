"""
Model loader for SAM1, SAM2, and SAM2.1 models.

Responsibilities:
- Read model metadata from merged configuration
- Resolve checkpoint + config YAML paths
- Autodownload missing files when enabled
- Load preset parameters
- Dispatch to correct model-family loader

Returns FOUR values:
    (family, predictor_or_model, preset_name, preset_params)

This matches what cmd_generate.py expects.
"""

from __future__ import annotations
from pathlib import Path
from typing import Tuple, Any, Dict

from loguru import logger
import requests
import torch


# Family loaders
from ssg_hs_forensics_app.core.model_sam1 import load_sam1, sam1_generate_masks
from ssg_hs_forensics_app.core.model_sam2 import load_sam2, sam2_generate_masks
from ssg_hs_forensics_app.core.model_sam21 import load_sam21, sam21_generate_masks

# Preset loader
from ssg_hs_forensics_app.core.preset_loader import load_preset_params


# ======================================================================
# Helpers
# ======================================================================

def _download_to(path: Path, url: str):
    """Download a file from URL into the specified path."""
    logger.debug(f"[model-loader] Downloading: {url}")
    resp = requests.get(url)
    resp.raise_for_status()
    path.write_bytes(resp.content)
    logger.debug(f"[model-loader] Saved file to: {path}")


def _resolve_file(
    folder: Path,
    filename_or_url: str,
    url_fallback: str | None,
    autodownload: bool,
    file_label: str,
) -> Path:
    """
    Resolve a required file such as a checkpoint or config YAML.

    Rules:
      - If filename_or_url contains '://', treat it as a direct remote URL.
      - Else treat as local filename under model folder.
      - If missing locally and autodownload enabled → fetch from URL fallback.
    """

    # Case A: Direct URL explicitly provided
    if "://" in filename_or_url:
        direct_url = filename_or_url
        local_name = Path(direct_url).name
        local_path = folder / local_name
        if not local_path.exists():
            if autodownload:
                _download_to(local_path, direct_url)
            else:
                raise FileNotFoundError(
                    f"[Model Loader] {file_label} missing: {local_path}\n"
                    f"Autodownload disabled; cannot fetch {direct_url}"
                )
        return local_path

    # Case B: Filename inside models/ folder
    local_path = folder / filename_or_url

    if local_path.exists():
        return local_path

    # Missing locally — need fallback URL
    if not url_fallback:
        raise FileNotFoundError(
            f"[Model Loader] {file_label} not found:\n"
            f"  {local_path}\n"
            f"No URL fallback provided in config.toml"
        )

    if not autodownload:
        raise FileNotFoundError(
            f"[Model Loader] {file_label} not found:\n"
            f"  {local_path}\n"
            f"Autodownload disabled; cannot fetch from:\n"
            f"  {url_fallback}"
        )

    # Download fallback
    _download_to(local_path, url_fallback)
    return local_path


# ======================================================================
# Device resolution helper
# ======================================================================

def resolve_device(device_str: str) -> str:
    """
    Resolve 'cpu' | 'cuda' | 'auto' to the actual device the model should use.
    Logs the final choice.
    """

    requested = device_str.strip().lower()

    # Explicit CUDA request
    if requested == "cuda":
        if torch.cuda.is_available():
            logger.debug("[Model Loader] Device request 'cuda' → using CUDA")
            return "cuda"
        logger.warning("[Model Loader] 'cuda' requested but no CUDA available → using CPU")
        return "cpu"

    # Automatic selection
    if requested == "auto":
        if torch.cuda.is_available():
            logger.debug("[Model Loader] Device 'auto' resolved to CUDA")
            return "cuda"
        if torch.backends.mps.is_available():
            logger.debug("[Model Loader] Device 'auto' resolved to Apple MPS")
            return "mps"
        logger.debug("[Model Loader] Device 'auto' resolved to CPU")
        return "cpu"

    # Default
    logger.debug("[Model Loader] Device request 'cpu' → using CPU")
    return "cpu"


# ======================================================================
# Public API
# ======================================================================

def load_model(
    config: Dict[str, Any],
    model_key: str,
    preset_name: str,
) -> Tuple[str, Any, str, Dict[str, Any]]:
    """
    Resolve and load a model described in config["models"][model_key].

    Returns:
        (family, predictor_or_model, preset_name, preset_params)
    Matching exactly what cmd_generate.py expects.
    """
    logger.debug(f"[Model Loader] Using explicitly requested model '{model_key}'")

    models_section = config.get("models", {})
    if model_key not in models_section:
        raise KeyError(f"[Model Loader] Unknown model key: '{model_key}'")

    model_entry = models_section[model_key]

    # ------------------------------------------------------------------
    # Basic metadata
    # ------------------------------------------------------------------
    family = model_entry.get("family")
    model_type = model_entry.get("type")

    if not family:
        raise ValueError(f"[Model Loader] Missing `family` for model '{model_key}'")
    if not model_type:
        raise ValueError(f"[Model Loader] Missing `type` for model '{model_key}'")

    # ------------------------------------------------------------------
    # Folder + autodownload
    # ------------------------------------------------------------------
    app_cfg = config.get("application", {})
    model_folder = Path(app_cfg.get("model_folder", "./models")).expanduser().resolve()
    model_folder.mkdir(parents=True, exist_ok=True)

    autodownload = bool(models_section.get("autodownload", False))

    # ------------------------------------------------------------------
    # Resolve device (default: cpu)
    # ------------------------------------------------------------------
    raw_device = models_section.get("device", "cpu")
    device = resolve_device(raw_device)
    logger.debug(f"[Model Loader] Final resolved device: {device}")

    # ------------------------------------------------------------------
    # Resolve checkpoint
    # ------------------------------------------------------------------
    checkpoint_name = model_entry.get("checkpoint")
    checkpoint_url = model_entry.get("url")

    if not checkpoint_name:
        raise ValueError(
            f"[Model Loader] Missing `checkpoint` for model '{model_key}'"
        )

    ckpt_path = _resolve_file(
        folder=model_folder,
        filename_or_url=checkpoint_name,
        url_fallback=checkpoint_url,
        autodownload=autodownload,
        file_label="Model checkpoint (.pt)",
    )

    # ------------------------------------------------------------------
    # Resolve config YAML
    # ------------------------------------------------------------------
    config_value = model_entry.get("config")
    config_url = model_entry.get("config_url")

    # SAM1 does not require a config YAML
    if family == "sam1":
        yaml_path = None
    else:
        if not config_value:
            raise ValueError(
                f"[Model Loader] Missing `config` entry for model '{model_key}' "
                f"in config.toml"
            )

        yaml_path = _resolve_file(
            folder=model_folder,
            filename_or_url=config_value,
            url_fallback=config_url,
            autodownload=autodownload,
            file_label="Model config YAML",
        )


    # ------------------------------------------------------------------
    # Load preset parameters
    # ------------------------------------------------------------------
    preset_params = load_preset_params(model_key, preset_name)

    # ------------------------------------------------------------------
    # Dispatch by family
    # ------------------------------------------------------------------
    if family == "sam1":
        if not model_type:
            raise ValueError(
                f"[Model Loader] SAM1 model '{model_key}' requires a `type` "
                f"(vit_b, vit_l, vit_h) in config.toml"
            )

        # Pass checkpoint + model_type
        model = load_sam1(
            checkpoint=ckpt_path,
            model_type=model_type,
            device=device,
        )

        # SAM1 has no predictor wrapper, so runtime_model = model
        return ("sam1", model, preset_name, preset_params)
    
    elif family == "sam2":
        model, predictor = load_sam2(
            checkpoint=ckpt_path,
            config=yaml_path,
            device=device,
        )
        return ("sam2", predictor, preset_name, preset_params)

    elif family in ("sam2.1", "sam21"):
        model, predictor = load_sam21(
            checkpoint=ckpt_path,
            config=yaml_path,
            device=device,
        )
        return ("sam21", predictor, preset_name, preset_params)

    else:
        raise ValueError(
            f"[Model Loader] Unknown model family '{family}' for '{model_key}'"
        )


# ======================================================================
# Mask-generation dispatcher
# ======================================================================

def run_model_generate_masks(
    family: str,
    model_or_predictor: Any,
    image_np,
    mg_config: Dict[str, Any],
):
    """
    Dispatch mask generation based on model family.
    """
    if family == "sam1":
        return sam1_generate_masks(model_or_predictor, image_np, mg_config)

    if family == "sam2":
        return sam2_generate_masks(model_or_predictor, image_np, mg_config)

    if family == "sam21":
        return sam21_generate_masks(model_or_predictor, image_np, mg_config)

    raise ValueError(f"[Model Loader] Unsupported model family: {family}")
