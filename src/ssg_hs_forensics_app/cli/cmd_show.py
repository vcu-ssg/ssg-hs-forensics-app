import click
from pathlib import Path
from loguru import logger

from ssg_hs_forensics_app.config_loader import load_builtin_config
from ssg_hs_forensics_app.config_logger import init_logging
from ssg_hs_forensics_app.core.masks import (
    load_masks_json,
    list_mask_files
)
from ssg_hs_forensics_app.core.postprocess import render_masks_overlay


@click.command(name="show")
@click.argument(
    "mask_file",
    required=False,
    type=click.Path(exists=True)
)
def cmd_show(mask_file):
    """
    Show mask files or visualize a specific mask.

    Usage:
        sammy show
            Lists all mask files in [application].mask_folder

        sammy show foo_masks.json
            Validates and displays mask overlays for that file
    """

    # Initialize logging
    init_logging()
    logger.debug("cmd_show invoked")

    # Load config so we know where mask files live
    cfg = load_builtin_config()
    mask_folder = Path(cfg["application"]["mask_folder"]).expanduser().resolve()

    # ------------------------------------------------------------
    # Case 1: No argument → List all masks
    # ------------------------------------------------------------
    if mask_file is None:
        click.echo(f"Mask folder:\n  {mask_folder}\n")

        mask_files = list_mask_files()

        if not mask_files:
            click.echo("No mask files found.")
            logger.info("No mask files found in mask folder.")
            return

        click.echo("Available mask files:\n")
        for mf in mask_files:
            click.echo(f"  {mf}")

        logger.info(f"Listed {len(mask_files)} mask files.")
        return

    # ------------------------------------------------------------
    # Case 2: Show a specific mask file
    # ------------------------------------------------------------

    mask_file = Path(mask_file).resolve()

    if not mask_file.name.endswith("_masks.json"):
        click.echo("ERROR: Argument must be a mask JSON file ending in '_masks.json'.")
        logger.error(f"Invalid mask file argument: {mask_file}")
        return

    # Load masks
    click.echo(f"Loading masks from:\n  {mask_file}")
    logger.debug(f"Loading mask file: {mask_file}")

    # load_masks_json expects the *image name*, so derive that
    image_stem = mask_file.stem.replace("_masks", "")
    possible_images = list(mask_folder.glob(f"{image_stem}.*"))

    if not possible_images:
        click.echo(f"No corresponding image found for mask file:\n  {mask_file}")
        logger.error(f"No matching image found for mask file: {mask_file}")
        return

    image_path = possible_images[0]
    logger.debug(f"Associated image found: {image_path}")

    masks = load_masks_json(image_path)
    click.echo(f"Loaded {len(masks)} masks.")

    # Render overlay
    render_masks_overlay(image_path, masks)
    logger.info("Mask visualization completed.")
