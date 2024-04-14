import os
import shutil
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

import click


def load_app(path: str | Path):
    app = Path(path).absolute()
    sys.path.append(str(app.parent))
    module = SourceFileLoader(app.stem, str(app)).load_module()
    return getattr(module, "app")


@click.group()
@click.argument("app", type=Path, required=True)
@click.pass_context
def cli(ctx, app):
    # Import the script
    app = load_app(app)
    ctx.obj["app"] = app


@cli.command()
@click.argument("args", type=str, required=False, nargs=-1)
@click.pass_context
def run(ctx, args: tuple[str]):
    ctx.obj["app"].run(args)


@cli.command()
@click.argument("path", type=click.Path(), required=True)
@click.option("--name", default="project", help="The project name")
@click.option(
    "--delete",
    "can_delete",
    is_flag=True,
    help="If the target path is not empty, delete it before proceeding",
)
@click.pass_context
def convert(ctx, path: click.Path, name: str, can_delete: bool = False):
    path: Path = Path(str(path)).resolve()
    if can_delete and path.exists():
        shutil.rmtree(str(path))

    ctx.obj["app"].convert(path, name)


def invoke():
    cli(obj={})
