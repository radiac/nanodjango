from types import ModuleType

from django.apps.config import AppConfig
from django.apps.registry import apps as apps_registry

from .. import settings


class NanodjangoAppConfig(AppConfig):
    """
    AppConfig with a hard-coded path
    """

    path = str(settings.DF_FILEPATH)


def prepare_apps(app_name: str, app_module: ModuleType):
    """
    Create and register the app config

    Do this while our script is importing, before apps.populate() is called.

    This tricks the apps registry into thinking our script module has already been
    loaded and doesn't try to import it again. Our models will get registered when the
    module finishes importing.
    """
    app_config = NanodjangoAppConfig(app_name=app_name, app_module=app_module)
    apps_registry.app_configs[app_config.label] = app_config
    app_config.apps = apps_registry
    app_config.models = {}
