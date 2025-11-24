# src/ssg_hs_forensics_app/cli/_main.py

import click
from pathlib import Path

from ssg_hs_forensics_app.core.config import get_config
from ssg_hs_forensics_app.core.logger import get_logger

from .cmd_generate import cmd_generate
from .cmd_masks import cmd_masks
from .cmd_config import cmd_config
from .cmd_images import cmd_images
from .cmd_models import cmd_models


@click.group(
    invoke_without_command=True,
    context_settings={"max_content_width": 120},
)
@click.option(
    "--log-level",
    type=click.Choice(
        ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"],
        case_sensitive=False,
    ),
    help="Override the log level defined in the config file.",
)
@click.option(
    "--config-file",
    type=click.Path(exists=True, dir_okay=False),
    help="Load an alternate config file instead of the default.",
)
@click.pass_context
def cli(ctx, log_level, config_file):
    """
    sammy — SAM image processing toolkit.

    \b
    Workflow:
        1) sammy images - to list available images
        2) sammy generate <image file name> to create mask file for image
        3) sammy masks  <mask file name> to view mask file

    \b
    Helpers
        * sammy masks  to view available mask files
        * sammy models to view available models
        * sammy images <image file name> to view image and details

    Details are available using --help for any command
    """

    ctx.ensure_object(dict)

    # ------------------------------------------------------------
    # Load CONFIG FILE (default OR user override)
    # ------------------------------------------------------------
    cfg = get_config(config_file_override=config_file)
    ctx.obj["config"] = cfg
    ctx.obj["config_file"] = config_file

    # ------------------------------------------------------------
    # Initialize logging AFTER knowing config + override
    # ------------------------------------------------------------
    effective_log_level = log_level or cfg["application"]["log_level"]
    ctx.obj["log_level_effective"] = effective_log_level
    ctx.obj["log_level_original"] = cfg["application"]["log_level"]

    log = get_logger(level_override=log_level)
    loaded_from = cfg.get("_loaded_from")
    log.debug(f"Loaded configuration from: {loaded_from}")


    # ------------------------------------------------------------
    # if no subcommmand, show help, etc.
    # ------------------------------------------------------------
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        click.echo("\nConfiguration summary:\n")
        _show_config_summary(
            cfg,
            config_file_used=cfg.get("_loaded_from"),
            effective_log_level=ctx.obj["log_level_effective"],
            original_log_level=ctx.obj["log_level_original"],
        )
        ctx.exit(0)


def _show_config_summary(cfg, config_file_used=None, effective_log_level=None, original_log_level=None):
    """Pretty-print selected configuration settings + model list."""

    app = cfg.get("application", {})
    model_cfg = cfg.get("models", {})

    click.echo("  Active config file:")
    click.echo(f"    {config_file_used}")

    # ------------------------------------------------------------
    # APPLICATION SETTINGS
    # ------------------------------------------------------------
    click.echo("\n  [application]")
    if effective_log_level and original_log_level and effective_log_level != original_log_level:
        click.echo(f"    log_level      = {effective_log_level}  (original: {original_log_level})")
    else:
        click.echo(f"    log_level      = {effective_log_level}")    
    click.echo(f"    config_folder  = {app.get('config_folder')}")
    click.echo(f"    image_folder   = {app.get('image_folder')}")
    click.echo(f"    mask_folder    = {app.get('mask_folder')}")
    click.echo(f"    model_folder   = {app.get('model_folder')}")

    # Base model folder for checking checkpoint existence
    model_folder = Path(app.get("model_folder", ""))

    # ------------------------------------------------------------
    # MODEL SETTINGS
    # ------------------------------------------------------------
    click.echo("\n  [models]")
    click.echo(f"    default        = {model_cfg.get('default')}")
    click.echo(f"    autodownload   = {model_cfg.get('autodownload')}")
    click.echo(f"    device         = {model_cfg.get('device')}")

    # ------------------------------------------------------------
    # AVAILABLE MODELS + CHECKPOINT STATUS
    # ------------------------------------------------------------
    click.echo("\n  Available models:")

    for name, info in model_cfg.items():
        if not isinstance(info, dict):
            continue
        if "checkpoint" not in info:
            continue

        desc = info.get("description", "(no description)")
        ckpt_name = info.get("checkpoint")

        ckpt_path = model_folder / ckpt_name
        downloaded = ckpt_path.exists()

        status = "[DOWNLOADED]" if downloaded else ""

        click.echo(f"    • {name:<20} — {desc} {status}")

    if model_cfg.get('autodownload',False):
        click.echo("  Per the autodownload setting above, models WILL be automatically downloaded on first use.")
    else:
        click.echo("  Per the autodownload setting above, models WILL NOT be automatically downloaded on first use.")


# Attach subcommands
cli.add_command(cmd_generate)
cli.add_command(cmd_masks)
cli.add_command(cmd_config)
cli.add_command(cmd_images)
cli.add_command(cmd_models)
