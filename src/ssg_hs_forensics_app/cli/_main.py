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
    # Initialize logging AFTER config is known
    # ------------------------------------------------------------
    effective_log_level = log_level or cfg["application"]["log_level"]
    ctx.obj["log_level_effective"] = effective_log_level
    ctx.obj["log_level_original"] = cfg["application"]["log_level"]

    log = get_logger(level_override=log_level)
    loaded_from = cfg.get("_loaded_from")
    log.debug(f"Loaded configuration from: {loaded_from}")

    # ------------------------------------------------------------
    # If no subcommand → JUST show help (NOT summary)
    # ------------------------------------------------------------
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        click.echo("\nRun 'sammy config' to see full configuration details.")
        ctx.exit(0)


# Attach subcommands
cli.add_command(cmd_generate)
cli.add_command(cmd_masks)
cli.add_command(cmd_config)
cli.add_command(cmd_images)
cli.add_command(cmd_models)
