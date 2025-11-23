# src/ssg_hs_forensics_app/cli/_main.py

import click
from ssg_hs_forensics_app.core.config import get_config

from .cmd_generate import cmd_generate
from .cmd_show import cmd_show
from .cmd_config import cmd_config
from .cmd_list import cmd_list
from .cmd_images import cmd_images
from .cmd_models import cmd_models


@click.group()
@click.pass_context
def cli(ctx):
    """sammy — SAM image processing toolkit."""

    # Ensure context object exists
    ctx.ensure_object(dict)

    # Load unified configuration (cached)
    ctx.obj["config"] = get_config()


# Attach subcommands
cli.add_command(cmd_generate)
cli.add_command(cmd_show)
cli.add_command(cmd_config)
cli.add_command(cmd_list)
cli.add_command(cmd_images)
cli.add_command(cmd_models)