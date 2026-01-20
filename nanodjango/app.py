from __future__ import annotations

import ast
import importlib
import inspect
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, Mapping, Sequence

import pluggy
from django import setup
from django import urls as django_urls
from django.db.models import Model
from django.shortcuts import render
from django.template import engines
from django.views import View

from . import app_meta, hookspecs
from .defer import defer
from .exceptions import ConfigurationError, UsageError
from .templatetags import TemplateTagLibrary
from .urls import urlpatterns
from .views import string_view

if TYPE_CHECKING:
    from pathlib import Path

    from django.http import HttpRequest, HttpResponse
    from ninja import NinjaAPI


def exec_manage(*args):
    from django.core.management import execute_from_command_line

    args = ["nanodjango"] + list(args)
    execute_from_command_line(args)


class Django:
    """
    The main Django app

    This class manages the single-file Django application lifecycle,
    from initial configuration through to serving requests.

    Only one ``Django()`` instance is allowed per script. Creating a second
    instance will raise a ``ConfigurationError``.

    Example::

        from nanodjango import Django

        app = Django(SECRET_KEY="my-secret", ALLOWED_HOSTS=["*"])

        @app.route("/")
        def index(request):
            return "Hello World"
    """

    # Class attribute: list of plugin modules to load - set by click
    _plugins = []

    # Class variable to ensure there can be only one
    _instantiated = False

    #: Name of the app script, eg counter.py has app_name == "counter"
    app_name: str

    #: Cached name of this app instance - see self.instance_name
    _instance_name: str | None = None

    #: Reference to the app script's module
    app_module: ModuleType

    #: Path of app script
    app_path: Path

    #: Whether this app has defined an @app.admin
    has_admin: bool = False

    #: In-memory template store - access via app.templates
    _templates: dict[str, str]

    #: Whether this app has any async views
    _has_async_view: bool = False

    # Settings cache to aid ``convert``
    _settings: dict[str, Any]

    # URL cache to aid ``convert``
    # {pattern:
    _routes: dict[str, tuple[Callable | None, dict[str, Any]]]

    # NinjaAPI instance for @app.api
    _api: NinjaAPI | None = None

    # Template tag library for @app.templatetag
    _templatetag: TemplateTagLibrary | None = None

    def __new__(cls, *args, **kwargs):
        # Enforce only one Django() per script, otherwise everything will get confused
        if cls._instantiated:
            raise ConfigurationError("An app can only have one Django() instance")
        cls._instantiated = True

        instance = super().__new__(cls)

        # Set app meta
        app_name = inspect.stack()[1].frame.f_globals["__name__"]
        app_meta._app_module = sys.modules[app_name]
        return instance

    def __init__(self, **_settings):
        """
        Initialise a new Django app, optionally with settings

        Usage::

            app = Django()
            app = Django(SECRET_KEY="some-secret", ALLOWED_HOSTS=["my.example.com"])
        """
        self._init_plugin_manager()

        self.has_admin = False
        self._settings = {}
        self._routes = {}
        self._config(_settings)
        self._prepared = False

    def _init_plugin_manager(self):
        self.pm = pluggy.PluginManager("nanodjango")
        self.pm.add_hookspecs(hookspecs)

        # Load installed modules which register with our entrypoint
        self.pm.load_setuptools_entrypoints("nanodjango")

        # Load contrib plugins we provide
        for module_path in hookspecs.get_contrib_plugins():
            module = importlib.import_module(module_path)
            self.pm.register(module)

        # Load plugins from the command line
        for plugin in self._plugins:
            self.pm.register(plugin)

    def _config(self, _settings):
        """
        Configure settings and patch Django ready for model definitions
        """
        self._settings = app_meta._app_conf = _settings

        # Settings
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nanodjango.settings")
        from django.conf import settings

        self.settings = settings

        # Update Django settings with ours
        for key, value in _settings.items():
            setattr(settings, key, value)

        # Set WHITENOISE_ROOT if public dir exists
        # Do it this way instead of setting WHITENOISE_ROOT directly, because if the dir
        # does not exist, Whitenoise will raise warnings when run in production
        if not getattr(settings, "WHITENOISE_ROOT", None):
            public_dir = settings.PUBLIC_DIR
            if public_dir.is_dir():
                settings.WHITENOISE_ROOT = settings.PUBLIC_DIR

        # Collect internal values
        self.app_name = settings.ND_APP_NAME
        self.app_module = app_meta.get_app_module()
        sys.modules[self.app_name] = self.app_module
        self.app_path = Path(inspect.getfile(self.app_module))
        self._templates = app_meta.get_templates()

        # Import and apply glue after django.conf has its settings
        from .django_glue.apps import prepare_apps
        from .django_glue.db import patch_db

        patch_db(self.app_name)
        prepare_apps(self.app_name, self.app_module)

        # Ready for Django's standard setup
        self.pm.hook.django_pre_setup(app=self)
        setup()

        # Import any deferred imports
        defer.apply()
        self.pm.hook.django_post_setup(app=self)

        # Register template tag library with Django's template engine
        self._register_template_library()

    @property
    def instance_name(self):
        """
        Variable name of this instance in the module it's defined in

        If this instance is assigned to multiple names, the first name will be used
        Example:

            foobar = Django
            foobar.instance_name == "foobar"
        """
        if not self._instance_name:
            for var, val in self.app_module.__dict__.items():
                if val == self:
                    self._instance_name = var
                    break

        if not self._instance_name:
            raise UsageError(
                f"Could not find Django instance name in {self.app_module.__name__}"
            )
        return self._instance_name

    def route(
        self,
        pattern: str,
        include=None,
        *,
        re: bool = False,
        name: str | None = None,
        **kwargs,
    ):
        """
        Decorator to add a view to the urls

        The pattern should use the Django path syntax - see
        https://docs.djangoproject.com/en/dev/ref/urls/#path

        Usage::

            # No parameters
            @app.route("/")
            def view(request):
                return "Hello"

            # path() parameters
            @app.route("/<int:pk>/")
            def view(request, pk):
                return f"Hello {pk}"

            # re_path() parameters
            @app.route("/(?P<slug>[a-z])/", re=True)
            def view(request, slug):
                return f"Hello {slug}"

            # Include another urlconf
            # Note this is called as a function, not a decorator
            # If this is a list not an include()
            app.route("/api/", include=api.urls)
            app.route("/api/", api.urls)

        All paths are relative to the root URL, leading slashes will be ignored.
        """
        # We want to support Flask-like patterns which have leading / in its patterns.
        # Django does not use these, so strip them out.
        pattern = pattern.removeprefix("/")

        # Find if it's a path() or re_path()
        unknown_kwargs = kwargs
        path_fn = self.pm.hook.django_route_path_fn(
            app=self, pattern=pattern, include=include, re=re, kwargs=unknown_kwargs
        )
        if unknown_kwargs:
            raise TypeError(
                f"'{list(unknown_kwargs.keys())[0]}' is an invalid keyword argument for route()"
            )
        if path_fn is None:
            path_fn = django_urls.re_path if re else django_urls.path

        if include is not None:
            # Being called directly with an include
            urlpatterns.append(path_fn(pattern, include))

            # If we're converting, we're going to need the source AST node based on the
            # current frame, so we have to capture it now
            # Get the full source code, then fine the expression by line number
            caller_frame = inspect.currentframe().f_back
            caller_lineno = caller_frame.f_lineno
            caller_source_lines, _ = inspect.findsource(caller_frame)
            caller_source = "".join(caller_source_lines)
            caller_ast = ast.parse(caller_source)

            # Find the node corresponding to the line that called the function
            source = None
            for node in ast.walk(caller_ast):
                if isinstance(node, ast.Expr) and node.lineno == caller_lineno:
                    source = node
                    break
                # Handle multiline expressions - check if caller line is within the expression
                elif (
                    isinstance(node, ast.Expr)
                    and hasattr(node, "end_lineno")
                    and node.end_lineno
                    and node.lineno <= caller_lineno <= node.end_lineno
                ):
                    source = node
                    break

            self._routes[pattern] = (
                None,
                {"re": re, "include": True, "source": source},
            )

            # Make sure this isn't being used as a decorator, that wouldn't make sense
            def invalid(fn):
                raise UsageError(
                    "app.route(path, include=urlconf) cannot be used as a decorator"
                )

            return invalid

        def wrapped(fn):
            path_kwargs = {
                "name": name or fn.__name__.lower(),
            }

            extra_kwargs_list = self.pm.hook.django_route_path_kwargs(
                app=self, pattern=pattern, include=include, re=re, kwargs=kwargs
            )
            for extra_kwargs_dict in extra_kwargs_list:
                path_kwargs.update(extra_kwargs_dict)

            # Store route for convert lookup
            self._routes[pattern] = (
                fn,
                {"re": re, "include": False, **path_kwargs},
            )

            # Detect async view
            if inspect.iscoroutinefunction(fn):
                self._has_async_view = True

                # Not ideal that this is changing the global, but it's the only way to
                # work around whatever uvicorn is doing, and you'd have to work hard for
                # it to be a problem.
                type(self).__call__ = type(self).asgi

            # Prepare CBVs
            if inspect.isclass(fn) and issubclass(fn, View):
                fn = fn.as_view()

            # Register URL
            urlpatterns.append(path_fn(pattern, string_view(fn), **path_kwargs))
            return fn

        return wrapped

    def path(
        self,
        pattern: str,
        include=None,
        *,
        name: str | None = None,
        **kwargs,
    ):
        """
        Decorator to add a view using Django path() syntax

        This is equivalent to app.route() with re=False (the default).
        Provided for compatibility with Django's standard URL functions.

        Usage::

            @app.path("")
            def home(request):
                return "Home"

            @app.path("posts/<int:id>/")
            def post_detail(request, id):
                return f"Post {id}"
        """
        return self.route(pattern, include, re=False, name=name, **kwargs)

    def re_path(
        self,
        pattern: str,
        include=None,
        *,
        name: str | None = None,
        **kwargs,
    ):
        """
        Decorator to add a view using Django re_path() regex syntax

        This is equivalent to app.route() with re=True.
        Provided for compatibility with Django's standard URL functions.

        Usage::

            @app.re_path(r"^posts/(?P<year>[0-9]{4})/$")
            def posts_by_year(request, year):
                return f"Posts from {year}"
        """
        return self.route(pattern, include, re=True, name=name, **kwargs)

    def admin(self, model: type[Model] | None = None, **options):
        """
        Decorator to add a model to the admin site

        The admin site must be added using ``settings.ADMIN_URL``.
        """
        self.has_admin = True

        def wrap(model: type[Model]):
            from django.contrib import admin

            admin.site.register(model, **options)
            return model

        if model is None:
            # Called with arguments, @admin(attr=val)
            return wrap

        # Called without arguments, @admin - call wrapped immediately
        return wrap(model)

    @property
    def ninja(self):
        """
        Make django-ninja available without needing to import - work around
        https://github.com/vitalik/django-ninja/issues/1169
        """
        try:
            import ninja
        except ImportError as e:
            raise ImportError(
                "Could not find django-ninja - try: pip install django-ninja"
            ) from e
        return ninja

    @property
    def api(self):
        """
        NinjaAPI instance for django-ninja integration

        Registered paths will be under settings.API_URL, default ``/api/``

        Usage::

            @app.api.get("/path/")
            def view_fn(request):
                ...

            @app.api.get("/async/")
            async def async_view(request):
                ...
        """
        if not self._api:
            api = self.ninja.NinjaAPI()
            self._api = api

        return self._api

    @property
    def templatetag(self):
        """
        Template tag integration
        """
        if not self._templatetag:
            self._templatetag = TemplateTagLibrary(self)

        return self._templatetag

    def _register_template_library(self):
        """
        Register this app's template tag library with Django's template engine
        so {% load app_name %} works
        """
        # Get the default template engine
        django_engines = engines.all()
        if not django_engines:
            return
        engine = django_engines[0]

        # Register our library under the app name
        if engine and hasattr(engine, "engine"):
            # For DjangoTemplates backend
            django_engine = engine.engine
            if hasattr(django_engine, "template_libraries"):
                # Create a fake module that returns our library's register object
                class FakeTemplateTagModule:
                    def __init__(self, library):
                        self.register = library

                # Register under the app name so {% load app_name %} works
                fake_module = FakeTemplateTagModule(self.templatetag.library)
                django_engine.template_libraries[self.app_name] = fake_module.register

    @property
    def templates(self) -> dict[str, str]:
        """
        In-memory template storage.

        Dictionary mapping template names to template content strings.

        Example::

            app.templates = {
                "index.html": "<h1>Hello {{ name }}</h1>",
                "about.html": "<h1>About</h1>"
            }
        """
        return self._templates

    @templates.setter
    def templates(self, data: dict[str, str]):
        # Set or replace the templates dict, maintaining the single object reference
        if self._templates:
            self._templates.clear()
        self._templates.update(data)

    def render(
        self,
        request: HttpRequest,
        template_name: str | Sequence[str],
        context: Mapping[str, Any] | None = None,
        content_type: str | None = None,
        status: int | None = None,
        using: str | None = None,
    ) -> HttpResponse:
        """
        Convenience wrapper for ``django.shortcuts.render`` to save an import
        """
        return render(request, template_name, context, content_type, status, using)

    def _prepare(self, is_prod=False):
        """
        Perform any final setup for this project after it has been imported:

        * detect if it has been run directly; if so, register it as an app
        * register the admin site
        * if in production mode, collectstatic into STATIC_ROOT
        * if in development mode, extend urls to serve media files
        """
        # Check this app hasn't already been prepared
        if self._prepared:
            return

        # Check if this is being called from click commands or directly
        if self.app_name not in sys.modules:
            # Hasn't been run through the ``nanodjango`` command
            if (
                "__main__" not in sys.modules
                or getattr(sys.modules["__main__"], self.instance_name) != self
            ):
                # Doesn't look like it was run directly either
                raise UsageError("App module not initialised")

            # Run directly, so register app module so Django won't try to load it again
            sys.modules[self.app_name] = sys.modules["__main__"]

        # If there are no models in this app, remove it from the migrations
        if not any(
            isinstance(obj, type) and issubclass(obj, Model)
            for obj in self.app_module.__dict__.values()
            if getattr(obj, "__module__", None) == self.app_name
        ):
            from django.conf import settings

            del settings.MIGRATION_MODULES[self.app_name]

        # Register the admin site
        admin_url = self.settings.ADMIN_URL
        if admin_url or self.has_admin:
            from django.contrib import admin

            if admin_url is None:
                admin_url = "admin/"
            if not isinstance(admin_url, str) or not admin_url.endswith("/"):
                raise ConfigurationError(
                    "settings.ADMIN_URL must be a string path ending in /"
                )
            urlpatterns.insert(
                0,
                django_urls.path(admin_url.removeprefix("/"), admin.site.urls),
            )

        # Register the API, if defined
        if self._api:
            self.route(self.settings.API_URL, include=self._api.urls)

        # If running in dev mode, serve media
        if is_prod:
            # Collect static
            exec_manage("collectstatic", "--clear", "--noinput")
        else:
            from django.conf.urls.static import static

            if self.settings.MEDIA_ROOT and Path(self.settings.MEDIA_ROOT).exists():
                urlpatterns.extend(
                    static(
                        self.settings.MEDIA_URL, document_root=self.settings.MEDIA_ROOT
                    )
                )

        self._prepared = True

    @property
    def has_async(self):
        # Check whether any of our views are async
        if self._has_async_view:
            return True

        # Check the Ninja API for any async endpoints
        if self._api:
            for _, router in self._api._routers:
                for view in router.path_operations.values():
                    if view.is_async:
                        return True

        return False

    def manage(self, args: list[str] | tuple[str] | None = None):
        """
        Run Django management commands.

        Args:
            args: Command and arguments to pass to Django's management command

        Example::

            # Run migrations
            app.manage(["migrate"])

            # Create a superuser
            app.manage(["createsuperuser"])

            # Shell
            app.manage(["shell"])
        """
        self._prepare(is_prod=False)
        exec_manage(*(args or []))

    def run(self, host: str | None = None):
        """
        Run the development server.

        This method:

        * Runs migrations (``makemigrations`` and ``migrate``)
        * Prompts to create a superuser if none exists
        * Starts the development server with auto-reload
        * Uses uvicorn for async views, Django's runserver otherwise

        Args:
            host: Host and port in format ``"host:port"`` (default: ``"0:8000"``)

        Example::

            if __name__ == "__main__":
                app.run()

            # Or with custom host
            if __name__ == "__main__":
                app.run("localhost:3000")
        """
        self._prepare(is_prod=False)
        host, port = self._prestart(host)
        if self.has_async:
            try:
                import uvicorn
            except ImportError:
                raise UsageError("Install uvicorn to use async views")

            uvicorn.run(
                f"{self.app_name}:{self.instance_name}._asgi_dev",
                host=host,
                port=port,
                log_level="info",
                reload=True,
                interface="asgi3",
            )
        else:
            exec_manage("runserver", f"{host}:{port}")

    def serve(self, host: str | None = None):
        """
        Run the production server.

        This method:

        * Runs migrations
        * Runs ``collectstatic``
        * Starts a production-ready server (gunicorn for WSGI, uvicorn for ASGI)
        * Sets ``DEBUG=False`` if not explicitly configured

        Args:
            host: Host and port in format ``"host:port"`` (default: ``"0:8000"``)

        Raises:
            UsageError: If gunicorn (for WSGI) or uvicorn (for ASGI) is not installed

        Example::

            if __name__ == "__main__":
                app.serve()
        """
        self._prepare(is_prod=True)
        host, port = self._prestart(host)

        if self.has_async:
            try:
                import uvicorn
            except ImportError:
                raise UsageError("Install uvicorn to use async views")

            port = 8000
            if ":" in host:
                host, port = host.split(":")
                port = int(port)

            uvicorn.run(
                f"{self.app_name}:{self.instance_name}",
                host=host,
                port=port,
                log_level="info",
                interface="asgi3",
            )
        else:
            try:
                from gunicorn.app.base import BaseApplication
            except ImportError:
                raise UsageError("Install gunicorn to serve WSGI")

            class LoadedApplication(BaseApplication):
                def __init__(self, app, host="127.0.0.1", port=8000):
                    self.app = app
                    self.host = host
                    self.port = port
                    super().__init__()

                def load_config(self):
                    self.cfg.set("bind", f"{self.host}:{self.port}")
                    self.cfg.set("workers", 4)

                def load(self):
                    return self.app

            wsgi = LoadedApplication(self, host=host, port=port)
            wsgi.run()

    def convert(self, path: Path, name: str, template: str | None = None):
        """
        Convert the single-file app to a full Django project structure.

        Args:
            path: Destination path for the new project (must not exist)
            name: Name for the Django project
            template: Optional project template to use

        Raises:
            UsageError: If the destination path already exists

        Example::

            from pathlib import Path

            app.convert(
                path=Path("/tmp/myproject"),
                name="myproject"
            )

        Note:
            This is typically called via the CLI:
            ``nanodjango convert app.py /path/to/project``
        """
        from .convert import Converter

        if path.exists():
            raise UsageError("Upgrade path is not empty - path cannot exist")
        path.mkdir()

        converter = Converter(app=self, path=path, name=name, template=template)
        converter.build()

    def _prestart(self, host: str | None = None) -> tuple[str, int]:
        """
        Common steps before start() and serve()

        Returns:
            (host: str, port: int)
        """
        # Be helpful and check sys.argv for the host in case the script is run directly
        if host is None:
            if len(sys.argv) > 2:
                raise UsageError("Usage: start [HOST]")
            elif len(sys.argv) == 2:
                host = sys.argv[1]
            else:
                host = "0:8000"

        port = 8000
        if ":" in host:
            host, _port = host.split(":")
            port = int(_port)
        elif not host:
            host = "0"

        # Only run migrations if contenttypes is installed (not in BARE mode)
        if "django.contrib.contenttypes" in self.settings.INSTALLED_APPS:
            # Check if this app has models
            has_models = any(
                isinstance(obj, type) and issubclass(obj, Model)
                for obj in self.app_module.__dict__.values()
                if getattr(obj, "__module__", None) == self.app_name
            )
            if has_models:
                exec_manage("makemigrations", self.app_name)
            exec_manage("migrate")

            # Only create superuser if auth is installed
            if "django.contrib.auth" in self.settings.INSTALLED_APPS:
                from django.contrib.auth import get_user_model

                User = get_user_model()
                if User.objects.count() == 0:
                    exec_manage("createsuperuser")

        return host, port

    def _pre_xsgi(self, is_prod=True):
        """
        Common steps to set up WSGI/ASGI
        """
        # WSGI/ASGI probably won't have had time to _prepare
        self._prepare()

        # Production settings
        if not is_prod:
            return

        if "DEBUG" not in self._settings:
            from django.conf import settings

            settings.DEBUG = False

    async def asgi(self, scope, receive, send, is_prod=True):
        """
        ASGI application.

        When async views are detected, this is available as the ``__call__`` method,
        making the Django instance directly usable as an ASGI application.

        Args:
            scope: ASGI scope dictionary
            receive: ASGI receive callable
            send: ASGI send callable
            is_prod: Whether to run in production mode (default: True)

        Returns:
            ASGI response

        Example with uvicorn::

            # In counter.py with async views:
            app = Django()

            @app.route("/")
            async def index(request):
                return "Hello async"

            # Command line:
            uvicorn counter:app
        """
        from django.core.asgi import get_asgi_application

        self._pre_xsgi(is_prod=is_prod)

        application = get_asgi_application()
        return await application(scope, receive, send)

    async def _asgi_dev(self, scope, receive, send):
        """
        ASGI application callable for development mode.

        This is used internally by ``run()`` when serving async applications.
        Sets ``is_prod=False`` to enable development features.
        """
        return await self.asgi(scope, receive, send, is_prod=False)

    def wsgi(self, environ, start_response):
        """
        WSGI application.

        When async views are not detected, this is available as the ``__call__`` method,
        making the Django instance directly usable as a WSGI application.

        Args:
            environ: WSGI environment dictionary
            start_response: WSGI start_response callable

        Returns:
            WSGI response iterable

        Example with gunicorn::

            # In counter.py:
            app = Django()

            # Command line:
            gunicorn counter:app
        """
        from django.core.wsgi import get_wsgi_application

        self._pre_xsgi()
        application = get_wsgi_application()
        return application(environ, start_response)

    async def create_server(
        self, host: str, port: int, log_level: str = "info", is_prod: bool = True
    ):
        """
        Initialise and run nanodjango as a task in an existing async loop.

        This will not call the prestart sequence, so will not call makemigrations,
        migrate or createsuperuser. Run these steps manually using
        ``nanodjango manage``.

        This is useful for running a Django server alongside other async code in a
        single process.

        Args:
            host: Host to bind to
            port: Port to bind to
            log_level: Uvicorn log level (default: "info")
            is_prod: Whether to run in production mode (default: True)
        """
        self._has_async_view = True
        type(self).__call__ = type(self).asgi  # Same hacky solution in wrapped()

        try:
            import uvicorn
        except ImportError:
            raise UsageError("Install uvicorn to use async server")

        # Prepare the app (but skip prestart migrations/superuser setup)
        self._prepare(is_prod=is_prod)

        config = uvicorn.Config(
            self, host=host, port=port, log_level=log_level, interface="asgi3"
        )
        server = uvicorn.Server(config)
        await server.serve()

    __call__ = wsgi
