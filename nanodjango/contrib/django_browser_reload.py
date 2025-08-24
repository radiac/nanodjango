from django.urls import include

from .. import Django, defer, hookimpl

with defer.optional:
    import django_browser_reload


@hookimpl
def django_pre_setup(app: Django):
    """
    If django-browser-reload is installed add it to the project
    """
    if not defer.is_installed("django_browser_reload"):
        return

    from django.conf import settings

    app_name = "django_browser_reload"
    if app_name not in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS.append(app_name)

    middleware = "django_browser_reload.middleware.BrowserReloadMiddleware"
    if middleware not in settings.MIDDLEWARE:
        settings.MIDDLEWARE.append(middleware)

    app.path("__reload__/", include("django_browser_reload.urls"))


@hookimpl
def convert_build_app_urls(converter, resolver, urls, extra_src):
    """
    Add django-browser-reload during conversion
    """
    if not defer.is_installed("django_browser_reload"):
        return

    urls.append('path("__reload__/", include("django_browser_reload.urls")),')
    converter.imports["path"] = "from django.urls import path"
    converter.imports["include"] = "from django.urls import include"
    resolver.add_references({"path", "include"})
