import shutil
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

import click


def load_module(module_name: str, path: str | Path):
    module = SourceFileLoader(module_name, str(path)).load_module()
    return module


def load_app(path: str | Path):
    path = Path(path).absolute()
    sys.path.append(str(path.parent))
    module = load_module(path.stem, path)
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
@click.option("--name", "-n", default="project", help="The project name")
@click.option(
    "--delete",
    "can_delete",
    is_flag=True,
    default=False,
    help="If the target path is not empty, delete it before proceeding",
)
@click.option("--plugin", "-p", multiple=True, help="Converter plugins to load")
@click.pass_context
def convert(ctx, path: click.Path, name: str, can_delete: bool, plugin: list[str]):
    # Load plugins
    for index, plugin_path in enumerate(plugin):
        plugin_name = Path(plugin_path).stem
        load_module(
            f"nanodjango.convert.contrib.runtime_{index}_{plugin_name}", plugin_path
        )

    # Clear out target path
    target_path: Path = Path(str(path)).resolve()
    if can_delete and target_path.exists():
        shutil.rmtree(str(target_path))

    ctx.obj["app"].convert(target_path, name)


def invoke():
    cli(obj={})
