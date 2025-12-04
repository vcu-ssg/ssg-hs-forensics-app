# src/ssg_hs_forensics_app/cli/cmd_config.py

"""
Configuration commands for inspecting Sammy configuration.
Matches structure of cli/cmd_images.py.
"""

from __future__ import annotations

import click
import tomli_w
from loguru import logger
from pathlib import Path

from ssg_hs_forensics_app.config_loader import (
    load_builtin_config,
    get_builtin_config_path,
)
from ssg_hs_forensics_app.core.system import get_system_summary


@click.group(name="config", invoke_without_command=True)
@click.pass_context
def cmd_config(ctx):
    """
    Inspect configuration settings.

    """
    ctx.ensure_object(dict)

    # If invoked without subcommand → show help and summary
    if ctx.invoked_subcommand is None:
        logger.debug("Default config group command")
        #click.echo(ctx.get_help())
        click.echo("\nConfiguration summary:\n")
        _show_config_summary(ctx.obj["config"])
        ctx.exit(0)


# =====================================================================
# Internal: summary printer
# =====================================================================

def _show_config_summary(cfg: dict):
    """Pretty-print selected configuration settings + system + models."""

    app = cfg.get("application", {})
    models = cfg.get("models", {})
    model_folder = Path(app.get("model_folder", ""))

    click.echo("  Active config file:")
    click.echo(f"    {cfg.get('_loaded_from')}")

    # ------------------------------------------------------------
    # APPLICATION
    # ------------------------------------------------------------
    click.echo("\n  [application]")
    click.echo(f"    log_level      = {app.get('log_level')}")
    click.echo(f"    config_folder  = {app.get('config_folder')}")
    click.echo(f"    image_folder   = {app.get('image_folder')}")
    click.echo(f"    mask_folder    = {app.get('mask_folder')}")
    click.echo(f"    model_folder   = {app.get('model_folder')}")

    # ------------------------------------------------------------
    # MODEL SETTINGS
    # ------------------------------------------------------------
    click.echo("\n  [models]")
    click.echo(f"    default        = {models.get('default')}")
    click.echo(f"    autodownload   = {models.get('autodownload')}")
    click.echo(f"    device         = {models.get('device')}")

    # ------------------------------------------------------------
    # SYSTEM DETAILS
    # ------------------------------------------------------------
    click.echo("\n  [system]")

    system = get_system_summary()

    click.echo(f"    os             = {system['os_name']}")
    click.echo(f"    os_version     = {system['os_version']}")
    click.echo(f"    cuda_hardware  = {'Available' if system['cuda_hardware'] else 'Not available'}")
    click.echo(f"    cuda_detail    = {system['cuda_hardware_detail']}")
    click.echo(f"    torch          = {'Installed' if system['torch_installed'] else 'Not installed'}")
    click.echo(f"    torch_cuda     = {'cuda' if system['torch_cuda'] else 'No cuda'} ({system['torch_detail']})")

    # ------------------------------------------------------------
    # Model recommendations (but do NOT override loader logic!)
    # ------------------------------------------------------------
    desired_device = models.get("device", "cpu")

    if system["cuda_hardware"] and desired_device == "cpu":
        click.echo("    ⚠ Recommendation: CUDA available, but config requests CPU.")
        click.echo("      Consider setting models.device = 'cuda' or 'auto'.")

    if not system["cuda_hardware"] and desired_device == "cuda":
        click.echo("    ⚠ Warning: config requests CUDA, but CUDA hardware not detected.")
        click.echo("      model_loader will fall back to CPU.")

    if ("Windows" in system["os_name"]
        and system["cuda_hardware"]
        and not system["torch_cuda"]):
        click.echo("    ⚠ Windows + CUDA hardware detected but Torch is CPU-only.")
        click.echo("      Installing CUDA-enabled Torch on Windows is difficult.")
        click.echo("      Consider using WSL for easier CUDA support.")

    # ------------------------------------------------------------
    # AVAILABLE MODELS
    # ------------------------------------------------------------
    click.echo("\n  Available models:")

    for name, info in models.items():
        if not isinstance(info, dict) or "checkpoint" not in info:
            continue

        desc = info.get("description", "(no description)")
        ckpt_path = model_folder / info["checkpoint"]
        downloaded = ckpt_path.exists()
        status = "[DOWNLOADED]" if downloaded else ""

        click.echo(f"    • {name:<20} — {desc} {status}")

    if models.get("autodownload", False):
        click.echo("  Per autodownload setting, models WILL be auto-downloaded.")
    else:
        click.echo("  Per autodownload setting, models WILL NOT be auto-downloaded.")
