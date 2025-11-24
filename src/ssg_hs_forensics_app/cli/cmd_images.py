# src/ssg_hs_forensics_app/cli/cmd_images.py

import click
from pathlib import Path
from PIL import Image
from loguru import logger

import matplotlib.pyplot as plt
import numpy as np

from ssg_hs_forensics_app.core.logger import get_logger
from ssg_hs_forensics_app.core.images import (
    list_images,
    get_image_by_index,
    get_image_by_name,
)


@click.command(name="images")
@click.argument("target", required=False)
@click.option(
    "--view",
    is_flag=True,
    help="Display the image (only works when inspecting a single image).",
)
@click.pass_context
def cmd_images(ctx, target, view):
    """
    List available images, or inspect one by name or index.

    Usage:
        sammy images
            - List all images

        sammy images 3
            - Inspect image #3

        sammy images sample.jpg
            - Inspect by filename

        sammy images sample.jpg --view
            - Display image
    """

    cfg = ctx.obj["config"]
    log = get_logger()

    folder = Path(cfg["application"]["image_folder"]).expanduser().resolve()
    if not folder.exists():
        click.echo(f"Image folder does not exist: {folder}")
        return

    # ------------------------------------------------------------
    # Get all images
    # ------------------------------------------------------------
    records = list_images(folder)

    if not target:
        # LIST MODE
        click.echo(f"Listing images under: {folder}")
        for rec in records:
            click.echo(f"  {rec['index']:3d}: {rec['name']}")
        return

    # ------------------------------------------------------------
    # INSPECTION MODE
    # ------------------------------------------------------------

    # Try interpret target as index
    meta = None
    if target.isdigit():
        idx = int(target)
        meta = get_image_by_index(records, idx)

    # Fallback: treat target as filename
    if not meta:
        meta = get_image_by_name(records, target)

    if not meta:
        click.echo(f"Image not found: {target}")
        return

    # Display metadata
    click.echo(f"Image #{meta['index']}: {meta['name']}")
    click.echo(f"  Path:      {meta['path']}")
    click.echo(f"  Size:      {meta['width']} x {meta['height']}")
    click.echo(f"  Format:    {meta['format']}")
    click.echo(f"  Mode:      {meta['mode']}")
    click.echo(f"  Bytes:     {meta['size_bytes']:,}")
    click.echo(f"  Created:   {meta['created']}")
    click.echo(f"  Modified:  {meta['modified']}")

    if meta["exif"]:
        click.echo("  EXIF:")
        for k, v in meta["exif"].items():
            click.echo(f"    {k}: {v}")

    # ------------------------------------------------------------
    # Optional image viewer
    # ------------------------------------------------------------
    if view:
        try:
            img = Image.open(path := meta["path"]).convert("RGB")
            arr = np.array(img)

            click.echo("Opening image viewer...")

            fig, ax = plt.subplots(1, 1, figsize=(8, 8))
            ax.imshow(arr)
            ax.set_title(meta["name"])
            ax.axis("off")
            plt.tight_layout()
            plt.show()

        except Exception as e:
            click.echo(f"Failed to display image: {e}")
            logger.error(f"cmd_images: failed to display image {meta['path']}: {e}")