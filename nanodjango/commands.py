import shutil
import sys
from importlib import import_module
from importlib.machinery import SourceFileLoader
from pathlib import Path

import click

from .app import Django


def load_module(module_name: str, path: str | Path):
    module = SourceFileLoader(module_name, str(path)).load_module()
    return module


def load_app(ctx: click.Context, param: str, value: str) -> Django:
    path = Path(value).absolute()

    # Look for the app name
    script_name = path.name
    app_name = None
    if ":" in str(script_name):
        script_name, app_name = script_name.split(":", 1)
        path = path.parent / script_name

    # Find the app module
    if "." in script_name:
        if path.exists():
            sys.path.append(str(path.parent))
            module = load_module(path.stem, path)
        else:
            raise click.UsageError(f"App {value} is not a file or module")
    else:
        try:
            module = import_module(script_name)
        except ModuleNotFoundError:
            raise click.UsageError(f"App {value} is not a file or module")

    # Find the Django instance to use - first try the app name provided
    if app_name and (app := getattr(module, app_name, None)):
        if isinstance(app, Django):
            return app
        else:
            raise click.UsageError(f"App {app_name} is not a Django instance")

    # None provided, find it
    app = None
    for var, val in module.__dict__.items():
        if isinstance(val, Django):
            app_name = var
            app = val
            break

    if app_name is None or app is None:
        raise click.UsageError(f"App {value} has no Django instances")

    app._instance_name = app_name
    return app


@click.group()
def cli():
    pass


@cli.command()
@click.argument("app", type=str, required=True, callback=load_app)
@click.argument("args", type=str, required=False, nargs=-1)
def run(app: Django, args: tuple[str]):
    """
    Run a management command.

    If no command is specified, it will run runserver 0:8000
    """
    app.run(args)


@cli.command()
@click.argument("app", type=str, required=True, callback=load_app)
@click.argument("host", type=str, required=False, default="")
def start(app: Django, host: str):
    """
    Start the app on the specified IP and port

    This will perform a series of setup commands:

        makemigrations <app>
        migrate
        createsuperuser
        runserver HOST
    """
    app.start(host)


@cli.command()
@click.argument("app", type=str, required=True, callback=load_app)
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
def convert(
    app: Django, path: click.Path, name: str, can_delete: bool, plugin: list[str]
):
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

    app.convert(target_path, name)


def invoke():
    cli(obj={})
