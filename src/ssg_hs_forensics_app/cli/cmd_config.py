"""
CLI commands for inspecting the built-in module configuration.
"""

from __future__ import annotations

import click
import tomllib
import tomli_w  # For pretty TOML output (installed automatically with Poetry)
from pathlib import Path

from ssg_hs_forensics_app.config_loader import get_builtin_config_path, load_builtin_config
from ssg_hs_forensics_app.config_logger import init_logging


@click.group(name="config")
def cmd_config():
    """Configuration inspection commands."""
    pass


# ============================================================
# SHOW
# ============================================================

@cmd_config.command("show")
def config_show():
    """
    Display the built-in config.toml in a nicely formatted TOML structure.
    """

    # Ensure logger is initialized before printing logs anywhere
    init_logging()

    cfg_path = get_builtin_config_path()
    cfg = load_builtin_config()

    click.echo(f"Using built-in config file:\n  {cfg_path}\n")

    # Pretty TOML output via tomli_w
    try:
        text = tomli_w.dumps(cfg)
        click.echo(text)
    except Exception:
        # fallback to raw dict printing
        click.echo(cfg)
