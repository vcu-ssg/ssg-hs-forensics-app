# src/ssg_hs_forensics_app/cli/cmd_models.py

"""
Model inspection command for Sammy.

Supports:
    - Listing models with sequence numbers
    - Selecting a model by key or by index
    - Showing default + available presets
"""

from __future__ import annotations

import click
from pathlib import Path

from ssg_hs_forensics_app.core.preset_loader import load_all_presets_for_model


@click.command(name="models")
@click.argument("target", required=False)
@click.pass_context
def cmd_models(ctx, target):
    """
    Inspect SAM model registry.

    Usage:
        sammy models
            - List all models

        sammy models 3
            - Show details for model #3

        sammy models sam2_hiera_small
            - Show details by model key

    """
    cfg = ctx.obj["config"]
    models_cfg = cfg.get("models", {})
    app_cfg = cfg.get("application", {})
    model_folder = Path(app_cfg.get("model_folder", "./models")).expanduser().resolve()

    # ------------------------------------------------------------
    # Build list of model-entries (sequence-numbered)
    # ------------------------------------------------------------
    records = []
    seq = 1
    for key, info in models_cfg.items():
        if not isinstance(info, dict):
            continue
        if "checkpoint" not in info:
            continue

        records.append({
            "index": seq,
            "key": key,
            "info": info,
        })
        seq += 1

    # ------------------------------------------------------------
    # NO TARGET → LIST MODELS
    # ------------------------------------------------------------
    if not target:
        click.echo("\n[models]")
        click.echo(f"default        = {models_cfg.get('default')}")
        click.echo(f"autodownload   = {models_cfg.get('autodownload')}")
        click.echo(f"device         = {models_cfg.get('device')}")

        click.echo("\nAvailable models:\n")
        for r in records:
            key = r["key"]
            info = r["info"]
            desc = info.get("description", "(no description)")
            ckpt_path = model_folder / info["checkpoint"]
            downloaded = ckpt_path.exists()
            status = "[DOWNLOADED]" if downloaded else ""
            click.echo(f"  {r['index']:2d}: {key:<20} — {desc} {status}")

        return

    # ------------------------------------------------------------
    # TARGET GIVEN → RESOLVE MODEL
    # ------------------------------------------------------------
    record = None

    # Numeric sequence index?
    if target.isdigit():
        idx = int(target)
        record = next((r for r in records if r["index"] == idx), None)

    # Model key?
    if record is None:
        record = next((r for r in records if r["key"] == target), None)

    if record is None:
        click.echo(f"Model not found: {target}")
        return

    # ------------------------------------------------------------
    # SHOW MODEL DETAIL
    # ------------------------------------------------------------
    key = record["key"]
    info = record["info"]

    click.echo(f"\nModel #{record['index']}: {key}")
    click.echo(f"  Family:      {info.get('family')}")
    click.echo(f"  Type:        {info.get('type')}")
    click.echo(f"  Description: {info.get('description', '(no description)')}")

    # Checkpoint
    ckpt_name = info.get("checkpoint")
    ckpt_path = model_folder / ckpt_name
    downloaded = ckpt_path.exists()
    click.echo(f"\n  Checkpoint:")
    click.echo(f"    file:      {ckpt_name}")
    click.echo(f"    path:      {ckpt_path}")
    click.echo(f"    exists:    {downloaded}")
    if url := info.get("url"):
        click.echo(f"    url:       {url}")

    # Config YAML
    if info.get("family") != "sam1":
        yaml_name = info.get("config")
        yaml_path = model_folder / yaml_name
        click.echo("\n  Config YAML:")
        click.echo(f"    file:      {yaml_name}")
        click.echo(f"    path:      {yaml_path}")
        if url := info.get("config_url"):
            click.echo(f"    url:       {url}")
    else:
        click.echo("\n  Config YAML: (not required for SAM1)")

    # Default preset
    default_preset = info.get("preset", "(none)")
    click.echo(f"\n  Default preset: {default_preset}")

    # Available presets
    click.echo("\n  Available presets:")
    presets = load_all_presets_for_model(cfg, key)

    if not presets:
        click.echo("    (none)")
    else:
        for pname in sorted(presets.keys()):
            click.echo(f"    • {pname}")

    click.echo("")  # final spacing
