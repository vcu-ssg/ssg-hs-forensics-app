import click
import asyncio
from loguru import logger
from ssg_hs_forensics_app.microscope.workflow import run_full_workflow


@click.group(name="microscope")
def cmd_microscope():
    """Microscope acquisition workflow."""
    pass


@cmd_microscope.command()
def run():
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
