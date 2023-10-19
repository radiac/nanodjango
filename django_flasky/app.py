import inspect
import os
import sys
from types import ModuleType

from django import setup
from django.urls import path as url_path

from . import app_meta
from .urls import urlpatterns
from .views import flask_view


class Django:
    """
    The main Django app
    """

    #: Name of the app script
    app_name: str
    #: Reference to the app script's module
    app_module: ModuleType

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)

        # Set app meta
        app_name = inspect.stack()[1].frame.f_globals["__name__"]
        app_meta._app_module = sys.modules[app_name]
        return instance

    def __init__(self, **settings):
        """
        Initialise a new Django app, optionally with settings to configure Django with

        Usage::

            app = Django()
            app = Django(SECRET_KEY="some-secret", ALLOWED_HOSTS=["lol.example.com"])
        """
        self.settings = settings
        self._config()

    def _config(self):
        """
        Configure and patch Django
        """

        # Settings
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_flasky.settings")
        from django.conf import settings

        for key, value in self.settings.items():
            setattr(settings, key, value)

        self.app_name = settings.DF_APP_NAME
        self.app_module = app_meta.get_app_module()

        # Import and apply glue after django.conf has its settings
        from .django_glue.apps import prepare_apps
        from .django_glue.db import patch_db

        patch_db(self.app_name)
        prepare_apps(self.app_name, self.app_module)

        # Ready for Django's standard setup
        setup()

    def route(self, pattern: str):
        """
        Decorator to add a view to the urls

        The pattern should use the Django path syntax - see
        https://docs.djangoproject.com/en/dev/ref/urls/#path

        Usage::

            @app.route("/")
            def view(request):
                return "Hello"

        All paths are relative to the root URL, leading slashes will be ignored
        """
        # Flask likes leading /, Django does not
        if pattern.startswith("/"):
            pattern = pattern[1:]

        def wrapped(fn):
            urlpatterns.append(url_path(pattern, flask_view(fn), name=fn.__name__))
            return fn

        return wrapped

    def run(self, args: list[str]):
        """
        Run a Django management command

        Defaults to:
            runserver 0:8000
        """
        from django.core.management import execute_from_command_line

        if not args:
            args = ["runserver", "0:8000"]
        args = ["django_flasky"] + list(args)
        execute_from_command_line(args)
