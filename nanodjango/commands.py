import shutil
import sys
from importlib import import_module
from importlib.machinery import SourceFileLoader
from pathlib import Path

import click

from .app import Django
from .hookspecs import get_contrib_plugins
from .play import Api, ApiError


def load_module(module_name: str, path: str | Path):
    module = SourceFileLoader(module_name, str(path)).load_module()
    return module


def load_app(ctx: click.Context, param: str, value: str) -> Django:
    # Called from Django.invoke(), which has already loaded the app
    root_obj = ctx.find_root().obj or {}
    if "app" in root_obj:
        return root_obj["app"]

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


@click.group()
def play() -> None:
    """
    nanodjango.dev playground
    """


@play.command("login")
def play_login() -> None:
    """
    Log in to the nanodjango playground
    """
    api = Api()
    if api.is_authenticated:
        click.echo(
            f"Already logged in as {api.username}."
            " Use 'play logout' first to switch accounts."
        )
        return
    try:
        api.login()
    except ApiError as e:
        raise click.ClickException(str(e))


@play.command("logout")
def play_logout() -> None:
    """
    Log out from the nanodjango playground
    """
    api = Api()
    try:
        api.logout()
    except ApiError as e:
        raise click.ClickException(str(e))
    click.echo("Logged out.")


@play.command("share")
@click.argument("source", type=click.Path(exists=True))
@click.option("--name", default=None, help="Script name (default: filename stem)")
@click.option("--title", default=None, help="Title shown on playground (default: name)")
@click.option("--description", default="", help="Short description")
@click.option(
    "--requirements",
    "-r",
    default=None,
    type=click.Path(),
    help="Requirements file (requirements.txt)",
)
@click.option(
    "--package",
    multiple=True,
    help="Package to add to requirements (repeatable)",
)
@click.option(
    "--env",
    multiple=True,
    help="Env var declaration: VARNAME or VARNAME:Description (repeatable)",
)
@click.option(
    "--force", is_flag=True, default=False, help="Overwrite if script already exists"
)
def play_share(
    source: str,
    name: str | None,
    title: str | None,
    description: str,
    requirements: str | None,
    package: tuple[str, ...],
    env: tuple[str, ...],
    force: bool,
) -> None:
    """
    Share a script on the nanodjango playground
    """
    api = Api()

    source_path = Path(source)
    if name is None:
        name = source_path.stem
    if title is None:
        title = name

    code = source_path.read_text()

    # Build packages list (newline-separated)
    pkg_lines = []
    if requirements is not None:
        req_path = Path(requirements)
        if not req_path.exists():
            raise click.ClickException(f"Requirements file not found: {requirements}")
        pkg_lines.append(req_path.read_text().rstrip())
    pkg_lines.extend(package)
    packages = "\n".join(pkg_lines)

    # Build environment as JSON dict {var_name: description_or_null}
    environment = {}
    for entry in env:
        if ":" in entry:
            varname, desc = entry.split(":", 1)
            environment[varname.strip()] = desc.strip()
        else:
            environment[entry.strip()] = None

    try:
        url = api.push(
            name,
            code,
            title=title,
            description=description,
            packages=packages,
            environment=environment,
            force=force,
        )
        click.echo(f"Shared at {url}")
    except ApiError as e:
        raise click.ClickException(str(e))


@play.command("pull")
@click.argument("script")
@click.argument("target", required=False, default=None)
@click.option(
    "--force", is_flag=True, default=False, help="Overwrite target if it exists"
)
def play_pull(script: str, target: str | None, force: bool) -> None:
    """
    Pull a script from the nanodjango playground
    """
    api = Api()

    if "/" in script:
        user, name = script.split("/", 1)
    else:
        user, name = None, script

    target_path = Path(target) if target else Path(f"{name}.py")
    if target_path.exists() and not force:
        raise click.ClickException(
            f"{target_path} already exists. Use --force to overwrite."
        )

    try:
        code = api.pull(name, user=user)
    except ApiError as e:
        raise click.ClickException(str(e))

    target_path.write_text(code)
    click.echo(f"Saved to {target_path}")


@play.command("list")
@click.argument("user", required=False, default=None)
def play_list(user: str | None) -> None:
    """
    List scripts on the nanodjango playground
    """
    api = Api()

    try:
        scripts = api.list(user=user)
        display_user = user or api.username
    except ApiError as e:
        raise click.ClickException(str(e))
    if not scripts:
        click.echo(f"No scripts found for {display_user}.")
        return

    col_name = max(max(len(s.get("name", "")) for s in scripts), 4)
    col_title = max(max(len(s.get("title", "")) for s in scripts), 5)
    col_vis = 10

    header = f"{'NAME':<{col_name}}  {'TITLE':<{col_title}}  {'VISIBILITY':<{col_vis}}  MODIFIED"
    click.echo(header)
    click.echo("-" * len(header))
    for s in scripts:
        name = s.get("name", "")
        title = s.get("title", "")
        visibility = s.get("visibility", s.get("public", ""))
        if isinstance(visibility, bool):
            visibility = "public" if visibility else "private"
        modified = s.get("modified", s.get("updated_at", ""))[:19]
        click.echo(
            f"{name:<{col_name}}  {title:<{col_title}}  {visibility:<{col_vis}}  {modified}"
        )


@play.command("ls")
@click.argument("user", required=False, default=None)
@click.pass_context
def play_ls(ctx: click.Context, user: str | None) -> None:
    """
    List scripts on the nanodjango playground (alias for 'list')
    """
    ctx.invoke(play_list, user=user)


# Register play group and top-level aliases
cli.add_command(play)
cli.add_command(play_share, "share")
cli.add_command(play_pull, "pull")


def invoke():
    cli(obj={})
