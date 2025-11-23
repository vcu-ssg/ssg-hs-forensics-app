# src/ssg_hs_forensics_app/cli/cmd_generate.py

import click
from pathlib import Path
from loguru import logger
import time
from datetime import datetime

from ssg_hs_forensics_app.core.config import load_config
from ssg_hs_forensics_app.config_logger import init_logging

from ssg_hs_forensics_app.core.images import load_image_as_numpy
from ssg_hs_forensics_app.core.model_loader import load_model
from ssg_hs_forensics_app.core.model_factory import generate_masks

from ssg_hs_forensics_app.core.mask_writer import (
    write_masks_h5,
    mask_output_path,
)


@click.command(name="generate")
@click.argument("image_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--model",
    "model_name",
    metavar="MODEL_KEY",
    help="Override model selection (e.g., sam1_vit_b). "
         "If omitted, uses config.models.default.",
)
@click.option(
    "--presets",
    "preset_override",
    metavar="PRESET",
    help="Override the model's default preset "
         "(e.g., default, fast, detailed).",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    show_default=True,
    help="Overwrite existing .h5 mask file.",
)
def cmd_generate(
    image_path,
    model_name,
    preset_override,
    overwrite,
):
    """
    Generate segmentation masks using a selected SAM model + preset.
    Writes an HDF5 file containing:

      • Raw SAM masks
      • Original JPEG file (bytes only)
      • Image metadata
      • Model + preset metadata
      • Timing benchmark metadata

    All validation is performed BEFORE running the heavy SAM inference.
    """

    # ------------------------------------------------------------
    # Logging init
    # ------------------------------------------------------------
    init_logging()
    logger.debug("cmd_generate invoked")

    # ------------------------------------------------------------
    # PRE-CHECK PHASE
    # ------------------------------------------------------------
    image_path = Path(image_path)
    config = load_config()

    # Debug: show which config file was loaded
    cfg_file = config.get("__config_file__", "<unknown>")
    logger.debug(f"Loaded built-in config from: {cfg_file}")

    cfg_file = load_config()
    logger.debug(f"Loaded config from: {cfg_file.get('__config_file__', '<unknown>')}")

    models_cfg = config["models"]

    # ---- Resolve model key ----
    if model_name is None:
        model_key = models_cfg["default"]
        logger.debug(f"No --model provided, using default: {model_key}")
    else:
        model_key = model_name
        logger.debug(f"Using user-specified model: {model_key}")

    if model_key not in models_cfg:
        raise click.ClickException(
            f"Model '{model_key}' not found in [models] config."
        )

    model_cfg = models_cfg[model_key]

    # ------------------------------------------------------------
    # PRESET RESOLUTION + VALIDATION (global preset section)
    # ------------------------------------------------------------
    presets_cfg = config.get("presets", {})

    if model_key not in presets_cfg:
        raise click.ClickException(
            f"No preset definitions found for model '{model_key}' "
            f"under [presets.{model_key}]."
        )

    model_presets = presets_cfg[model_key]

    # Determine preset name: override → model default → error
    if preset_override:
        preset_name = preset_override
    elif "preset" in model_cfg:
        preset_name = model_cfg["preset"]
    else:
        raise click.ClickException(
            f"Model '{model_key}' has no default preset defined and "
            "no --presets override was provided."
        )

    # Validate preset exists
    if preset_name not in model_presets:
        raise click.ClickException(
            f"Preset '{preset_name}' is not defined for model '{model_key}'.\n"
            f"Available presets: {', '.join(model_presets.keys())}"
        )

    preset_dict = model_presets[preset_name]

    logger.debug(
        f"Using preset '{preset_name}' for model '{model_key}' "
        f"(override={preset_override is not None})"
    )

    # ------------------------------------------------------------
    # Load image early (decoded)
    # ------------------------------------------------------------
    image_np = load_image_as_numpy(image_path)
    height, width = image_np.shape[:2]
    channels = image_np.shape[2] if image_np.ndim == 3 else 1

    # ------------------------------------------------------------
    # Load model (fast)
    # ------------------------------------------------------------
    model_tuple = load_model(config, model_key=model_key, preset_name=preset_name)
    family, runtime_model, preset_used, preset_from_loader = model_tuple

    logger.debug(
        f"load_model returned preset_used='{preset_used}' "
        f"(input preset_name='{preset_name}')"
    )

    # ------------------------------------------------------------
    # Output path + overwrite check
    # ------------------------------------------------------------
    out_path = mask_output_path(
        image_path=image_path,
        model_key=model_key,
        preset=preset_used,
        mask_folder=Path(config["application"]["mask_folder"]),
    )

    if out_path.exists() and not overwrite:
        raise click.ClickException(
            f"Mask file already exists: {out_path}\n"
            f"Use --overwrite to replace it."
        )

    # ------------------------------------------------------------
    # Metadata before inference
    # ------------------------------------------------------------
    image_info = {
        "image_path": str(image_path),
        "width": width,
        "height": height,
        "channels": channels,
        "dtype": str(image_np.dtype),
        "shape": list(image_np.shape),
    }

    model_info = {
        "family": family,
        "model_type": model_cfg.get("type"),
        "checkpoint": (
            runtime_model.checkpoint_path
            if hasattr(runtime_model, "checkpoint_path")
            else model_cfg.get("checkpoint")
        ),
        "config_yaml": model_cfg.get("config"),
        "preset": preset_used,
        "model_key": model_key,
    }

    preset_info = preset_dict or {}

    # ------------------------------------------------------------
    # HEAVY PHASE — mask generation
    # ------------------------------------------------------------
    logger.debug("All pre-checks passed. Beginning SAM mask inference...")

    start_ts = datetime.now()
    start_perf = time.perf_counter()

    try:
        masks = generate_masks(model_tuple, image_np)

    except RuntimeError as e:
        msg = str(e).lower()

        if "cuda" in msg or "out of memory" in msg:
            raise click.ClickException(
                "The SAM model failed due to a GPU memory error.\n"
                "Possible fixes:\n"
                "  • Use a smaller model (sam1_vit_b)\n"
                "  • Use a faster preset (--presets fast)\n"
                "  • Downscale the input image\n"
                "  • Close GPU-heavy apps\n"
            )

        raise click.ClickException(f"Runtime error during SAM inference: {e}")

    except ValueError as e:
        raise click.ClickException(f"Value error in mask generation: {e}")

    except Exception as e:
        raise click.ClickException(f"Unexpected error: {e}")

    # ------------------------------------------------------------
    # Timing + throughput
    # ------------------------------------------------------------
    end_ts = datetime.now()
    elapsed = time.perf_counter() - start_perf
    megapixels = (width * height) / 1_000_000
    masks_per_sec = len(masks) / elapsed if elapsed > 0 else None
    mp_per_sec = megapixels / elapsed if elapsed > 0 else None

    logger.debug(f"Generated {len(masks)} masks in {elapsed:.2f} seconds")

    runinfo = {
        "filtering": "none",
        "start_time": start_ts.isoformat(),
        "end_time": end_ts.isoformat(),
        "elapsed_seconds": elapsed,
        "masks_per_second": masks_per_sec,
        "megapixels_processed": megapixels,
        "megapixels_per_second": mp_per_sec,
    }

    # ------------------------------------------------------------
    # JPEG-only writer call
    # ------------------------------------------------------------
    jpeg_bytes = image_path.read_bytes()   # <-- NEW: save original JPEG only

    logger.debug(
        f"Writing output HDF5 → {out_path} "
        f"(jpeg_bytes={len(jpeg_bytes)} bytes)"
    )

    write_masks_h5(
        out_path=out_path,
        masks=masks,
        jpeg_bytes=jpeg_bytes,
        image_info=image_info,
        model_info=model_info,
        preset_info=preset_info,
        runinfo=runinfo,
    )

    click.echo(
        f"✓ Wrote {len(masks)} raw masks to:\n"
        f"  {out_path}\n"
        f"Elapsed: {elapsed:.2f} seconds"
    )
