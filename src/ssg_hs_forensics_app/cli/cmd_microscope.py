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
    Microscope group help goes here

    
    """
    ctx.ensure_object(dict)

    if ctx.invoked_subcommand is None:
        logger.debug("Default microscope group command")
        click.echo(ctx.get_help())
        ctx.exit(0)


    
# ------------------------------------------------------------
# WORKFLOW MONITOR (incremental scaffold)
# ------------------------------------------------------------
@cmd_microscope.command("run")
@click.pass_context
def monitor_cmd(ctx):
    """Run and monitor the microscope download process."""
    logger.info("Launching workflow monitor…")
    asyncio.run(run_monitor())
