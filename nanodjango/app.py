from __future__ import annotations

import ast
import inspect
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable

from django import setup
from django import urls as django_urls
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Model
from django.views import View

from . import app_meta
from .exceptions import ConfigurationError, UsageError
from .urls import urlpatterns
from .views import string_view

if TYPE_CHECKING:
    from pathlib import Path

    from ninja import NinjaAPI


def exec_manage(*args):
    from django.core.management import execute_from_command_line

    args = ["nanodjango"] + list(args)
    execute_from_command_line(args)


class Django:
    """
    The main Django app
    """

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

    #: Whether this app has any async views
    _has_async_view: bool = False

    # Settings cache to aid ``convert``
    _settings: dict[str, Any]

    # URL cache to aid ``convert``
    # {pattern:
    _routes: dict[str, tuple[Callable | None, dict[str, Any]]]

    # NinjaAPI instance for @app.api
    _api: NinjaAPI | None = None

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
        self.has_admin = False
        self._settings = {}
        self._routes = {}
        self._config(_settings)
        self._prepared = False

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
        self.app_name = settings.DF_APP_NAME
        self.app_module = app_meta.get_app_module()
        self.app_path = Path(inspect.getfile(self.app_module))

        # Import and apply glue after django.conf has its settings
        from .django_glue.apps import prepare_apps
        from .django_glue.db import patch_db

        patch_db(self.app_name)
        prepare_apps(self.app_name, self.app_module)

        # Ready for Django's standard setup
        setup()

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


    def route(self, pattern: str, *, re=False, include=None, name=None):
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

        All paths are relative to the root URL, leading slashes will be ignored.
        """
        # We want to support Flask-like patterns which have leading / in its patterns.
        # Django does not use these, so strip them out.
        pattern = pattern.removeprefix("/")

        # Find if it's a path() or re_path()
        path_fn = django_urls.re_path if re else django_urls.path

        if include is not None:
            # Being called directly with an include
            urlpatterns.append(path_fn(pattern, include))

            # If we're converting, we're going to need the source AST node
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
            # Store route for convert lookup
            self._routes[pattern] = (
                fn,
                {"re": re, "include": False, "name": name or fn.__name__.lower()},
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
            urlpatterns.append(
                path_fn(pattern, string_view(fn), name=name or fn.__name__.lower())
            )
            return fn

        return wrapped

    def admin(self, model: type[Model] | None = None, **options):
        """
        Decorator to add a model to the admin site

        The admin site must be added using ``settings.ADMIN_URL``.
        """
        self.has_admin = True

        def wrap(model: type[Model]):
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
        Ninja integration
        """
        if not self._api:
            api = self.ninja.NinjaAPI()
            self._api = api

        return self._api

    def _prepare(self, is_prod=False):
        """
        Perform any final setup for this project after it has been imported:

        * detect if it has been run directly; if so, register it as an app
        * register the admin site
        * if in production mode, collectstatic into STATIC_ROOT
        * if in development mode, extend urls to serve media files
        """
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
            if admin_url is None:
                admin_url = "admin/"
            if not isinstance(admin_url, str) or not admin_url.endswith("/"):
                raise ConfigurationError(
                    "settings.ADMIN_URL must be a string path ending in /"
                )
            urlpatterns.append(
                django_urls.path(admin_url.removeprefix("/"), admin.site.urls)
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
        Run a Django management command, passing all arguments
        """
        self._prepare(is_prod=False)
        exec_manage(*(args or []))

    def run(self, host: str | None = None):
        """
        Perform app setup commands and run the server in development mode
        """
        self._prepare(is_prod=False)
        host, port = self._prestart(host)
        if self.has_async:
            try:
                import uvicorn
            except ImportError:
                raise UsageError("Install uvicorn to use async views")

            uvicorn.run(
                f"{self.app_name}:{self.instance_name}.asgi_dev",
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
        Perform app setup and run the server in production mode
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

    def convert(self, path: Path, name: str):
        from .convert import Converter

        if path.exists():
            raise UsageError("Upgrade path is not empty - path cannot exist")
        path.mkdir()

        converter = Converter(app=self, path=path, name=name)
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

        exec_manage("makemigrations", self.app_name)
        exec_manage("migrate")
        User = get_user_model()
        if User.objects.count() == 0:
            exec_manage("createsuperuser")

        return host, port

    def _pre_xsgi(self, is_prod=True):
        """
        Common steps to set up WSGI/ASGI
        """
        # WSGI/ASGI probably won't have had time to _prepare
        if not self._prepared:
            self._prepare()

        # Production settings
        if not is_prod:
            return

        if "DEBUG" not in self._settings:
            from django.conf import settings

            settings.DEBUG = False

 
    async def asgi(self, scope, receive, send, is_prod=True):
        """
        ASGI handler

        Swapped into __call__ when an async view is found

        Alternatively run with uvicorn script:app.asgi
        """
        from django.core.asgi import get_asgi_application
        self._pre_xsgi(is_prod=is_prod)
        
        application = get_asgi_application()
        return await application(scope, receive, send)

    async def asgi_dev(self, scope, receive, send):
        """
        ASGI handler for development mode

        Used by uvicorn when called from ``run``
        """
        return await self.asgi(scope, receive, send, is_prod=False)

    def wsgi(self, environ, start_response):
        """
        WSGI handler
        """
        from django.core.wsgi import get_wsgi_application

        self._pre_xsgi()
        application = get_wsgi_application()
        return application(environ, start_response)

    __call__ = wsgi
