from __future__ import annotations

import inspect
import os
import sys
from types import ModuleType
from typing import TYPE_CHECKING

from django import setup
from django.contrib import admin
from django.urls import path as url_path

from . import app_meta
from .exceptions import ConfigurationError
from .urls import urlpatterns
from .views import flask_view

if TYPE_CHECKING:
    from django.db.models import Model


class Django:
    """
    The main Django app
    """

    #: Name of the app script
    app_name: str

    #: Reference to the app script's module
    app_module: ModuleType

    _admin_site: admin.sites.AdminSite | None = None

    def __new__(cls, *args, **kwargs):
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
        self._config(_settings)

    def _config(self, _settings):
        """
        Configure settings and patch Django ready for model definitions
        """

        # Settings
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_flasky.settings")
        from django.conf import settings

        self.settings = settings

        for key, value in _settings.items():
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

    def _prepare(self):
        """
        Perform any final setup for this project after it has been imported:

        * register the admin site
        """
        admin_url = self.settings.ADMIN_URL
        if admin_url:
            if not isinstance(admin_url, str) or not admin_url.endswith("/"):
                raise ConfigurationError(
                    "settings.ADMIN_URL must be a string path ending in /"
                )
            urlpatterns.append(url_path(admin_url.removeprefix("/"), admin.site.urls))

    def route(self, pattern: str):
        """
        Decorator to add a view to the urls

        The pattern should use the Django path syntax - see
        https://docs.djangoproject.com/en/dev/ref/urls/#path

        Usage::

            @app.route("/")
            def view(request):
                return "Hello"

        All paths are relative to the root URL, leading slashes will be ignored.
        """
        # Flask likes leading / in its patterns, Django does not
        if pattern.startswith("/"):
            pattern = pattern[1:]

        def wrapped(fn):
            urlpatterns.append(
                url_path(pattern.removeprefix("/"), flask_view(fn), name=fn.__name__)
            )
            return fn

        return wrapped

    @property
    def has_admin(self):
        return isinstance(self.settings.ADMIN_URL, str)

    def admin(self, model: type[Model] | None = None, **options):
        """
        Decorator to add a model to the admin site

        The admin site must be added using ``settings.ADMIN_URL``.
        """
        if not self.has_admin:
            raise ConfigurationError(
                "Cannot register ModelAdmin - settings.ADMIN_URL is not set"
            )

        def wrap(model: type[Model]):
            admin.site.register(model, **options)
            return model

        if model is None:
            return wrap
        return wrap(model)

    def run(self, args: list[str]):
        """
        Run a Django management command

        Defaults to:
            runserver 0:8000
        """
        self._prepare()
        from django.core.management import execute_from_command_line

        if not args:
            args = ["runserver", "0:8000"]
        args = ["django_flasky"] + list(args)
        execute_from_command_line(args)
