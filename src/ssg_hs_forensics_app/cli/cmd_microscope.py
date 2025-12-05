import click
import asyncio
from loguru import logger

from ssg_hs_forensics_app.microscope.workflow import run_full_workflow
from ssg_hs_forensics_app.microscope.download import list_images
from ssg_hs_forensics_app.microscope.workflow_monitor import run_monitor


@click.group(name="microscope", invoke_without_command=True)
@click.pass_context
def cmd_microscope(ctx):
    """
    Microscope group
    """
    ctx.ensure_object(dict)

    if ctx.invoked_subcommand is None:
        logger.debug("Default microscope group command")
        click.echo(ctx.get_help())
        ctx.exit(0)


@cmd_microscope.command("debug-downloads")
def debug_downloads():
    from ssg_hs_forensics_app.microscope.capture_helpers import find_downloads_folder
    print("Downloads folder detected:", find_downloads_folder())

    
# ------------------------------------------------------------
# FULL WORKFLOW
# ------------------------------------------------------------
@cmd_microscope.command()
@click.pass_context
def run(ctx):
    """Run the full microscope workflow."""
    logger.info("Launching microscope workflow...")

    config = {
        "ssid": "iolight",
        "ui_url": "http://192.168.1.1",
    }

    result = asyncio.run(run_full_workflow(config))

    logger.info("Workflow completed successfully.")
    click.echo("\n=== WORKFLOW SUMMARY ===")
    for key, value in result.items():
        click.echo(f"{key}: {value}")


# ------------------------------------------------------------
# LIST COMMAND
# ------------------------------------------------------------
@cmd_microscope.command("list")
@click.pass_context
def list_cmd(ctx):
    """List images available on the ioLight microscope."""
    logger.info("Listing images available on the microscope...")
    result = asyncio.run(list_images())

    if not result:
        click.echo("No images found or unable to query microscope.")
    else:
        click.echo(f"\nFound {len(result)} image(s).")


# ------------------------------------------------------------
# WORKFLOW MONITOR (incremental scaffold)
# ------------------------------------------------------------
@cmd_microscope.command("monitor")
@click.pass_context
def monitor_cmd(ctx):
    """Run the incremental workflow monitor (scaffold)."""
    logger.info("Launching workflow monitor…")
    asyncio.run(run_monitor())
