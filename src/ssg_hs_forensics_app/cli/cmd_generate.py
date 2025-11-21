import click
from pathlib import Path
import time
import base64
import hashlib
from datetime import datetime
from loguru import logger

from ssg_hs_forensics_app.config_loader import load_builtin_config
from ssg_hs_forensics_app.config_logger import init_logging

from ssg_hs_forensics_app.core.sam_loader import load_sam_model
from ssg_hs_forensics_app.core.mask_generator import build_mask_generator, run_generator

# NEW: import both writers
from ssg_hs_forensics_app.core.masks import (
    write_masks_json,
    write_masks_h5,
    mask_name_for_image,
)


@click.command(name="generate")
@click.argument("image_path", type=click.Path(exists=True))
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    show_default=True,
    help="Allow overwriting an existing output file.",
)
@click.option(
    "--format",
    type=click.Choice(["json", "h5"], case_sensitive=False),
    default="h5",
    show_default=True,
    help="Output storage format for masks.",
)
def cmd_generate(image_path, overwrite, format):
    """
    Generate SAM masks for IMAGE_PATH and save results.

    Mask generator config is chosen from:
        mask_generator.{sam.model_type}.{sam.mask_config}

    Checkpoint is loaded from:
        [application].models_folder + sam.checkpoint

    Output is saved as either JSON or HDF5 (default).
    """
    # --------------------------------------------------------
    # Initialize logging
    # --------------------------------------------------------
    init_logging()
    logger.debug("cmd_generate invoked")

    # --------------------------------------------------------
    # Load configuration
    # --------------------------------------------------------
    cfg = load_builtin_config()
    logger.debug("Loaded built-in config.toml")

    sam_cfg = cfg["sam"]
    app_cfg = cfg["application"]

    # --------------------------------------------------------
    # Resolve paths
    # --------------------------------------------------------
    img_path = Path(image_path).resolve()
    mask_folder = Path(app_cfg.get("mask_folder", "masks")).expanduser().resolve()

    # Pick the right extension
    ext = "h5" if format == "h5" else "json"
    out_file = mask_folder / mask_name_for_image(img_path, ext=ext)

    logger.debug(f"Planned output file: {out_file}")

    if out_file.exists() and not overwrite:
        click.echo(
            f"ERROR: Output file already exists:\n  {out_file}\n"
            "Use --overwrite to replace it."
        )
        logger.error(f"Refusing to overwrite existing file: {out_file}")
        return

    # --------------------------------------------------------
    # Resolve model checkpoint path
    # --------------------------------------------------------
    models_folder = Path(app_cfg.get("models_folder", "models")).expanduser().resolve()
    checkpoint_name = sam_cfg["checkpoint"]
    checkpoint_path = (models_folder / checkpoint_name).resolve()

    logger.debug(f"Models folder resolved to: {models_folder}")
    logger.debug(f"Model checkpoint resolved to: {checkpoint_path}")

    if not checkpoint_path.exists():
        click.echo(f"ERROR: Checkpoint not found:\n  {checkpoint_path}")
        logger.error(f"Checkpoint missing: {checkpoint_path}")
        return

    # --------------------------------------------------------
    # Resolve mask generator PRESET
    # --------------------------------------------------------
    model_type = sam_cfg["model_type"]
    preset_name = sam_cfg.get("mask_config", "default")

    mk = cfg.get("mask_generator", {})
    model_group = mk.get(model_type, {})
    mg_cfg = model_group.get(preset_name)

    logger.debug(f"Available presets for {model_type}: {list(model_group.keys())}")

    if mg_cfg is None:
        click.echo(
            f"ERROR: Mask generator preset not found:\n"
            f"  mask_generator.{model_type}.{preset_name}"
        )
        logger.error(f"Missing mask generator preset for {model_type}.{preset_name}")
        return

    logger.debug(f"Using mask generator preset: {model_type}.{preset_name}")
    logger.debug(f"Mask generator configuration:\n{mg_cfg}")

    # --------------------------------------------------------
    # Load SAM model
    # --------------------------------------------------------
    logger.debug(
        f"Loading SAM model type='{model_type}' from checkpoint='{checkpoint_path}'"
    )
    sam = load_sam_model(model_type, str(checkpoint_path))

    # --------------------------------------------------------
    # Build mask generator instance
    # --------------------------------------------------------
    logger.debug("Building mask generator instance...")
    generator = build_mask_generator(sam, mg_cfg)

    # --------------------------------------------------------
    # RUN SAM with timing
    # --------------------------------------------------------
    click.echo(f"Processing image: {img_path}")
    logger.info(f"Running mask generator for: {img_path}")

    t0 = time.time()
    masks = run_generator(generator, img_path, mg_cfg=mg_cfg)
    t1 = time.time()

    # Log debugging about masks
    logger.debug(f"Mask generator returned type: {type(masks)}")
    if isinstance(masks, list):
        logger.debug(f"Returned {len(masks)} masks")

    # --------------------------------------------------------
    # Collect INPUT metadata (sha256 + base64)
    # --------------------------------------------------------
    sha256 = None
    base64_data = None

    try:
        with open(img_path, "rb") as f:
            raw = f.read()
            sha256 = hashlib.sha256(raw).hexdigest()
            base64_data = base64.b64encode(raw).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to read/encode image: {e}")

    input_info = {
        "image_name": img_path.name,
        "image_path": str(img_path),
        "sha256": sha256,
        "base64": base64_data,
    }

    # --------------------------------------------------------
    # MODEL metadata
    # --------------------------------------------------------
    model_info = {
        "model_type": model_type,
        "checkpoint": str(checkpoint_path),
        "mask_config": preset_name,
        "mask_parameters": mg_cfg,
    }

    # --------------------------------------------------------
    # RUNTIME metadata
    # --------------------------------------------------------
    runinfo = {
        "start_time": datetime.fromtimestamp(t0).isoformat(),
        "end_time": datetime.fromtimestamp(t1).isoformat(),
        "elapsed_seconds": t1 - t0,
    }

    # --------------------------------------------------------
    # SAVE using JSON or HDF5
    # --------------------------------------------------------
    mask_folder.mkdir(parents=True, exist_ok=True)

    if format == "json":
        logger.debug("Writing JSON output...")
        out_file = write_masks_json(
            img_path,
            masks,
            output_folder=mask_folder,
            input_info=input_info,
            model_info=model_info,
            runinfo=runinfo,
        )
    else:
        logger.debug("Writing HDF5 output...")
        out_file = write_masks_h5(
            img_path,
            masks,
            output_folder=mask_folder,
            input_info=input_info,
            model_info=model_info,
            runinfo=runinfo,
        )

    click.echo(f"Saved masks → {out_file}")
    logger.info(f"Mask generation complete → {out_file}")
