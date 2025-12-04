import click

from .cmd_generate import cmd_generate
from .cmd_show import cmd_show
from .cmd_config import cmd_config
from .cmd_list import cmd_list
from .cmd_microscope import cmd_microscope

@click.group()
def cli():
    """sammy — SAM image processing toolkit."""
    pass

# Attach subcommands
cli.add_command(cmd_generate)
cli.add_command(cmd_show)
cli.add_command(cmd_config)
cli.add_command(cmd_list)
cli.add_command(cmd_microscope)