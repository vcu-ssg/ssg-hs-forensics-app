import click
from pathlib import Path
from loguru import logger

from ssg_hs_forensics_app.config_loader import load_builtin_config
from ssg_hs_forensics_app.config_logger import init_logging

from ssg_hs_forensics_app.core.sam_loader import load_sam_model
from ssg_hs_forensics_app.core.mask_generator import build_mask_generator, run_generator
from ssg_hs_forensics_app.core.masks import write_masks_json, make_output_json_path


@click.command(name="generate")
@click.argument("image_path", type=click.Path(exists=True))
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    show_default=True,
    help="Allow overwriting an existing masks JSON file.",
)
def cmd_generate(image_path, overwrite):
    """
    Generate SAM masks for IMAGE_PATH and save results.

    Mask generator config is chosen from:
        mask_generator.{sam.model_type}.{sam.mask_config}

    Checkpoint is loaded from:
        [application].models_folder + sam.checkpoint

    Masks are saved into:
        [application].mask_folder
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
    # Compute mask output path **before running anything**
    # --------------------------------------------------------
    img_path = Path(image_path).resolve()
    mask_folder = Path(app_cfg.get("mask_folder", "masks")).expanduser().resolve()
    out_file = make_output_json_path(img_path, output_folder=mask_folder)

    logger.debug(f"Predicted output mask JSON path: {out_file}")

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
    sam = load_sam_model(
        model_type,
        str(checkpoint_path)
    )

    # --------------------------------------------------------
    # Build mask generator instance
    # --------------------------------------------------------
    logger.debug("Building mask generator instance...")
    generator = build_mask_generator(sam, mg_cfg)

    # --------------------------------------------------------
    # Run SAM on the image
    # --------------------------------------------------------
    click.echo(f"Processing image: {img_path}")
    logger.info(f"Running mask generator for: {img_path}")

    masks = run_generator(generator, img_path, mg_cfg=mg_cfg)

    # --------------------------------------------------------
    # DEBUG: Log what run_generator returned
    # --------------------------------------------------------
    logger.debug(f"Mask generator returned type: {type(masks)}")

    try:
        logger.debug(f"Number of masks returned: {len(masks)}")
    except Exception:
        logger.debug("Could not determine mask count (non-list output)")

    if isinstance(masks, list) and masks:
        logger.debug(f"Sample mask[0] keys: {list(masks[0].keys())}")
        if len(masks) > 1:
            logger.debug(f"Sample mask[1] keys: {list(masks[1].keys())}")
    else:
        logger.debug("Mask list empty or invalid.")

    # --------------------------------------------------------
    # Save masks
    # --------------------------------------------------------
    mask_folder.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Mask folder resolved to: {mask_folder}")

    out_file = write_masks_json(img_path, masks, output_folder=mask_folder)

    logger.debug(f"write_masks_json wrote file to: {out_file}")

    click.echo(f"Saved masks → {out_file}")
    logger.info(f"Mask generation complete → {out_file}")
