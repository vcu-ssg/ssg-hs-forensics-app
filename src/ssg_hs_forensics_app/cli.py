import click

@click.command()
def cli():
    """Simple Hello World CLI."""
    click.echo("Hello, world!")
