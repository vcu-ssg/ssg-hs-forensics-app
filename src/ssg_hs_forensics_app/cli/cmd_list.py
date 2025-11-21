import click
from pathlib import Path
from loguru import logger

from ssg_hs_forensics_app.config_loader import load_builtin_config
from ssg_hs_forensics_app.config_logger import init_logging
from ssg_hs_forensics_app.core.masks import list_mask_files


IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
MODEL_EXTS = {".pth", ".pt", ".onnx"}

@click.group(name="list")
def cmd_list():
    """List images or masks based on config settings."""
    init_logging()
    logger.debug("cmd_list initialized")
    pass


# ------------------------------------------------------------
# Helper: Format path as relative to cwd
# ------------------------------------------------------------
def _rel(path: Path) -> str:
    """Return path relative to cwd if possible."""
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        # fallback: show only filename if not under cwd
        return str(path.name)


# ------------------------------------------------------------
# LIST IMAGES
# ------------------------------------------------------------
@cmd_list.command("images")
def list_images():
    """List all image files under the configured image_folder."""

    init_logging()
    cfg = load_builtin_config()

    folder = cfg["application"].get("image_folder", ".")
    root = Path(folder).resolve()

    if not root.exists():
        click.echo(f"Image folder does not exist: {_rel(root)}")
        return

    click.echo(f"Listing images under: {_rel(root)}")
    logger.debug(f"Searching recursively under: {root}")

    count = 0
    for path in root.rglob("*"):
        if path.suffix.lower() in IMAGE_EXTS:
            click.echo(_rel(path))
            count += 1

    logger.info(f"Found {count} images")
    if count == 0:
        click.echo("No images found.")


# ------------------------------------------------------------
# LIST MASKS
# ------------------------------------------------------------
@cmd_list.command("masks")
def list_masks():
    """List all mask JSON files under the configured mask_folder."""

    init_logging()
    cfg = load_builtin_config()

    folder = cfg["application"].get("mask_folder", ".")
    root = Path(folder).resolve()

    if not root.exists():
        click.echo(f"Mask folder does not exist: {_rel(root)}")
        return

    click.echo(f"Listing masks under: {_rel(root)}")
    logger.debug(f"Searching recursively under: {root}")

    # ✅ FIX: pass mask_folder to list_mask_files()
    mask_files = list_mask_files(root)

    if not mask_files:
        click.echo("No mask files found.")
        logger.info("No mask files found.")
        return

    for path in mask_files:
        click.echo(_rel(path))

    logger.info(f"Found {len(mask_files)} mask files")


# ------------------------------------------------------------
# LIST MODELS
# ------------------------------------------------------------
@cmd_list.command("models")
def list_models():
    """List all pre-trained SAM models under the configured models_folder."""

    init_logging()
    cfg = load_builtin_config()

    # default to "models" if not provided
    folder = cfg["application"].get("models_folder", "models")
    root = Path(folder).resolve()

    if not root.exists():
        click.echo(f"Models folder does not exist: {_rel(root)}")
        return

    click.echo(f"Listing models under: {_rel(root)}")
    logger.debug(f"Searching recursively under: {root}")

    count = 0
    for path in root.rglob("*"):
        if path.suffix.lower() in MODEL_EXTS:
            click.echo(_rel(path))
            count += 1

    logger.info(f"Found {count} models")
    if count == 0:
        click.echo("No model files found.")

