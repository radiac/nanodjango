import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

import click


@click.group()
@click.argument("app", type=Path, required=True)
@click.pass_context
def cli(ctx, app):
    # Import the script
    app = app.absolute()
    sys.path.append(str(app.parent))
    module = SourceFileLoader(app.stem, str(app)).load_module()
    ctx.obj["app"] = getattr(module, "app")


@cli.command()
@click.argument("args", type=str, required=False, nargs=-1)
@click.pass_context
def run(ctx, args: tuple[str]):
    ctx.obj["app"].run(args)


@cli.command()
@click.argument("args", type=str, required=False, nargs=-1)
@click.pass_context
def upgrade(ctx, args: tuple[str]):
    raise click.ClickException(
        "The upgrade is not yet implemented - contributions welcome"
    )


def invoke():
    cli(obj={})
