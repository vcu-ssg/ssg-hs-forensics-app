import click
import asyncio
from ssg_hs_forensics_app.microscope.workflow import run_full_session
from ssg_hs_forensics_app.microscope.platform import get_wifi_adapter


@click.group(name="microscope")
def cmd_microscope():
    """Microscope automation workflow."""
    pass


@cmd_microscope.command()
def run():
    """Run the full microscope workflow."""
    asyncio.run(run_full_session())
    click.echo("Microscope workflow completed.")


@cmd_microscope.command()
def connect():
    """Connect to microscope Wi-Fi only."""
    wifi = get_wifi_adapter()
    asyncio.run(wifi.connect("iolight"))
    click.echo("Connected to microscope Wi-Fi.")


@cmd_microscope.command()
@click.argument("ssid")
def restore(ssid):
    """Restore a specific Wi-Fi network by SSID."""
    wifi = get_wifi_adapter()
    asyncio.run(wifi.restore(ssid))
    click.echo(f"Restored Wi-Fi network: {ssid}")
