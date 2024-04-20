# App metadata
#
# These values are set by Django.__new__ and Django.__init__ before
# nanodjango.settings is imported, so we can configure settings based on these values
#
# Always access the values through their get_*() methods
from types import ModuleType
from typing import Any


#: Reference to app module
#:
#: Available after the app is imported, before app.run() is called
#:
#: Always access through get_app_module()
_app_module: ModuleType | None = None

#: App configuration
#:
#: Used to configure settings
_app_conf: dict[str, Any] = {}


def get_app_module() -> ModuleType:
    global _app_module
    if _app_module is None:
        raise ValueError("App module can only be accessed after it is imported")
    return _app_module


def get_app_conf() -> dict[str, Any]:
    return _app_conf
