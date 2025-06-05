from .. import Django, hookimpl

try:
    import django_distill
except ImportError:
    installed = False
except Exception:
    # It tries to access settings, but this is before setup(), so it will error
    installed = True
else:
    installed = True


# TODO: wrap this. or finally find a way to defer settings


@hookimpl
def django_pre_setup(app: Django):
    if not installed:
        return

    from django.conf import settings

    if "django_distill" not in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS.append("django_distill")


@hookimpl
def django_route_path_fn(app, pattern: str, include, re: bool, kwargs: dict):
    distill = kwargs.pop("distill", False)
    distill_file = kwargs.pop("distill_file", None)
    distill_func = kwargs.pop("distill_func", None)

    # Check distill
    if distill_file or distill_func:
        distill = True

    if distill:
        try:
            from django_distill import distill_path, distill_re_path
        except ImportError as e:
            raise ImportError(
                "Could not find django-distill - try: pip install django-distill"
            ) from e
        return distill_re_path if re else distill_path

    # Not using distill, allow other plugins to handle
    return None


@hookimpl
def django_route_path_kwargs(
    app,
    pattern: str,
    include,
    re: bool,
    kwargs: dict,
):
    distill = kwargs.pop("distill", False)
    distill_file = kwargs.pop("distill_file", None)
    distill_func = kwargs.pop("distill_func", None)

    if distill or distill_file or distill_func:
        return {
            "distill_file": distill_file,
            "distill_func": distill_func,
        }
