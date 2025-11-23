"""
CLI commands for inspecting application configuration.
"""

from __future__ import annotations

import click
import tomli_w
from pathlib import Path

from ssg_hs_forensics_app.config_logger import init_logging
from ssg_hs_forensics_app.config_loader import (
    load_builtin_config,
    get_builtin_config_path,
)


@click.group(name="config")
@click.pass_context
def cmd_config(ctx):
    """Configuration inspection commands."""
    # Ensure our context is initialized
    ctx.ensure_object(dict)
    init_logging()


# =====================================================================
# merged (merged config)
# =====================================================================

@cmd_config.command("merged")
@click.pass_context
def config_merged(ctx):
    """
    Display the merged configuration (built-in + user override).
    """
    cfg = ctx.obj["config"]   # merged config injected by _main.py

    click.echo("Merged configuration (built-in + user override):\n")

    try:
        text = tomli_w.dumps(cfg)
        click.echo(text)
    except Exception:
        click.echo(cfg)


# =====================================================================
# BUILT-IN ONLY (original module config)
# =====================================================================

@cmd_config.command("built-in")
def config_built_in():
    """
    Display ONLY the built-in config.toml shipped with the module.
    """
    cfg_path = get_builtin_config_path()
    builtin = load_builtin_config()

    click.echo(f"Built-in config file:\n  {cfg_path}\n")

    try:
        text = tomli_w.dumps(builtin)
        click.echo(text)
    except Exception:
        click.echo(builtin)
