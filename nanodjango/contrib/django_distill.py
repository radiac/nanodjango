from .. import Django, defer, hookimpl

with defer.optional:
    import django_distill


@hookimpl
def django_pre_setup(app: Django):
    if not defer.is_installed("django_distill"):
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
            import django_distill
        except ImportError as e:
            raise ImportError(
                "Could not find django-distill - try: pip install django-distill"
            ) from e

        path_fn = django_distilldistill_re_path if re else django_distill.distill_path

        if int(django_distill.__version__.split(".")[0]) >= 4:

            def path_fn(*args, _build_pattern=path_fn, **inner_kwargs):
                url_pattern = _build_pattern(*args, **inner_kwargs)
                django_distill.add_distilled_url(url_pattern)
                return url_pattern

        return path_fn

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
