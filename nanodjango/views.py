import inspect

from django.http import HttpResponse


def string_view(fn):
    """
    Wrapper to automatically convert the response from a view function into an
    HttpResponse to support returning a string.
    """

    def make_response(response):
        if isinstance(response, HttpResponse):
            return response
        return HttpResponse(response)

    if inspect.iscoroutinefunction(fn):
        async def django_view(request, **kwargs):
            response = await fn(request)
            return make_response(response)
    else:
        def django_view(request, **kwargs):
            response = fn(request, **kwargs)
            return make_response(response)

    return django_view
