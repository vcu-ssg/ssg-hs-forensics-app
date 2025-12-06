import click
import asyncio
from loguru import logger

from ssg_hs_forensics_app.microscope.workflow_monitor import run_monitor
from ssg_hs_forensics_app.microscope.browser import open_ui
from ssg_hs_forensics_app.microscope.connectivity_helpers import open_wifi_settings_screen


@click.group(name="microscope", invoke_without_command=True)
@click.pass_context
def cmd_microscope(ctx):
    """
    Tools for working with an ioLight digital microscope.

    Commands include:

      \b
      run         Monitor the microscope workflow, detect new captures,
                  and automatically export images.
      \b
      quickstart  Open the ioLight Quick Start Guide PDF.

      \b
      wifi        Open the system Wi-Fi settings page.

      \b
      setup       Combined command helper.  Open the ioLight Quick Start Guide,
                  launch Wi-Fi settings, then begin the workflow monitor.

      
    Use 'sammy microscope <command> --help' for details on each command.
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
@click.option(
    "--autosave-previous/--no-autosave-previous",
    default=True,
    show_default=True,
    help="Automatically export previously-captured images."
)
@click.option(
    "--autosave-fresh/--no-autosave-fresh",
    default=True,
    show_default=True,
    help="Automatically export newly-captured images."
)
@click.option(
    "--clean-downloads/--no-clean-downloads",
    default=True,
    show_default=True,
    help="Delete downloaded files after exporting."
)
@click.pass_context
def monitor_cmd(
    ctx,
    autosave_previous,
    autosave_fresh,
    clean_downloads,
):
    """Run and monitor the image capture process."""
    logger.info("Launching workflow monitor…")

    asyncio.run(
        run_monitor(
            autosave_previous=autosave_previous,
            autosave_fresh=autosave_fresh,
            clean_downloads=clean_downloads,
        )
    )

# ------------------------------------------------------------
# WIFI SETTINGS
# ------------------------------------------------------------
@cmd_microscope.command("wifi")
def wifi_cmd():
    """Open the system Wi-Fi settings screen."""
    logger.info("Opening Wi-Fi settings screen…")
    asyncio.run(open_wifi_settings_screen())
    click.echo("Wi-Fi settings should now be open.")


# ------------------------------------------------------------
# IOlight Quick Start PDF
# ------------------------------------------------------------
@cmd_microscope.command("quickstart")
def quickstart_cmd():
    """Open the ioLight Quick Start PDF."""
    url = (
        "https://iolight.co.uk/wp-content/uploads/2025/01/"
        "Quick-Start-Guide-V8-3-A1-0-3-672-iOS680-fw16-05-06-24.pdf"
    )
    logger.info(f"Opening ioLight Quick Start Guide: {url}")
    asyncio.run(open_ui(url))
    click.echo("Quick Start Guide opened in your browser.")

# ------------------------------------------------------------
# SETUP COMMAND
# ------------------------------------------------------------
@cmd_microscope.command("setup")
@click.option(
    "--autosave-previous/--no-autosave-previous",
    default=True,
    show_default=True,
    help="Automatically export previously-captured images."
)
@click.option(
    "--autosave-fresh/--no-autosave-fresh",
    default=True,
    show_default=True,
    help="Automatically export newly-captured images."
)
@click.option(
    "--clean-downloads/--no-clean-downloads",
    default=True,
    show_default=True,
    help="Delete downloaded files after exporting."
)
@click.pass_context
def setup_cmd(
    ctx,
    autosave_previous,
    autosave_fresh,
    clean_downloads,
):
    """
    Open Quickstart → WiFi → Monitor.
    """

    quickstart_url = (
        "https://iolight.co.uk/wp-content/uploads/2025/01/"
        "Quick-Start-Guide-V8-3-A1-0-3-672-iOS680-fw16-05-06-24.pdf"
    )

    logger.info("Opening ioLight Quick Start Guide…")
    asyncio.run(open_ui(quickstart_url))

    click.echo("")
    click.echo("📄 The ioLight Quick Start Guide has been opened in your browser.")
    click.echo("")

    logger.info("Opening Wi-Fi settings to connect to the ioLight microscope…")
    asyncio.run(open_wifi_settings_screen())

    click.echo("")
    click.echo("📶 Please connect your computer to the ioLight Wi-Fi network.")
    click.echo("When connected, press ENTER to continue…")
    input()

    click.echo("\nLaunching workflow monitor…\n")
    logger.info("Starting workflow monitor after setup…")

    asyncio.run(
        run_monitor(
            autosave_previous=autosave_previous,
            autosave_fresh=autosave_fresh,
            clean_downloads=clean_downloads,
        )
    )
