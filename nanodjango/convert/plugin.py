"""
Converter plugin management
"""

from __future__ import annotations

import importlib.metadata
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    import ast

    from .converter import Converter, Resolver


class BaseConverterPlugin:
    def init(self, converter: Converter):
        """
        The source file has been parsed, plugins have been loaded, and the conversion
        process is about to start.

        Args:
            converter (Converter): The current converter instance.
        """

    def build_start(self, converter: Converter):
        """
        The new project and app are about to be built.

        Args:
            converter (Converter): The current converter instance.
        """

    def collect_imports(self, converter: Converter):
        """
        Imported symbols have been collected into ``self.imports``.

        Args:
            converter (Converter): The current converter instance.
        """

    def build_project_done(self, converter: Converter):
        """
        The project directory has been created, the settings are about to be modified.

        Args:
            converter (Converter): The current converter instance.
        """

    def build_settings(
        self, converter: Converter, resolver: Resolver, settings_ast: ast.AST
    ) -> tuple[Resolver, ast.AST]:
        """
        Modify the settings AST.

        Args:
            converter (Converter): The current converter instance.
            resolver (Resolver): The current resolver instance for
                ``project/settings.py``.
            settings_ast (ast.AST): The abstract syntax tree for the settings file.
        """
        return resolver, settings_ast

    def build_settings_done(self, converter: Converter):
        """
        The ``project/settings.py`` file has been updated and the assets are about to be
        copied.

        Args:
            converter (Converter): The current converter instance.
        """

    def copy_assets(self, converter: Converter):
        """
        Copy additional assets into the project.

        Args:
            converter (Converter): The current converter instance.
        """

    def build_app_models(
        self, converter: Converter, resolver: Resolver, extra_src: list[str]
    ) -> tuple[Resolver, list[str]]:
        """
        Extend ``app/models.py``.

        Models have been collected on ``converter.models`` (wrapped in ``AppModel``
        instances) and are about to be written into ``app/models.py``.

        Args:
            converter (Converter): The current converter instance.
            resolver (Resolver): The current resolver instance for ``app/models.py``.
            extra_src (list[str]): Lines of Python code to insert at the end.

        Returns:
            resolver (Resolver): The current resolver instance.
            extra_src (list[str]): Lines of Python code to insert at the end.
        """
        return resolver, extra_src

    def build_app_models_done(self, converter: Converter):
        """
        The ``app/models.py`` has been written, the views are about to be built.

        Args:
            converter (Converter): The current converter instance.
        """

    def build_app_views(
        self, converter: Converter, resolver: Resolver, extra_src: list[str]
    ) -> tuple[Resolver, list[str]]:
        """
        Extend ``app/views.py``.

        Views have been collected on ``converter.views`` (wrapped in ``AppView``
        instances) and are about to be written into ``app/views.py``.

        Args:
            converter (Converter): The current converter instance.
            resolver (Resolver): The current resolver instance for ``app/views.py``.
            extra_src (list[str]): Lines of Python code to insert at the end.

        Returns:
            resolver (Resolver): The current resolver instance.
            extra_src (list[str]): Lines of Python code to insert at the end.
        """
        return resolver, extra_src

    def build_app_views_done(self, converter: Converter):
        """
        The ``app/views.py`` has been written, the app urls are about to be built.

        Args:
            converter (Converter): The current converter instance.
        """

    def build_app_api(
        self,
        converter: Converter,
        resolver: Resolver,
        extra_src: list[str],
    ) -> tuple[Resolver, list[str]]:
        """
        Extend ``app/api.py``

        API endpoints have been collected on ``converter.api_views`` (wrapped in
        ``AppAPIView`` instances) and are about to be written into ``app/api.py``

        Args:
            converter (Converter): The current converter instance.
            resolver (Resolver): The current resolver instance for ``app/admin.py``.
            admins (list[str]): Lines of Python code for model admin definitions.
            extra_src (list[str]): Lines of Python code to insert at the end.

        Returns:
            resolver (Resolver): The current resolver instance.
            admins (list[str]): Lines of Python code for model admin definitions.
            extra_src (list[str]): Lines of Python code to insert at the end.
        """
        return resolver, extra_src

    def build_app_api_done(self, converter: Converter):
        """
        The ``app/api.py`` has been written (or not if there were no APIs defined), and
        the unused objects are about to be built.

        Args:
            converter (Converter): The current converter instance.
        """

    def build_app_urls(
        self,
        converter: Converter,
        resolver: Resolver,
        urls: list[str],
        extra_src: list[str],
    ) -> tuple[Resolver, list[str], list[str]]:
        """
        Extend app/urls.py

        Urls have been collected and passed into this hook as ``urls``.

        Args:
            converter (Converter): The current converter instance.
            resolver (Resolver): The current resolver instance for ``app/urls.py``.
            urls (list[str]): Lines of Python to insert into ``urlpatterns = [...]``
            extra_src (list[str]): Lines of Python code to insert at the end.

        Returns:
            resolver (Resolver): The current resolver instance.
            urls (list[str]): Lines of Python to insert into ``urlpatterns = [...]``
            extra_src (list[str]): Lines of Python code to insert at the end.
        """
        return resolver, urls, extra_src

    def build_app_urls_done(self, converter: Converter):
        """
        The ``app/urls.py`` has been written, the project urls are about to be built.

        Args:
            converter (Converter): The current converter instance.
        """

    def build_urls(self, converter: Converter, src: str) -> str:
        """
        Modify ``project/urls.py``

        The ``project/urls.py`` has been loaded into ``src``, and the app's urls (if
        present) and admin URL have been updated. This hook can modify the source
        further, returning the full string to be written out to the file.

        Args:
            converter (Converter): The current converter instance. src (str): The Python
            code for ``project/urls.py``

        Returns:
            src (str): The Python code
        """
        return src

    def build_urls_done(self, converter: Converter):
        """
        The ``project/urls.py`` has been written, the app admin is about to be built.

        Args:
            converter (Converter): The current converter instance.
        """

    def build_app_admin(
        self,
        converter: Converter,
        resolver: Resolver,
        admins: list[str],
        extra_src: list[str],
    ) -> tuple[Resolver, list[str], list[str]]:
        """
        Extend ``app/admin.py``

        ModelAdmin definitions have been built into ``admins``. This hook can modify
        this list, or add some extra lines of source code to add to the end of the file.

        Args:
            converter (Converter): The current converter instance. resolver (Resolver):
            The current resolver instance for ``app/admin.py``. admins (list[str]):
            Lines of Python code for model admin definitions. extra_src (list[str]):
            Lines of Python code to insert at the end.

        Returns:
            resolver (Resolver): The current resolver instance. admins (list[str]):
            Lines of Python code for model admin definitions. extra_src (list[str]):
            Lines of Python code to insert at the end.
        """
        return resolver, admins, extra_src

    def build_app_admin_done(self, converter: Converter):
        """
        The ``app/admin.py`` has been written, the unused code is about to be written
        out.

        Args:
            converter (Converter): The current converter instance.
        """

    def build_app_unused(
        self,
        converter: Converter,
        resolver: Resolver,
        extra_src: list[str],
    ) -> tuple[Resolver, list[str]]:
        """
        Extend ``app/unused.py``

        All active files have been built, any leftover code is about to be written into
        ``app/unused.py``.

        It is better to collect important code before this function.

        Args:
            converter (Converter): The current converter instance.
            resolver (Resolver): The current resolver instance for ``app/unused.py``.
            extra_src (list[str]): Lines of Python code to insert at the end.

        Returns:
            resolver (Resolver): The current resolver instance.
            extra_src (list[str]): Lines of Python code to insert at the end.
        """
        return resolver, extra_src

    def build_end(self, converter: Converter):
        """
        The build process is complete.

        Args:
            converter (Converter): The current converter instance.
        """


class Manager:
    # Entrypoint group
    entrypoint = "nanodjango"

    def __init__(self):
        self.plugins = []

    def load(self):
        """
        Load plugins
        """
        # Load by contrib
        from . import contrib  # noqa

        # Load by entrypoint
        for dist in importlib.metadata.distributions():
            for entry_point in dist.entry_points:
                if entry_point.group != self.entrypoint:
                    continue

                # Import the module - any plugins will auto-register
                entry_point.load()

    def register(self, cls):
        self.plugins.append(cls)

    def __getattribute__(self, name):
        """
        Pass hook calls to the manager through to the plugins
        """

        def call(converter, *args) -> Any:
            is_single_arg = False
            returned = args
            if len(args) == 1:
                is_single_arg = True
                returned = args[0]

            for plugin in self.plugins:
                fn = getattr(plugin, name)
                returned = fn(plugin, converter, *args)
                # TODO: Add type checking to safeguard plugin return values
                if returned is None:
                    pass
                elif is_single_arg:
                    args = (returned,)
                else:
                    args = returned

            return returned

        if name in BaseConverterPlugin.__dict__:
            return call

        return super().__getattribute__(name)


plugins = Manager()


# We need to define the ConverterPlugin after the manager, as it needs to auto-register.
# But the manager needs the ConverterPlugin to be defined before, as it introspects it
# We therefore introspect the BaseConverterPlugin, and add auto-registration afterwards
class ConverterPlugin(BaseConverterPlugin):
    def __init_subclass__(cls) -> None:
        plugins.register(cls)
