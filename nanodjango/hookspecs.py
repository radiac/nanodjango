from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

import pluggy

if TYPE_CHECKING:
    import ast

    from .app import Django
    from .convert import Converter
    from .convert.converter import Resolver

hookspec = pluggy.HookspecMarker("nanodjango")


def get_contrib_plugins() -> list[str]:
    """
    Return the list of module paths for contrib plugin modules
    """
    module_paths = []
    contrib_dir = Path(__file__).resolve().parent / "contrib"
    for plugin_file in contrib_dir.glob("*.py"):
        if plugin_file.name != "__init__.py":
            # Convert filename to module path
            module_name = plugin_file.stem
            module_path = f"nanodjango.contrib.{module_name}"
            module_paths.append(module_path)
    return module_paths


@hookspec
def django_pre_setup(app: Django):
    """
    Django's setup is about to be called

    Args:
        app (Django): The nanodjango app instance
    """


@hookspec
def django_post_setup(app: Django):
    """
    Django's setup has been called

    Args:
        app (Django): The nanodjango app instance
    """


@hookspec(firstresult=True)
def django_route_path_fn(
    app: Django, pattern: str, include, re: bool, kwargs: dict
) -> Callable | None:
    """
    Override the path function used for routing

    If this plugin adds extra kwargs to route(), it must pop them here. Unpopped kwargs
    will raise an exception.

    Args:
        app (Django): The nanodjango app instance
        pattern (str): the route pattern
        include: the include value
        re (bool): if this is a regex or plain pattern
        kwargs (dict): dict of keyword args passed to route()

    Returns:
        Callable: The path function
    """
    # For now we only accept one plugin returning a value for this hook.
    #
    # It's unclear what would need to happen if we ever need multiple plugins to modify
    # this - so we'll look at it if it's ever an issue.


@hookspec
def django_route_path_kwargs(
    app,
    pattern: str,
    include,
    re: bool,
    kwargs: dict,
):
    """
    Override the kwargs used to initialise the path function
    """


@hookspec
def convert_init(converter: Converter):
    """
    The source file has been parsed, plugins have been loaded, and the conversion
    process is about to start.

    Args:
        converter (Converter): The current converter instance.
    """


@hookspec
def convert_build_start(converter: Converter):
    """
    The new project and app are about to be built.

    Args:
        converter (Converter): The current converter instance.
    """


@hookspec
def convert_collect_imports(converter: Converter):
    """
    Imported symbols have been collected into ``converter.imports``.

    Args:
        converter (Converter): The current converter instance.
    """


@hookspec
def convert_build_project_done(converter: Converter):
    """
    The project directory has been created, the settings are about to be modified.

    Args:
        converter (Converter): The current converter instance.
    """


@hookspec
def convert_build_settings(
    converter: Converter, resolver: Resolver, settings_ast: ast.AST
):
    """
    Modify the settings AST.

    Args:
        converter (Converter): The current converter instance.
        resolver (Resolver): The current resolver instance for
            ``project/settings.py``.
        settings_ast (ast.AST): The abstract syntax tree for the settings file.
    """


@hookspec
def convert_build_settings_done(converter: Converter):
    """
    The ``project/settings.py`` file has been updated and the assets are about to be
    copied.

    Args:
        converter (Converter): The current converter instance.
    """


@hookspec
def convert_copy_assets(converter: Converter):
    """
    Copy additional assets into the project.

    Args:
        converter (Converter): The current converter instance.
    """


@hookspec
def convert_build_app_templates(converter: Converter):
    """
    Build templates from the app.templates dict.

    Args:
        converter (Converter): The current converter instance.
    """


@hookspec
def convert_build_app_models(
    converter: Converter, resolver: Resolver, extra_src: list[str]
):
    """
    Extend ``app/models.py``.

    Models have been collected on ``converter.models`` (wrapped in ``AppModel``
    instances) and are about to be written into ``app/models.py``.

    Args:
        converter (Converter): The current converter instance.
        resolver (Resolver): The current resolver instance for ``app/models.py``.
        extra_src (list[str]): Lines of Python code to insert at the end.
    """


@hookspec
def convert_build_app_models_done(converter: Converter):
    """
    The ``app/models.py`` has been written, the views are about to be built.

    Args:
        converter (Converter): The current converter instance.
    """


@hookspec
def convert_build_app_views(
    converter: Converter, resolver: Resolver, extra_src: list[str]
):
    """
    Extend ``app/views.py``.

    Views have been collected on ``converter.views`` (wrapped in ``AppView``
    instances) and are about to be written into ``app/views.py``.

    Args:
        converter (Converter): The current converter instance.
        resolver (Resolver): The current resolver instance for ``app/views.py``.
        extra_src (list[str]): Lines of Python code to insert at the end.
    """


@hookspec
def convert_build_app_views_done(converter: Converter):
    """
    The ``app/views.py`` has been written, the app urls are about to be built.

    Args:
        converter (Converter): The current converter instance.
    """


@hookspec
def convert_build_app_api(
    converter: Converter,
    resolver: Resolver,
    extra_src: list[str],
):
    """
    Extend ``app/api.py``

    API endpoints have been collected on ``converter.api_views`` (wrapped in
    ``AppAPIView`` instances) and are about to be written into ``app/api.py``

    Args:
        converter (Converter): The current converter instance.
        resolver (Resolver): The current resolver instance for ``app/admin.py``.
        extra_src (list[str]): Lines of Python code to insert at the end.

    Returns:
        resolver (Resolver): The current resolver instance.
        extra_src (list[str]): Lines of Python code to insert at the end.
    """


@hookspec
def convert_build_app_api_done(converter: Converter):
    """
    The ``app/api.py`` has been written (or not if there were no APIs defined), and
    the unused objects are about to be built.

    Args:
        converter (Converter): The current converter instance.
    """


@hookspec
def convert_build_app_urls(
    converter: Converter,
    resolver: Resolver,
    urls: list[str],
    extra_src: list[str],
):
    """
    Extend app/urls.py

    Urls have been collected and passed into this hook as ``urls``.

    Args:
        converter (Converter): The current converter instance.
        resolver (Resolver): The current resolver instance for ``app/urls.py``.
        urls (list[str]): Lines of Python to insert into ``urlpatterns = [...]``
        extra_src (list[str]): Lines of Python code to insert at the end.
    """


@hookspec
def convert_build_app_urls_done(converter: Converter):
    """
    The ``app/urls.py`` has been written, the project urls are about to be built.

    Args:
        converter (Converter): The current converter instance.
    """


@hookspec
def convert_build_urls(converter: Converter, src: list[str]):
    """
    Modify ``project/urls.py``

    The ``project/urls.py`` has been loaded into ``src``, and the app's urls (if
    present) and admin URL have been updated. This hook can modify the source
    further, returning the full string to be written out to the file.

    Args:
        converter (Converter): The current converter instance.
        src (list[str]): The lines of Python code for ``project/urls.py``
    """


@hookspec
def convert_build_urls_done(converter: Converter):
    """
    The ``project/urls.py`` has been written, the app admin is about to be built.

    Args:
        converter (Converter): The current converter instance.
    """


@hookspec
def convert_build_app_admin(
    converter: Converter,
    resolver: Resolver,
    admins: list[str],
    extra_src: list[str],
):
    """
    Extend ``app/admin.py``

    ModelAdmin definitions have been built into ``admins``. This hook can modify
    this list, or add some extra lines of source code to add to the end of the file.

    Args:
        converter (Converter): The current converter instance. resolver (Resolver):
        The current resolver instance for ``app/admin.py``. admins (list[str]):
        Lines of Python code for model admin definitions. extra_src (list[str]):
        Lines of Python code to insert at the end.
    """
    return resolver, admins, extra_src


@hookspec
def convert_build_app_admin_done(converter: Converter):
    """
    The ``app/admin.py`` has been written, the unused code is about to be written
    out.

    Args:
        converter (Converter): The current converter instance.
    """


@hookspec
def convert_build_app_unused(
    converter: Converter,
    resolver: Resolver,
    extra_src: list[str],
):
    """
    Extend ``app/unused.py``

    All active files have been built, any leftover code is about to be written into
    ``app/unused.py``.

    It is better to collect important code before this function.

    Args:
        converter (Converter): The current converter instance.
        resolver (Resolver): The current resolver instance for ``app/unused.py``.
        extra_src (list[str]): Lines of Python code to insert at the end.
    """


@hookspec
def convert_build_end(converter: Converter):
    """
    The build process is complete.

    Args:
        converter (Converter): The current converter instance.
    """
