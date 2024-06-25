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

    #: Name of the app script
    app_name: str

    #: Reference to the app script's module
    app_module: ModuleType

    #: Path of app script
    app_path: Path

    #: Whether this app has defined an @app.admin
    has_admin: bool = False

    #: Variable name for this current app
    _instance_name: str

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

    def _config(self, _settings):
        """
        Configure settings and patch Django ready for model definitions
        """
        self._settings = app_meta._app_conf = _settings

        # Settings
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nanodjango.settings")
        from django.conf import settings

        self.settings = settings

        for key, value in _settings.items():
            setattr(settings, key, value)

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
            @app.route("/(?P<slug>[a-z]/", re=True)
            def view(request, char):
                return f"Hello {char}"

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

    def _prepare(self, with_static=False):
        """
        Perform any final setup for this project after it has been imported:

        * detect if it has been run directly; if so, register it as an app
        * register the admin site

        If with_static is True, serve STATIC_URL and MEDIA_URL using
        django.conf.urls.static.static
        """

        # Check if this is being called from click commands or directly
        if self.app_name not in sys.modules:
            # Hasn't been run through the ``nanodjango`` command
            if (
                "__main__" not in sys.modules
                or getattr(sys.modules["__main__"], self._instance_name) != self
            ):
                # Doesn't look like it was run directly either
                raise UsageError("App module not initialised")

            # Run directly, so register app module so Django won't try to load it again
            sys.modules[self.app_name] = sys.modules["__main__"]

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

        # Register static and media
        if with_static:
            from django.conf.urls.static import static

            if self.settings.STATIC_ROOT and Path(self.settings.STATIC_ROOT).exists():
                urlpatterns.extend(
                    static(
                        self.settings.STATIC_URL,
                        document_root=self.settings.STATIC_ROOT,
                    )
                )
            if self.settings.MEDIA_ROOT and Path(self.settings.MEDIA_ROOT).exists():
                urlpatterns.extend(
                    static(
                        self.settings.MEDIA_URL, document_root=self.settings.MEDIA_ROOT
                    )
                )

    def run(self, args: list[str] | tuple[str] | None = None):
        """
        Run a Django management command, passing all arguments

        Defaults to:
            runserver 0:8000
        """
        # Be helpful and check sys.argv for args. This will almost certainly be because
        # it's running directly.
        if args is None:
            args = sys.argv[1:]

        self._prepare(with_static=True)
        if args:
            exec_manage(*args)
        else:
            exec_manage("runserver", "0:8000")

    def start(self, host: str | None = None):
        """
        Perform app setup commands and run the server
        """
        # Be helpful and check sys.argv for the host
        if host is None:
            print(sys.argv)
            if len(sys.argv) > 2:
                raise UsageError("Usage: start [HOST]")
            elif len(sys.argv) == 2:
                host = sys.argv[1]
        if not host:
            host = "0:8000"

        self._prepare(with_static=True)
        exec_manage("makemigrations", self.app_name)
        exec_manage("migrate")
        User = get_user_model()
        if User.objects.count() == 0:
            exec_manage("createsuperuser")
        exec_manage("runserver", host)

    def convert(self, path: Path, name: str):
        from .convert import Converter

        if path.exists():
            raise UsageError("Upgrade path is not empty - path cannot exist")
        path.mkdir()

        converter = Converter(app=self, path=path, name=name)
        converter.build()

    def __call__(self, *args, **kwargs):
        from django.core.wsgi import get_wsgi_application

        if "DEBUG" not in self._settings:
            from django.conf import settings

            settings.DEBUG = False

        application = get_wsgi_application()
        return application(*args, **kwargs)
