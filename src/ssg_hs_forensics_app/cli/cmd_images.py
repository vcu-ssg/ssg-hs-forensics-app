# src/ssg_hs_forensics_app/cli/cmd_images.py

import click
from pathlib import Path
from loguru import logger

from ssg_hs_forensics_app.config_logger import init_logging
from ssg_hs_forensics_app.core.images import list_images as core_list_images


@click.command(name="images")
@click.pass_context
def cmd_images(ctx):
    """
    List all images under the configured image_folder.

    Equivalent to: sammy list images
    """
    ctx.ensure_object(dict)
    init_logging()

    cfg = ctx.obj["config"]

    # Resolve the image folder
    folder = cfg["application"].get("image_folder", "./images")
    root = Path(folder).expanduser().resolve()

    if not root.exists():
        click.echo(f"Image folder does not exist: {_rel(root)}")
        return

    click.echo(f"Listing images under: {_rel(root)}")
    logger.debug(f"Searching recursively under: {root}")

    # Shared core logic
    images = core_list_images(root)

    if not images:
        click.echo("No images found.")
        logger.info("No images found.")
        return

    for path in images:
        click.echo(_rel(path))

    logger.info(f"Found {len(images)} images")


# ------------------------------------------------------------
# Helper: Format path as relative to cwd
# ------------------------------------------------------------
def _rel(path: Path) -> str:
    """Return path relative to current working directory if possible."""
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path.name)
