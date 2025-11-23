# src/ssg_hs_forensics_app/cli/cmd_models.py

import click
from pathlib import Path
from tabulate import tabulate
from loguru import logger

from ssg_hs_forensics_app.config_logger import init_logging
from ssg_hs_forensics_app.core.config import get_config


@click.group(name="models")
@click.pass_context
def cmd_models(ctx):
    """Inspect installed and available segmentation models."""
    init_logging()
    ctx.ensure_object(dict)
    logger.debug("cmd_models initialized")


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def _exists(path: Path | None) -> bool:
    return path is not None and path.exists()


def _status_icon(path: Path | None) -> str:
    return "✔" if _exists(path) else "✘"


def _resolve_paths(model_folder: Path, entry: dict):
    """
    Given a config model entry, return (ckpt_path, yaml_path).
    YAML is None for SAM1 models.
    """
    ckpt = entry.get("checkpoint")
    yaml = entry.get("config")

    ckpt_path = model_folder / ckpt if ckpt else None
    yaml_path = model_folder / yaml if yaml else None

    return ckpt_path, yaml_path


def _is_downloaded(entry: dict, ckpt_path: Path | None, yaml_path: Path | None) -> bool:
    """
    Determine whether the model is fully downloaded.

    - SAM1: checkpoint only
    - SAM2/SAM2.1: checkpoint + YAML
    """
    family = entry.get("family", "").lower()

    if family == "sam1":
        return _exists(ckpt_path)

    # SAM2 / SAM2.1
    return _exists(ckpt_path) and _exists(yaml_path)


# ---------------------------------------------------------------------
#  models list
# ---------------------------------------------------------------------

@cmd_models.command("list")
@click.pass_context
def models_list(ctx):
    """
    Show all models defined in config.toml, including:
        key, family, type, downloaded?, default marker.
    """
    cfg = ctx.obj["config"]
    model_folder = Path(cfg["application"]["model_folder"]).expanduser().resolve()

    models = cfg.get("models", {})
    default_key = models.get("default")

    rows = []

    # Loop through model records
    for key, entry in models.items():
        if key in ("default", "autodownload", "registry_file"):
            continue

        ckpt_path, yaml_path = _resolve_paths(model_folder, entry)
        downloaded = "✔" if _is_downloaded(entry, ckpt_path, yaml_path) else "✘"

        rows.append([
            key,
            entry.get("family"),
            entry.get("type"),
            downloaded,
            "<-- default" if key == default_key else "",
        ])

    headers = ["Key", "Family", "Type", "Downloaded", "Default"]
    click.echo(tabulate(rows, headers=headers, tablefmt="github"))

    click.echo(f"\nModel folder: {model_folder}")
    click.echo("✔ = available, ✘ = missing\n")


# ---------------------------------------------------------------------
#  models show <model_key>
# ---------------------------------------------------------------------

@cmd_models.command("show")
@click.argument("model_key")
@click.pass_context
def models_show(ctx, model_key):
    """
    Show detailed information about a specific model key
    (or the default model).
    """
    cfg = ctx.obj["config"]
    models = cfg.get("models", {})

    # Allow "sammy models show default"
    if model_key == "default":
        model_key = models.get("default")

    if model_key not in models:
        raise click.ClickException(f"Model '{model_key}' not found in config.toml")

    entry = models[model_key]
    model_folder = Path(cfg["application"]["model_folder"]).expanduser().resolve()

    ckpt_path, yaml_path = _resolve_paths(model_folder, entry)

    click.echo(f"\n=== Model: {model_key} ===\n")

    click.echo(f"Family:        {entry.get('family')}")
    click.echo(f"Type:          {entry.get('type')}")
    click.echo(f"Description:   {entry.get('description', '(none)')}\n")

    # ---------------------------------------------
    # Checkpoint
    # ---------------------------------------------
    ckpt = entry.get("checkpoint")
    click.echo(f"Checkpoint:    {ckpt}")
    click.echo(f"  Exists:      {_status_icon(ckpt_path)}   {ckpt_path}")

    # ---------------------------------------------
    # YAML (SAM2 / SAM2.1 only)
    # ---------------------------------------------
    yaml = entry.get("config")
    if yaml:
        click.echo(f"\nConfig YAML:   {yaml}")
        click.echo(f"  Exists:      {_status_icon(yaml_path)}   {yaml_path}")
    else:
        click.echo("\nConfig YAML:   (not required for SAM1)")

    # ---------------------------------------------
    # URLs
    # ---------------------------------------------
    click.echo(f"\nDownload URL:  {entry.get('url', '(none)')}")
    click.echo(f"Config URL:    {entry.get('config_url', '(none)')}\n")

    # ---------------------------------------------
    # Default?
    # ---------------------------------------------
    if model_key == models.get("default"):
        click.echo("(This is the DEFAULT model)\n")
