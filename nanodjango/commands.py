import shutil
import sys
from importlib import import_module
from importlib.machinery import SourceFileLoader
from pathlib import Path

import click

from .app import Django
from .hookspecs import get_contrib_plugins


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
    if script_name.endswith(".py"):
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

    # This would get picked up by app.instance_name, but we have it already
    app._instance_name = app_name
    return app


@click.group()
@click.option(
    "--plugin",
    "-p",
    multiple=True,
    help="Plugin path - either a filesystem path or a Python module",
)
def cli(plugin: list[str]):
    # Load plugins
    for index, plugin_path in enumerate(plugin):
        if plugin_path.endswith(".py"):
            plugin_name = Path(plugin_path).stem
            module = load_module(
                f"nanodjango.contrib.runtime_{index}_{plugin_name}", plugin_path
            )
        else:
            module = import_module(plugin_path)
        Django._plugins.append(module)


@cli.command(
    context_settings={"allow_extra_args": True, "allow_interspersed_args": False}
)
@click.argument("app", type=str, required=True, callback=load_app)
@click.pass_context
def manage(ctx: click.Context, app: Django):
    """
    Run a management command
    """
    app.manage(tuple(ctx.args))


@cli.command()
@click.argument("app", type=str, required=True, callback=load_app)
@click.argument("host", type=str, required=False, default="")
@click.option(
    "--username",
    "--user",
    is_flag=False,
    flag_value="",
    default=None,
    help="Username for superuser creation (prompts if flag used without value)",
)
@click.option(
    "--password",
    "--pass",
    is_flag=False,
    flag_value="",
    default=None,
    help="Password for superuser creation (prompts if flag used without value)",
)
def run(app: Django, host: str, username: str | None, password: str | None):
    """
    Start the app in development mode on the specified IP and port
    """
    app.run(host, username=username, password=password)


@cli.command()
@click.argument("app", type=str, required=True, callback=load_app)
@click.argument("host", type=str, required=False, default="")
@click.option(
    "--username",
    "--user",
    is_flag=False,
    flag_value="",
    default=None,
    help="Username for superuser creation (prompts if flag used without value)",
)
@click.option(
    "--password",
    "--pass",
    is_flag=False,
    flag_value="",
    default=None,
    help="Password for superuser creation (prompts if flag used without value)",
)
def serve(app: Django, host: str, username: str | None, password: str | None):
    """
    Serve the app in production mode on the specified IP and port
    """
    app.serve(host, username=username, password=password)


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
@click.option(
    "--template",
    "-t",
    help="Path or URL to a custom Django project template",
)
def convert(app: Django, path: click.Path, name: str, can_delete: bool, template: str):
    """
    Convert the app into a full Django site
    """
    # Clear out target path
    target_path: Path = Path(str(path)).resolve()
    if can_delete and target_path.exists():
        shutil.rmtree(str(target_path))

    app.convert(target_path, name, template=template)


@cli.command()
def plugins():
    """
    List installed plugins
    """
    import importlib.metadata

    click.echo("Active nanodjango plugins:")

    entry_points = importlib.metadata.entry_points()
    count = 0

    for contrib_module in get_contrib_plugins():
        click.echo(f"  {contrib_module}")
        count += 1

    for entry_point in entry_points:
        if entry_point.group == "nanodjango":
            click.echo(f"  {entry_point.name}")
            count += 1

    if count == 0:
        click.echo("None")


def invoke():
    cli(obj={})
